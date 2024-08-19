'''

Sample code made for Matthew Benti to showcase PyQt6.

Runs a simple user interface to illustrate how a UI can be built and how functions can be called.

Initial Code:       Darren Homeniuk, P.Eng.
Initial Date:       May 9, 2024
*****************************************************************************************************************
Version:            1.0 - May 9, 2024
By:                 Darren Homeniuk, P.Eng.
Notes:              Set up the initial code.
*****************************************************************************************************************
'''

import sys
from PyQt6.QtCore import Qt
import numpy as np
import pyqtgraph as pg
from subprocess import call 
from streamTest_T7 import DAQ
import time
from threading import Thread, Timer
from datetime import datetime, date
import os
import csv
from pandas import DataFrame




#import the necessary aspects of PyQt6 for this user interface window
from PyQt6.QtWidgets import QWidget, QPushButton, QApplication, QLabel, QMessageBox, QGridLayout, QComboBox, QLineEdit, QGroupBox, QVBoxLayout, QHBoxLayout, QSpacerItem, QSizePolicy, QRadioButton, QCheckBox, QSlider, QSpinBox, QFileDialog, QTabWidget
from PyQt6.QtCore import *
from PyQt6.QtGui import *


#this class handles the main window interactions, mainly initialization

class MainWindow(QWidget):
    

    # variable "e" is the condition that determines whether the test will run of not, if it is false, the test will not run
    # this is set to "True" when start is clicked
    e = False
    
    closing = False             #tells if the UI is closing or not
    line1 = None
    line2 = None

    #iniitalized dictionaries used to store lines; called later in the numLines function
    linesT = {}
    linesP = {}
    linesM = {}
 
    #####################################
    # INITIALIZATIONS FOR INPUTS
    #####################################
    """
    This is where the list initializations are made, the first lists of "AIN_" are a list of analog inputs connected to a type of sensor.
    for example "AINT" is a list of analog input connected to the temperature sensor, where "T" stands for temperature.

    based on the number of elements within the AIN lists, a empty list will be appened to the dictionaries below, where each empty list corresponds to a 
    individual sensor, and all data from that sensor is recorded in that list. 
    
    For example: lets say 'AIN0' is connected to a MagCheck, after writing down AIN0 as a element of the list "AINM" a empty list will be appened to 
    the dictionaries DataM, fileListM, lisM, and fieldnameM (functions of each list is explained further in this code and the "streamTest_T7 code"). 
    This gives us a storage place for each sensors data, and combines sensors of the same type in a bundle or "dataframe".

    these are then passed into the functions from streamTest later on in the code in the updatePlot functions
    """
    AINT = ['AIN0','AIN4']
    AINP = ['AIN3']
    AINM = ['AIN2']


