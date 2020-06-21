
'''
---Asset Price Predictor---

This program grabs cryptocurrency information from Deribit webpage 
and stores it locally in a csv file using the user given dates and 
then using the same dates the user can display in screen using any 
spreadsheet opener.

https://www.devdungeon.com/content/python3-qt5-pyqt5-tutorial
https://www.tutorialspoint.com/pyqt/pyqt_using_qt_designer.htm
pip install -U scikit-learn


--Notes--



--Plans--
1) Implement QThreads or Threads to run the backgroud process apart from
   the main window.
2) 

--History--

Dec/15/2019:
	1) Fisrt program was made using coinbase webpage.
Feb/6/2020:
	1) The cryptocurrency data will be extracted using Deribit webpage.
Feb/15/2020:
	1) GUI was implemented using PyQt5
	2) Classes were implemented
	3) Started implementing System tray and Threads.
Mar/4/2020:
	1) Ui file was removed of usage and everything was implemented in
	   the system tray GUI.
	2) Clearing screen now accepts Windows or Linux.
Mar/5/2020:
	1) The program now runs the deribit-parsing file, generatig a csv
	   file in the current directory.
	2) It also opens the the file generated with the default spreedsheet
	   opener no matter if it's Windows or Linux.
Mar/6/2020:
	1) Organized the main script.
Mar/21/2020:
	1) Changed Display and Generate buttons color.
Mar/29/2020:
	1) Created a list to store all raw report files generated.
	2) Created RawFilesManager function to create another list
	   to store just the names and/or dates from the files.
Apr/1/2020:
	1) Changed the extension remover and RawFiles function to 
	   the class.
Apr/6/2020:
	1) Added an info window when a file is not present when opening.
	2) Separated Deribit file from the generate button. For the moment
	   Raw files are gathered automatically when opening the program by
	   calling it's own function called getReport().
	3) Documented the generateReport function to what to do next.
	4) Added the date to the name when storing the files from Deribit.
    5) Created a date variable so that it can be sent to setEverything funtion.
Apr/12/2020:
	1) A window icon was added(In Windows taskbar it still not working).
	2) The auto data collector at the start of the program was removed to implement
	   the Deribit resample calculator and let the user select the range of dates
	   to obtain the data.
	3) Combo boxes of the dates were replaced by dropdown menu with a calendar.
	   Also, dates were implemented using dropdown menus and sending it to the
	   deribit file.
	4) The display function was changed to open the file previously generated
	   when using the Display Report button which at the same time uses the dates
	   already selected by the user. It also prints to terminal the resample 
	   calculation of the same file.
	5) The size was fixed so that the user cannot resize the window, allowing 
	   the program to automatically appear in the center of the screen.
	6) The code was organized and documented.
	7) A version variable was created so that it can be changed in the top and 
	   not in the code.
May/4/2020:
	1) The user cannot use a from date greater than to date nor cannot use a to date
	   greater than the actual real date.
	2) The errors in GUI form were added when selecting the wrong dates.
	3) The info of successful creation of the report in generate function are only
	   shown if there is no problem with the coins or dates.
	4) The generate report function were documented.
	5) RawFilesManager and DataOrganizer functions were removed due to non usage.
	6) dateList list variable were removed due to non usage.
	7) Every function were documented.
May/18/2020:
	1) Dylan's Linear regression code was implemented with the GUI.
	2) The local function SVR was changed to LinearRegression due to problems with
	   library SVR that has the same function.
	3) The difference in the dates were implemented and sent to LinearRegression.
May/19/2020:
	1) verUpdate variable now updates each time a report is generated or the program opens.
May/20/2020:
	1) Fixed the inverse dates in Display function.
	2) Added GUI errors in inverse dates in Display function.
	3) The difference in the dates were fixed to compare the entire date, not just 
	   the days. Due to the different months and/or years.
	4) Fixed the logic in displayReport function by only using 1 try/except and handling
	   an exception if the selected file does not exists, which is generated in deribit
	   file and return as an error to be handled here. It now goes like this, with the
	   selected file the bootstrap is calculted, then the resample is done and it gets
	   displayed in screen + opened in the spreadsheet opener.
	5) Local variables boot and oob were created in bootstrap function so that it exists.
	   And if an error of FileNotFound raises it gets returned to the displayReport function.
Jun/9/2020:
	1) Display button was changed to Display report.
Jun/10/2020:
	1) Changed XGBoost name to StockPredictor.
	2) Changed StockPredictor to a class structure.
Jun/14/2020:
	1) fromDate is used to say from where to start the report and toDate to determine the limit 
	   of prediction. For the raw report fromDate is used to limit to the actual date and for 
	   prediction toDate is used as the limit for the prediction.
Jun/16/2020:
	1) The last version was compiled using Pyinstaller.
	2) Cleaned up the scripts.
	3) It was a pleasure you guys!!

'''

