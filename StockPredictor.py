import numpy as np
import pandas as pd
from datetime import datetime as dt
import datetime
import requests
import matplotlib.pyplot as plt
import glob
import itertools
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.statespace.sarimax import SARIMAX
from matplotlib.pylab import rcParams
from tqdm import tqdm_notebook as tqdm
plt.style.use("ggplot")

class StockPredictor:

    operatingSystem = ""
    coin = ""
    actualDate = ""
    
    def __init__(self, op, ad):
        self.operatingSystem = op
        self.actualDate = ad

    def getTrades(self, instrument_name, start_date, end_date, namePath):
        
        try:
            json_df = pd.DataFrame()
            json_data = [1]

            startepoch = int((dt.strptime(start_date,'%Y-%m-%d').timestamp()-14400)*1000)
            endepoch = int((dt.strptime(end_date,'%Y-%m-%d').timestamp()+72000)*1000)

            url = 'https://www.deribit.com/api/v2/public/get_last_trades_by_instrument_and_time?' \
                    'instrument_name={0}&end_timestamp={1}&count=1000&' \
                    'include_old=true&sorting=asc&start_timestamp={2}'.format(instrument_name,endepoch,startepoch)

            json_data = requests.get(url).json()
            json_df = pd.DataFrame(json_data['result']['trades'])
            df = json_df
            
            #move independent variable to last column, ensures column is in the data set too
            dependent_variable = ['price']
            df = df[[dv for dv in df if dv not in dependent_variable] 
                + [dv for dv in dependent_variable if dv in df]]
            
            #convert miliseconds* epoch to datetime (GMT timezone),
            #df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

            if 'liquidation' in df.columns:
                df = df.drop(['liquidation'])

            #df = df.drop(['index_price', 'instrument_name', 'mark_price', 'trade_id', 'trade_seq'], axis = 1)
            df.to_csv(namePath, index = None, header=True)
            return df
        except Exception as e:
            print(e)
    
    def plot_diff(self, df):

        
        # Differencing the price
        df_diff = df.diff(1).dropna()
        
        results = adfuller(df_diff.price)
        #print(f'P-Value= {results[1]}')
        # Plotting the differences daily
        df_diff.plot(figsize=(12,5))
        plt.title(f'Daily Price Changes for {self.coin}')
        plt.ylabel('Change')
        plt.xlabel('Date')
        plt.show()

    def best_param(self, model, data, pdq, pdqs):
        
        # 1) Loops through each possible combo for pdq and pdqs
        # 2) Runs the model for each combo
        # 3) Retrieves the model with lowest AIC score
        
        ans = []
        for comb in tqdm(pdq):
            for combs in tqdm(pdqs):
                try:
                    mod = model(data,
                                order=comb,
                                seasonal_order=combs,
                                enforce_stationarity=False,
                                enforce_invertibility=False,
                                freq='D')
    
                    output = mod.fit()
                    ans.append([comb, combs, output.aic])
                except:
                    continue
    
        ans_df = pd.DataFrame(ans, columns=['pdq', 'pdqs', 'aic'])
        return ans_df.loc[ans_df.aic.idxmin()]
    
    #This function returns the instrument name whether is Bitcoin or Ethereum
    def getInstName(self, coin):
        if coin == "Bitcoin":
            return 'btc'
        elif coin == "Ethereum":
            return 'eth'
    def setCoin(self, c):
        self.coin = self.getInstName(c)

    def predict(self, fromDate, toDate):

        df = pd.read_csv(f'close/{self.coin}_20_close.csv')        
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values(by='date')                         
        df.set_index(pd.DatetimeIndex(df['date']), inplace=True)         
        df = df[['price']]
        df['price'] = df['price'].astype(float)
        df = df.loc[fromDate:toDate]
        # pd.date_range(start = '2019-03-14', end = '2020-05-31' ).difference(df.index), check if missing dates
        
        self.plot_diff(df)
        
        # Converting the data to a logarithmic scale
        df_log = pd.DataFrame(np.log(df.price))
        
        # Differencing the log values
        log_diff = df_log.diff().dropna()
        
        results = adfuller(log_diff.price)
        print(f"P-value: {results[1]}")
        
        # Assigning variables for p, d, q.
        p = d = q = range(0,6)
        d = range(2)
        
        # Creating a list of all possible combinations of p, d, and q.
        pdq = list(itertools.product(p, d, q))
        
        # Keeping seasonality at zeroes
        pdqs = [(0,0,0,0)]
        
        # Finding the best parameters for SARIMAX function
        params = self.best_param(SARIMAX, df_log, pdq, pdqs)
        
        #split 33% train, 33%test, 33%validate
        index = round(len(df)*.33)
        
        train = df_log.iloc[:index]
        test = df_log.iloc[index:]
        
        #fit the model to the training set
        model = SARIMAX(train, 
                        order=params[0], 
                        seasonal_order=params[1], 
                        freq='D', 
                        enforce_stationarity=False, 
                        enforce_invertibility=False)
        output = model.fit()
        
        print(output.summary())
        output.plot_diagnostics(figsize=(15,8))
        plt.show()
     
        #test with test set
        fc   = output.get_forecast(len(test))
        conf = fc.conf_int()
        
        #transform values back to normal
        fc_series    = np.exp(pd.Series(fc.predicted_mean, index=test.index))
        lower_series = np.exp(pd.Series(conf.iloc[:, 0], index=test.index))
        upper_series = np.exp(pd.Series(conf.iloc[:, 1], index=test.index))
        
        etrain = np.exp(train)
        etest  = np.exp(test)
        
        #test values with train set, see how model would fit
        predictions = output.get_prediction(start=pd.to_datetime(fromDate), dynamic=False)
        pred        = np.exp(predictions.predicted_mean)
        
        #confidence interval for the training set
        conf_int   = np.exp(predictions.conf_int())
        low_conf   = np.exp(pd.Series(conf_int.iloc[:,0], index=train.index))
        upper_conf = np.exp(pd.Series(conf_int.iloc[:,1], index=train.index))
        
        rcParams['figure.figsize'] = 16, 8
        
        forecast = pred
        actual_val = etrain.price
 
        # Calculating root mean squared error
        rmse = np.sqrt(((forecast - actual_val) ** 2).mean())
        print(rmse)
        print("The ML model is off the mark by $", "{:.2f}".format(rmse))
        
        ################################
        #Predict Forecast Future Values
        ################################
        
        model = SARIMAX(df_log, 
                        order=(1, 0, 0), 
                        seasonal_order=(0,0,0,0), 
                        freq='D', 
                        enforce_stationarity=False, 
                        enforce_invertibility=False)
        output = model.fit()
        
        #get the forecast of future values
        future = output.get_forecast(steps=180)
        
        #transform values back
        pred_fut = np.exp(future.predicted_mean)
        
        #Confidence interval for our forecasted values
        pred_conf = future.conf_int()
        
        #transform value back
        pred_conf = np.exp(pred_conf)
        
        #################################################
        #Plot Forecast Future Values until November 2020
        #################################################
        
        #plot the prices up to the most recent
        ax = np.exp(df_log).plot(label='Actual', figsize=(16,8))
        
        #plot the forecast
        pred_fut.plot(ax=ax, label='Future Vals')
        
        #shading in the confidence interval
        ax.fill_between(pred_conf.index,
                        pred_conf.iloc[:, 0],
                        pred_conf.iloc[:, 1], color='k', alpha=.25)
        
        ax.set_xlabel('Date')
        ax.set_ylabel(f'{self.coin} Price')
        ax.set_xlim([fromDate, toDate])
        if self.coin == 'btc':
            ax.set_ylim([4000, 14000])
        else:
            ax.set_ylim([100, 350])
        
        plt.title('Forecasted values')
        plt.legend()
        plt.savefig('fc_val.png')
        plt.show()

    def display(self, path, fromD, toD):
        self.predict(fromD, toD)

#end of class
    