# initializes each 2-D list
    DataM = {}
    filelistM = {}
    listM = {}

    
        
    # appends a new list to the 2D list for every sensor used in the magnetic field testing
    for sensor in AINM:
        DataM.update({sensor:[]})
        filelistM.update({sensor:[]})
        listM.update({sensor:[]})


    # initializes each 2-D list
    # RECREATE ALL LISTS INTO ONE "NUMSENSOR" LIST AND THEN USE .COPY INSIDE 
    DataT = {}
    filelistT = {}
    fileBufferListT = {}
    derAvg = {}
    derBufferList = {}
    spikeDataT = {}


    #resistence values of wire corresponding connected to its respected input
    ResValues = {AINT[0]:1.080, AINT[1]:1.099}
        
    # appends a new list to the 2D list for every sensor used in the temperature testing
    for sensor in AINT:
        DataT.update({sensor:[]})
        filelistT.update({sensor:[]})
        fileBufferListT.update({sensor:[]})
        derBufferList.update({sensor:[]})
        derAvg.update({sensor:[]})
        spikeDataT.update({sensor:[]})


    # initializes each 2-D list
    DataP = {}
    filelistP = {}
    listP = {}
    spikeDataP = {}


    # appends a new list to the 2D list for every sensor used in the pressure testing
    for sensor in AINP:
        DataP.update({sensor:[]})
        filelistP.update({sensor:[]})
        listP.update({sensor:[]})
        spikeDataP.update({sensor:[]})
  
    
    #function to handle initialization - mainly calls a subfunction to create the user interface
    def __init__(self):
        super().__init__()
        self.initUI()
        

    #function to create the user interface, and load in external modules for equipment control
    def initUI(self):
        
        #define a font for the title of the UI
        titleFont = QFont()
        titleFont.setBold(True)
        titleFont.setPointSize(12)
        
        #define a font for the buttons of the UI
        buttonFont = QFont()
        buttonFont.setBold(False)
        buttonFont.setPointSize(10)
        
        boldButtonFont = QFont()
        boldButtonFont.setBold(True)
        boldButtonFont.setPointSize(12)
        
        #set width of main window (X, Y , WIDTH, HEIGHT)
        windowWidth = 1200
        windowHeight = 800
        self.setGeometry(50, 50, windowWidth, windowHeight)
        # self.setStyleSheet("background-color: darkgray;")
        self.setMinimumSize(windowWidth, windowHeight)
        
        #number of columns on main inputs
        col = 12
        
        #name the window
        self.setWindowTitle('TEM Monitor')
        
        #determine the grid pattern
        mainGrid = QGridLayout()
        mainGrid.setSpacing(10)
        mainGrid.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        #current row tracker to avoid a lot of rework when things move around
        r = 0
        
        #create a label at the top of the window so we know what the software does
        topTextLabel = QLabel('SEM Temperature & Pressure', self)
        topTextLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        topTextLabel.setWordWrap(True)
        topTextLabel.setFont(titleFont)
        mainGrid.addWidget(topTextLabel, r, 0, 1, col)
        r += 1
        
        self.connectText = QLabel('Device Connected8oi', self)
        self.connectText.setFont(boldButtonFont)
        self.connectText.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mainGrid.addWidget(self.connectText, r, 0, 1, 3)
        r += 1
        
        #-------------------------------------------------------------
        # Operation Mode Radio group
        #-------------------------------------------------------------
        
        #mainGrid.addWidget(deviceName, row, col, rowSpan, colSpan)
        
        self.radioGroup = QGroupBox("Mode Selection")
        self.radioGroup.setFont(titleFont)
        self.radioGroup.setCheckable(False)
        self.radioGroup.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mainGrid.addWidget(self.radioGroup, r, 0, 4, 3)
        r += 4
        
        self.vbox = QVBoxLayout()
        self.radioGroup.setLayout(self.vbox)
        
        self.radio1 = QRadioButton('Magnetic Field vs. Time')
        self.radio1.setFont(buttonFont)
        self.radio1.setToolTip("Click to monitor the Magnetic field of environment")
        self.radio1.clicked.connect(lambda: self.uiModeChanged(1))
        self.vbox.addWidget(self.radio1)

        self.radio1.setChecked(True)
        
        self.radio2 = QRadioButton('Temperature vs. Time')
        self.radio2.setFont(buttonFont)
        self.radio2.setToolTip("Click to monitor temperature of environment")
        self.radio2.clicked.connect(lambda: self.uiModeChanged(2))
        self.vbox.addWidget(self.radio2)

        self.radio3 = QRadioButton('Pressure vs. Time')
        self.radio3.setFont(buttonFont)
        self.radio3.setToolTip("Click to monitor Pressure of environment")
        self.radio3.clicked.connect(lambda: self.uiModeChanged(3))
        self.vbox.addWidget(self.radio3)

        
        self.radio1.setChecked(True)

        self.spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        mainGrid.addItem(self.spacer, r, 0, 1, 3)
        r += 1
        
        #-------------------------------------------------------------
        # COMBOBOX SETTINGS
        #-------------------------------------------------------------
        
        #A COMBOBOX DEMO
        label1 = QLabel('Timeframes: ')
        label1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label1.setToolTip("You can add newline characters by adding the character  \nThis is after the line break.")
        label1.setFont(titleFont)
        mainGrid.addWidget(label1, r, 0, 1, 3)
        r += 1
        
        self.comboBox1 = QComboBox()
        self.comboBox1.addItem('default')
        self.comboBox1.addItem('90 seconds')
        self.comboBox1.addItem('5 minutes')
        self.comboBox1.addItem('10 minutes')
        self.comboBox1.setToolTip("these are the timeframes on which you can view\n all the data")
        self.comboBox1.setFont(buttonFont)
        self.comboBox1.currentIndexChanged.connect(self.uiCombobox1Changed)
        mainGrid.addWidget(self.comboBox1, r, 0, 1, 3)
        r += 1
        
        mainGrid.addItem(self.spacer, r, 0, 1, 3)
        r += 1
        
        ##########################
        # SPINBOX SETTINGS
        ##########################
        spinLabel = QLabel('Frequency(1/s):')
        spinLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        spinLabel.setFont(titleFont)
        mainGrid.addWidget(spinLabel, r, 0, 1, 2)

        self.spinbox1 = QSpinBox()
        self.spinbox1.setRange(1,10000000)
        self.spinbox1.setSingleStep(1)
        self.spinbox1.setValue(1)
        self.spinbox1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spinbox1.setFont(buttonFont)
        self.spinbox1.setToolTip("This box sets the frequency of data acquisition")
        self.spinbox1.editingFinished.connect(self.uispinbox1Changed)
        mainGrid.addWidget(self.spinbox1, r, 2, 1, 1)
        r += 1
        
        mainGrid.addItem(self.spacer, r, 0, 1, 3)
        r += 1
        
        ##############################################################
        # START RUN AND STOP RUN INTIALIZATIONS
        ##############################################################

        self.startRunButton = QPushButton('Start Test')
        self.startRunButton.setFont(boldButtonFont)
        self.startRunButton.clicked.connect(self.startRun)

        self.stopRunButton = QPushButton('Stop Test')
        self.stopRunButton.setFont(boldButtonFont)
        self.stopRunButton.clicked.connect(self.stopRun)

        
        mainGrid.addWidget(self.startRunButton, r, 0, 1, 3)
        r += 2
        mainGrid.addWidget(self.stopRunButton, r, 0, 1, 3)


        ##############################################################
        # GRAPH INITIALIZATOINS
        ##############################################################

        self.lineProfile1 = pg.plot()
        self.lineProfile1.showGrid(x = True, y = True, alpha=0.5)
        self.lineProfile1.setTitle("Magnetic field vs. Time")
        self.lineProfile1.setLabel('left', 'Magnetic Field', units = 'Gauss')
        self.lineProfile1.setLabel('bottom', 'Time', units = 'seconds')
        self.lineProfile1.setXRange(0, 120, padding=0.01)
        self.lineProfile1.setYRange(0, 50, padding=0.01)
        self.lineProfile1.setLimits(xMin=0, minXRange=0,yMin=-1000,minYRange=0,yMax=119,maxYRange=119)
        self.lineProfile1.setBackground('w')
        
        

        #define the ranges for the plot
        self.plotX = np.array(range(0,120))
        self.plotLeft = np.zeros_like(range(0,120))
        self.plotRight = np.zeros_like(range(0,120))
        
        #define the lines themselves
        
        # self.line1 = self.lineProfile1.plot(self.plotX, self.plotRight, pen=pg.mkPen('r', width=1), name='Right-click')
        # self.line2 = self.lineProfile1.plot(self.plotX, self.plotRight, pen=pg.mkPen('b', width=1), name='Left-click')


        mainGrid.addWidget(self.lineProfile1, 2, 11, r-1, 1)
        #mainGrid.addWidget(self.lineProfile2, 1+int(r/2), 11, int(r/2), 1)

        #set the layout into the widget
        self.setLayout(mainGrid)
                
        #show the main user interface
        # self.show()  
        self.showMaximized()

    def numLines(self):
        """
        This function determines how many lines are going to appear on each graph accourding to the AIN values set in the start function.

        it sets each used AIN to a line in a dictionary corresponding to which type of sensor your using. so for all inputs in AINT (analog input for temp),
        assign the same amount of lines to the input and stores it in a dictionary which is called later to graph
        """

        colors = ['r', 'b', 'g' , 'y']

        for i in range(len(self.AINM)):
            self.linesM["line %s" %self.AINM[i]] = self.lineProfile1.plot(self.plotX, self.plotRight, pen=pg.mkPen(colors[i], width=1), name=self.AINM[i])

        for i in range(len(self.AINT)):
            self.linesT["line %s" %self.AINT[i]] = self.lineProfile1.plot(self.plotX, self.plotRight, pen=pg.mkPen(colors[i], width=1), name=self.AINT[i])
        
        for i in range(len(self.AINP)):
            self.linesP["line %s" %self.AINP[i]] = self.lineProfile1.plot(self.plotX, self.plotRight, pen=pg.mkPen(colors[i], width=1), name=self.AINP[i])


        


    def startRun(self):
        """
        Starts the test. This function initializes the analog inputs used into three groups according to which sensor they are using.

        each function loops depending on the value of a parameter "e", if its true, it will keep looping, if not, then the function will stop. the value of e is intialized to false,
        but the startRun function sets it equal to true, starting the loop

        """

        if self.e == True:
            print('Test has already begun!')
            return
        

        self.numLines()

        self.test = DAQ()
        self.e = True

        
        # starts the magnetic data graphing function that repeats periodically
        self.MagTimer = Timer(0.95,self.updatePlot1)
        self.MagTimer.start()


        # starts the temp data graphing function that repeats periodically
        self.TempTimer = Timer(0.95,self.updatePlot2)
        self.TempTimer.start()
        self.now = datetime.now()

       # starts the pressure data graphing function that repeats periodically
        self.PressTimer = Timer((1/3),self.updatePlot3)
        self.PressTimer.start()

        print('Stream has started')
        x = 0

    def stopRun(self):
        """
        This function stops the graphing and logging data function by setting the parameter "e" equal to false, meaning the timers
        will no longer reset at the end of each funciton. it also resets the stored Data in each sensor in case the user presses start again.
        """
        if self.e ==True:
            self.e = False
            self.test.stopRun()

            self.MagTimer.cancel()
            for sensor in self.AINM:
                self.linesM['line %s' %sensor].clear()
                self.DataM[sensor].clear()
                #self.filelistM[sensor].clear()
            

            self.TempTimer.cancel()
            for sensor in self.AINT:
                self.linesT['line %s' %sensor].clear()
                self.DataT[sensor].clear()
                #self.filelistT[sensor].clear()

            self.PressTimer.cancel()
            for sensor in self.AINP:
                self.linesP['line %s' %sensor].clear()
                self.DataP[sensor].clear()
                #self.filelistP[sensor].clear()




        print('Stream has stopped')


    """
    Each update plot function is almost identical in how it is run, on intervals given in the startrun function, it will grab data from its respective
    function from the DAQ module, assigning it to 2D-Lists that account for each sensor and data in each sensor.

    Then using the line-dictionary created by the numLines function, we assign each sensors data to a line of a specific color and name whihc then get plotted to the graph. However
    if the correct radio button isnt pressed then the lines will not appear on the graph.

    we then use the fileWriter function to write the data from the file list to a file. the fileList is also 2 dimentional, so we can properly seperate each sensors data and plot it.

    Lastly, the function is set to loop if the parameter "e" is set to true.
    """


    def updatePlot1(self):
        # the time now is used display the time on the file list
        now = datetime.now()

        """
        DataM - the collection of magnetic field data taken each second from each sensor (2D)
        xData - the collection of time when each piece of data was taken in seconds (1D)
        filelistx - the collection of time when each piece of data was taken in minutes (1D)
        filelistM - the colleciton of a average of Data over that minute appended to a list (2D)
        """
        xData, self.DataM, fileListx, self.filelistM = self.test.MData(

        self.AINM,
        self.DataM,
        self.filelistM,
        self.listM,
    )

        self.filelistM.update({'Time':fileListx})

        # this is the part that actually graphs the line using xData and DataM
        if self.radio1.isChecked() == True:
            #makes sure relevant data is visible
            if len(xData)>=1:
                self.imageUpdate1(xData)

            # sets data to their lines
            for sensor in self.AINM:
                self.lineProfile1.addLegend()
                self.linesM['line %s' %sensor].setData(xData,self.DataM[sensor])
                

        else:
            for sensor in self.AINM:
                self.linesM['line %s' %sensor].clear()
                
        # writes data to file
        self.fileWriter(
            self.filelistM,
            'Mag',
            now
        )
 
        #restarts the function if "e" is true
        if self.e == True:
            self.MagTimer = Timer(0.95,self.updatePlot1)
            self.MagTimer.start()


    def updatePlot2(self):
        # the time now is used display the time on the file list
        
        now = datetime.now()

        """
        DataT - the collection of temperature data taken each second from each sensor (2D)
        xData - the collection of time when each piece of data was taken in seconds (1D)
        filelistx - the collection of time when each piece of data was taken in minutes (1D)
        filelistM - the colleciton of a average of Data over that minute appended to a list (2D)
        """
        
        xData, self.DataT, fileListx, self.filelistT = self.test.TData(

        self.AINT,
        self.DataT,
        self.ResValues,
        self.spikeDataT,
        self.derAvg,
        self.filelistT,
        self.fileBufferListT,
        )

        self.filelistT.update({'Time':fileListx})
       
        ############################    
        # MAPPING TO PLOT
        ############################


        # this is the part that actually graphs the line using xData and DataT
        if self.radio2.isChecked() == True:
            #makes sure relevant data is visible
            if len(xData)>=1:
                self.imageUpdate1(xData)

            # sets data to their lines
            for sensor in self.AINT:
                self.lineProfile1.addLegend()
                self.linesT['line %s' %sensor].setData(xData,self.DataT[sensor])

        else:
            for sensor in self.AINT:
                self.linesT['line %s' %sensor].clear()
                
        # writes data to file
        self.fileWriter(
            self.filelistT,
            'Temp',
            now
        )

        #restarts the function if "e" is true
        if self.e == True:
            self.TempTimer = Timer(0.95,self.updatePlot2)
            self.TempTimer.start()


        


    def updatePlot3(self): 
        # the time now is used display the time on the file list
        now = datetime.now()

        """
        DataP - the collection of Pressure data taken each second from each sensor (2D)
        xData - the collection of time when each piece of data was taken in seconds (1D)
        filelistx - the collection of time when each piece of data was taken in minutes (1D)
        filelistM - the colleciton of a average of Data over that minute appended to a list (2D)
        """

        xData, self.DataP, fileListx, self.filelistP = self.test.PData(

        self.AINP,
        self.DataP,
        self.filelistP,
        self.listP,
        self.spikeDataP
        )

        self.filelistP.update({'Time':fileListx})
        
        #print(len(xData),len(self.DataP[0]))
        
        # this is the part that actually graphs the line using xData and DataP
        if self.radio3.isChecked() == True:
            #makes sure relevant data is visible
            if len(xData)>=1:
                self.imageUpdate1(xData)

            # sets data to their lines
            for sensor in self.AINP:
                self.lineProfile1.addLegend()
                self.linesP['line %s' %sensor].setData(xData,self.DataP[sensor])
                
        else:
            for sensor in self.AINP:
                self.linesP['line %s' %sensor].clear()
                
        # writes data to file
        self.fileWriter(
            self.filelistP,
            'Pressure',
            now
        )

        #restarts the function if "e" is true
        if self.e == True:
            self.PressTimer = Timer((1/3),self.updatePlot3)
            self.PressTimer.start()


    def fileWriter(self,fileList: dict, type: str, now: time):
        """
        This function writes the values of the file lists to a csv file accordong to which sensor.
        
        first it sets the value of row to be a dictionary splitting up the values within the fileListY,
        so each sensors data of fileListY can be with its respective "name". it then creates a folder 
        based on what day it is and a file based on the hour.

        it then writes a csv file where the data of each sensor is listed in columns
        
        """            
        
        # creates a dictionary that has each row of data of the test; this will be looped over
        row = fileList.copy()

        # Sets the dictionary "row" as a pandas dataframe to easily log data to files
        df = DataFrame(row)

        #Sets the path
        mypath = 'C:\\Users\\Bentim\\Documents\\TEM Data\\%s Data\\%s' %(type, now.strftime('%b %d, %Y'))

        # if the folder doesnt exsist, make it
        if not os.path.exists(mypath):
            os.makedirs(mypath)
        
        
        #writes to file
        with open(mypath + '\\%s at %s.csv'%(type,now.hour), 'w+') as csvfile:
            df.to_csv(csvfile, index=False)
        
            if self.e ==False:
                csvfile.close()
    
    


   

    #----------------------------------------------------------------------------------------------------------------------
    # UPDATES FROM UI HANDLED BELOW
    #----------------------------------------------------------------------------------------------------------------------
    #----------------------------------------------------------------------------------------------------------------------
    # This function (insert descriptive notes here)
    def uiCombobox1Changed(self):
        if self.closing:
            return
        
        
        value = self.comboBox1.currentIndex()
               
        print('Combobox has value changed to index ' + str(value))

    #----------------------------------------------------------------------------------------------------------------------
    #this function (insert descriptive notes here)
    def uispinbox1Changed(self):
        if self.closing:
            return
        print('Spinbox value has changed to: ' + str(self.spinbox1.value()))
        #call other functions here if necessary
    
    #----------------------------------------------------------------------------------------------------------------------
    #this function (insert descriptive notes here)
    def uiModeChanged(self, value):

        """
        This function changes the labels of the graph according to whatever radio box value of the radiobox is pressed.
        """
        if self.closing:
            return
        print('we changed radio buttons here to ' + str(value) + '.')
        #call other functions here if necessary, like this

        if self.radio1.isChecked() == True:
            self.radio2.setChecked(False)
            self.radio3.setChecked(False)
            self.lineProfile1.setLabel('left', 'Magnetic Field', units = 'Gauss')
            self.lineProfile1.setTitle("Magnetic field vs. Time")


        if self.radio2.isChecked() == True:
            self.radio1.setChecked(False)
            self.radio3.setChecked(False)
            self.lineProfile1.setLabel('left', 'Temperature', units = 'C')
            self.lineProfile1.setTitle("Temperature vs. Time")


        if self.radio3.isChecked() == True:
            self.radio2.setChecked(False)
            self.radio1.setChecked(False)
            self.lineProfile1.setLabel('left', 'Pressure', units = 'p')
            self.lineProfile1.setTitle("Pressure vs. Time")    
    

    #----------------------------------------------------------------------------------------------------------------------
    #this function called to update the top plot, not the bottom one
    def imageUpdate1(self,xData):
        Index = self.comboBox1.currentIndex()
        """
        the function controls the range of values presented on the graph. it is determined by the combobox index value chosen by the user.
        
        there are 4 settings:
        default - this shows all the data, but only works up to a certain point as to not congest the frame
        90s - shows the previous 90s of data
        5min - shows the previous 5min of data
        10min - shows the previous 10min of data
        
        """
        if self.closing:
            return
        
        if Index == 0:
            if xData[-1] > 90:
                self.comboBox1.setCurrentIndex(1)
        if Index ==1:
            if xData[-1]>90:
                self.lineProfile1.setXRange(int(xData[-1]-90),int(xData[-1]+5), padding = 0.01)           
            else:
                print('Not enough Data')
                self.comboBox1.setCurrentIndex(0)
        if Index ==2:
            if xData[-1]>=5*60:
                self.lineProfile1.setXRange(int(xData[-1]-(5*60)),int(xData[-1]+5), padding = 0.01) 
            else:
                print('Not enough Data')
                self.comboBox1.setCurrentIndex(0)
        if Index ==3:
            if xData[-1]>=600:
                self.lineProfile1.setXRange(int(xData[-1]-(10*60)),int(xData[-1]+5), padding = 0.01)         
            else:
                print('Not enough Data')
                self.comboBox1.setCurrentIndex(0)
        

    
    #----------------------------------------------------------------------------------------------------------------------
    #this function called to update the bottom plot, not the top one
    def imageUpdate2(self,xData,yData):
        if self.closing:
            return
        #self.line1.setData(self.plotX, np.zeros_like(range(0,120)))
        self.line1.plot("2nd RTD", xData,yData, 'r')
    

    
    #----------------------------------------------------------------------------------------------------------------------
    #make a clean shutdown, only if intended though!
    def closeEvent(self,event):
        #generate a popup message box asking the user if they REALLY meant to shut down the software
        #note that unless they've saved variable presets etc, they would lose a lot of data if they accidentally shut down the program
        reply = QMessageBox.question(self,'Closing?', 'Are you sure you want to shut down the program?', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)

        #respond according to the user reply
        if reply == QMessageBox.StandardButton.Yes:
            self.closing = True
            event.accept()
            if self.e == True:
                self.stopRun()

        else:
            event.ignore()

def main():

    #instantiate the application
    app = QApplication(sys.argv)
    #link the window to a variable, set the window to be visible
    screen = MainWindow()
    screen.show()
    
    #halt execution here until the window is closed
    sys.exit(app.exec())
    

if __name__ == '__main__':
    main()