import time
import datetime
import sys
import os
import platform
import subprocess
import pandas as pd
from subprocess import Popen
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from bs4 import BeautifulSoup

import StockPredictor #as deribit

#---------------------Clears the screen at start------------------------
operatingSystem = platform.system()
if operatingSystem == "Linux":
	bashCmd = 'clear'
elif operatingSystem == "Windows":
	bashCmd = 'cls'
subprocess.call(bashCmd, shell=True)
#-----------------------------------------------------------------------

class mainWindow(QMainWindow):

	currentDate = datetime.datetime.now()
	actualDate = str(currentDate.year) + "-" + str(currentDate.month) + "-" + str(currentDate.day)
	verUpdate = ""
	df = ""
	displayData = 0

	deribit = 0

	def __init__(self):
		
		self.deribit = StockPredictor.StockPredictor(operatingSystem, self.actualDate)
		QMainWindow.__init__(self)
		self.trayIcon = QSystemTrayIcon(self)
		self.trayIcon.setIcon(QtGui.QIcon("res/CryptocurrencySysTray.png"))
		
		#-------------Combo boxes------------

		self.coinBox = QtWidgets.QComboBox(self)
		self.coinBox.setGeometry(QtCore.QRect(80, 100, 101, 22))
		self.coinBox.setObjectName("coinBox")
		self.coinBox.addItem("")
		self.coinBox.addItem("")
		self.coinBox.addItem("")

		self.styleBox = QtWidgets.QComboBox(self)
		self.styleBox.setGeometry(QtCore.QRect(270, 100, 101, 22))
		self.styleBox.setObjectName("styleBox")
		self.styleBox.addItem("")
		self.styleBox.addItem("")
		self.styleBox.addItem("")

		#-------------Dates selectors------------

		# from dropdown menu
		self.fromDate = QtWidgets.QDateEdit(self)
		self.fromDate.setGeometry(QtCore.QRect(80, 60, 101, 22))
		self.fromDate.setButtonSymbols(QtWidgets.QAbstractSpinBox.UpDownArrows)
		self.fromDate.setMaximumDateTime(QtCore.QDateTime(QtCore.QDate(3000, 12, 31), QtCore.QTime(23, 59, 59)))
		self.fromDate.setMinimumDate(QtCore.QDate(1900, 9, 14))
		self.fromDate.setCalendarPopup(True)
		self.fromDate.setTimeSpec(QtCore.Qt.LocalTime)
		self.fromDate.setDate(QtCore.QDate(2020, 1, 1))
		self.fromDate.setObjectName("fromDate")

		# to dropdown menu
		self.toDate = QtWidgets.QDateEdit(self)
		self.toDate.setGeometry(QtCore.QRect(270, 60, 101, 22))
		self.toDate.setButtonSymbols(QtWidgets.QAbstractSpinBox.UpDownArrows)
		self.toDate.setMaximumDateTime(QtCore.QDateTime(QtCore.QDate(3000, 12, 31), QtCore.QTime(23, 59, 59)))
		self.toDate.setMinimumDate(QtCore.QDate(1900, 9, 14))
		self.toDate.setCalendarPopup(True)
		self.toDate.setTimeSpec(QtCore.Qt.LocalTime)
		self.toDate.setDate(QtCore.QDate(2020, 1, 1))
		self.toDate.setObjectName("toDate")
		
		#-------------Buttons------------
		
		self.genReportBtn = QtWidgets.QPushButton(self)
		self.genReportBtn.setGeometry(QtCore.QRect(150, 150, 121, 23))
		self.genReportBtn.setAutoFillBackground(False)
		self.genReportBtn.setStyleSheet("background-color: cyan")
		self.genReportBtn.setObjectName("genReportBtn")
		self.dispReportBtn = QtWidgets.QPushButton(self)
		self.dispReportBtn.setGeometry(QtCore.QRect(150, 190, 121, 23))
		self.dispReportBtn.setStyleSheet("background-color: cyan")
		self.dispReportBtn.setObjectName("dispReportBtn")
		
		#-------------Buttons actions------------
		
		self.genReportBtn.clicked.connect(self.generateReport)
		self.dispReportBtn.clicked.connect(self.displayReport)
		
		#-------------fonts------------
		
		font = QtGui.QFont()
		font.setFamily("Times New Roman")
		font.setPointSize(16)
		font.setBold(True)
		font.setUnderline(True)
		font.setWeight(75)
		font.setStrikeOut(False)
		
		#-------------Labels-------------
		
		self.nameLbl = QtWidgets.QLabel(self)
		self.nameLbl.setGeometry(QtCore.QRect(100, 0, 201, 41))
		self.nameLbl.setFont(font)
		self.nameLbl.setObjectName("nameLbl")
		self.fromLbl = QtWidgets.QLabel(self)
		self.fromLbl.setGeometry(QtCore.QRect(30, 60, 41, 20))
		self.fromLbl.setObjectName("fromLbl")
		self.toLbl = QtWidgets.QLabel(self)
		self.toLbl.setGeometry(QtCore.QRect(230, 60, 31, 20))
		self.toLbl.setObjectName("toLbl")
		self.dateLbl = QtWidgets.QLabel(self)
		self.dateLbl.setGeometry(QtCore.QRect(120, 230, 300, 20))
		self.dateLbl.setObjectName("dateLbl")
		self.CoinLbl = QtWidgets.QLabel(self)
		self.CoinLbl.setGeometry(QtCore.QRect(30, 100, 41, 20))
		self.CoinLbl.setObjectName("CoinLbl")
		self.styleLbl = QtWidgets.QLabel(self)
		self.styleLbl.setGeometry(QtCore.QRect(220, 100, 41, 20))
		self.styleLbl.setObjectName("styleLbl")
		self.statusbar = QtWidgets.QStatusBar(self)
		self.statusbar.setObjectName("statusbar")
		self.actionAbout = QtWidgets.QAction(self)
		self.actionAbout.setObjectName("actionAbout")
		
		#-------------Tray options------------
		
		showAction = QAction("Show App", self)
		showAction.triggered.connect(self.openApp)
		exit_action = QAction("Exit",self)
		exit_action.triggered.connect(self.exit_app)
		trayMenu = QMenu()
		trayMenu.addAction(showAction)
		trayMenu.addAction(exit_action)
		self.trayIcon.setContextMenu(trayMenu)  # Set right-click menu
		self.trayIcon.show()
		
		self.setEverything(self)
		QtCore.QMetaObject.connectSlotsByName(self)
		
		
	def setEverything(self, mainWindow):
		_translate = QtCore.QCoreApplication.translate
		self.setWindowTitle(_translate("mainWindow", "Asset Price Predictor"))
		
		#-------------Labels-------------
		
		self.nameLbl.setText(_translate("mainWindow", "Asset Prices Predictor"))
		self.toLbl.setText(_translate("mainWindow", "To:"))
		self.fromLbl.setText(_translate("mainWindow", "From:"))
		self.dateLbl.setText(_translate("mainWindow", self.lastReportRead()))
		self.CoinLbl.setText(_translate("mainWindow", "Coin:"))
		self.styleLbl.setText(_translate("mainWindow", "Style:"))
		
		#-------------Combo boxes-------------

		self.coinBox.setItemText(0, _translate("mainWindow", "-Select-"))
		self.coinBox.setItemText(1, _translate("mainWindow", "Bitcoin"))
		self.coinBox.setItemText(2, _translate("mainWindow", "Ethereum"))
		self.styleBox.setItemText(0, _translate("mainWindow", "-Select-"))
		self.styleBox.setItemText(1, _translate("mainWindow", "Report"))
		self.styleBox.setItemText(2, _translate("mainWindow", "Graph"))

		#-------------Dates selectors------------

		self.fromDate.setDisplayFormat(_translate("mainWindow", "yyyy-M-d"))
		self.toDate.setDisplayFormat(_translate("mainWindow", "yyyy-M-d"))
		
		#-------------Buttons-------------
		
		self.genReportBtn.setText(_translate("mainWindow", "Generate Report"))
		self.dispReportBtn.setText(_translate("mainWindow", "Display Report"))
		
		
		self.actionAbout.setText(_translate("mainWindow", "About"))
	
	#This function returns the instrument name whether is Bitcoin or Ethereum
	def getInstName(self, coin):
		if coin == "Bitcoin":
			return 'BTC-PERPETUAL'
		elif coin == "Ethereum":
			return 'ETH-PERPETUAL'
		else:
			QMessageBox.information(self, "Error", "You must select a currency!")

	#This function downloads a report with the user selected dates from Deribit page
	#and stores them in a folder called RawReports.
	def generateReport(self):
		#-----This try grabs any error that is produced by inputting a wrong data-----
		try:

			#These if statements verifies that the dates selected by the user are correct
			#Case 1: fromDate is bigger than toDate.
			check = 0
			if str(self.fromDate.text()) > str(self.toDate.text()):
				check = 1
				raise Exception
			
			path = "RawReports/" + str(self.coinBox.currentText()) + "_" + str(self.fromDate.text()) +"_"+ str(self.toDate.text()) + ".csv"
			#Calls the info extractor functions
			self.df = self.deribit.getTrades(str(self.getInstName(str(self.coinBox.currentText()))), str(self.fromDate.text()), str(self.toDate.text()), path)
			QMessageBox.information(self, "Info", "File created succesfully!")
			self.verUpdate = "Last report generated: " + self.actualDate
			self.lastReportWrite(self.verUpdate)
			self.dateLbl.setText(self.verUpdate)
		except KeyError:
			QMessageBox.information(self, "Error", "Verify that the correct instrument name is selected!")
		except FileNotFoundError: #If the folder doesn't exists it creates one
			os.mkdir("RawReports")
			self.deribit.getTrades(str(self.getInstName(str(self.coinBox.currentText()))), str(self.fromDate.text()), str(self.toDate.text()), path)
			QMessageBox.information(self, "Info", "File created succesfully!")
		except Exception: #depending on the number of the check variable, the message changes.
			if check == 1:
				QMessageBox.information(self, "Date error", "The dates entered are invalid!"+
				"\nPlease enter a from date lower than to date.")
			elif check == 2:
				QMessageBox.information(self, "Date error", "To date entered is invalid!"+
				"\nPlease enter a date no bigger than today.")
	
	#This function looks for the file in RawReports with the coin name and dates selected by the user.
	#In the case that it doesn't exists it displays an error.
	#If it exists, it takes the name in (coin_fromDate_toDate.csv) format and path to the
	#deribit file to calculate the data and finally it opens the generated graphs or report depending
	#on the selection of the style by the user.
	def displayReport(self):
		
		coin = str(self.coinBox.currentText())
		fromD = str(self.fromDate.text())
		toD = str(self.toDate.text())
		
		cwd = os.getcwd()+"/RawReports/"
		path = coin + "_" + fromD +"_"+ toD + ".csv" #Establishes the name to look for.
		
		if not os.path.exists(cwd + path):
			self.df = self.deribit.getTrades(str(self.getInstName(str(self.coinBox.currentText()))), str(self.fromDate.text()), str(self.actualDate), cwd+path)
		
		self.deribit.setCoin(coin)
		
		try:
			
			if str(self.styleBox.currentText()) == "Report":
				if operatingSystem == "Linux":
					if coin == 'Bitcoin':
						subprocess.call(["xdg-open", cwd + path])
					elif coin == 'Ethereum':
						subprocess.call(["xdg-open", cwd + path])
				elif operatingSystem == "Windows":
					if coin == 'Bitcoin':
						os.startfile(cwd + path)
					elif coin == 'Ethereum':
						os.startfile(cwd + path)
			elif str(self.styleBox.currentText()) == "Graph":
				try:
					self.deribit.display(cwd + path, fromD, toD)
				except AttributeError as ae:
					print(ae)
					QMessageBox.warning(self, "No report error", "You must generate a report first!")
			
		except FileNotFoundError:
			QMessageBox.warning(self, "File error", "The file for the date entered does not exists!"+
				"\nPlease enter a date with an existing file"
				"\nor check that the date is correctly selected.")
		

	#This function writes to a file the last day which a raw report were created.
	def lastReportWrite(self, dateUpdate):
		log = open("LastGenReportDate.txt", "w")
		log.write(dateUpdate)
		log.close()
	
	#This function opens the LastGenReportDate file and displays it in the program when it opens.
	def lastReportRead(self):
		try:
			log = open("LastGenReportDate.txt", "r")
			content = log.readline()	
			log.close()
		except FileNotFoundError:
			content = "There is no report yet!"
			log = open("LastGenReportDate.txt", "w")
			log.close()

		return content

	#This function generates a desktop notification when the program is closed using the X.
	def notify(self, message):
		self.trayIcon.showMessage("Application minized!", message, QSystemTrayIcon.Information, 3000)
	
	#This function reopens the program if it were closed using to the system tray.
	def openApp(self):
		self.show()
	
	def exit_app(self):
		self.trayIcon.hide()  # Do this or icon will linger until you hover after exit
		qApp.quit()
	
	# With closeEvent, we can ignore the event and instead hide the window, producing 
	# a "close-to-system-tray" action. To exit, the right-click->Exit option from the system
	# tray must be used.
	def closeEvent(self, event):
		event.ignore()
		self.hide()
		self.notify("App minimized to system tray.")

#This function sets up the main window before starting it.
def loadWindow():
		
		app = QApplication(sys.argv)
		window = mainWindow()
		window.setObjectName("mainWindow")
		window.setEnabled(True)
		window.setFixedSize(400,300)
		window.setWindowIcon(QtGui.QIcon("res/CryptocurrencySysTray.png"))
		
		window.show()
		
		sys.exit(app.exec_())

if __name__ == '__main__':
	
	loadWindow()
	
#--------------------------------Notes or old stuff------------------------------------------
