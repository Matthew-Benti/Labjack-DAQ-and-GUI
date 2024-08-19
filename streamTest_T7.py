from labjack import ljm
import sys
import numpy as np
from datetime import datetime, date
from math import log, sqrt as ln, sqrt 
from pandas import DataFrame
import csv
import os
from threading import Thread, Timer

class DAQ():


    """
    this class is designed exclusivvely for converting voltages read from the labjack T7
    to values of temperature, magnetic field strength, and pressure.

    the following functions "TData", "PData", and "MData" are all extremely similar in how they operate, 
    they follow the following premise:
     - voltage of sensor is grabbed from the labjack and converted into its respective value
     - the time of when the conversion took place is tracked in "timeData" list
     - all sensor data are stored in a bundle of lists, where each list in the bundle corresponds to the
     Data from ONE sensor
     - file lists are made in a similar way where it contains a bundle of sensor data, but it has been made so that
     filelists are only appended to once a minute, with the value appened being an average of data from the sensor
     over that minute.
     - the residual if statments are all meant ot regulate the size of each list so the code can run indefinetly without crashing
     for example, to ensure smoothness, the lists containing the continuous data of the sensor will only contain a max of 15 min
     of data at any time.

    """

    ###############################
    # INITIALIZATIONS FOR TEMP
    ###############################

    timeDataT= []
    filelistT1 = []
    spikeTimeT = []
    spikeThreadRunningT = True

    
    


    ###############################
    # INITIALIZATIONS FOR PRESSURE
    ###############################

    threshold = 1000
    
    spikeTimeP = []
    timeDataP = []
    filelistP1 = []
    


    ###############################
    # INITIALIZATIONS FOR MAGNETICS
    ###############################


    timeDataM = []
    filelistM1 = []
    spikeThreadRunningP = True





    def __init__(self):
        self.handle = ljm.openS("T7", "ANY", "ANY")
        self.start=datetime.now()

    def TData(self,AIN : dict, Data: dict, ResValues: dict, spikeData, derAvg: dict ,filelist: dict, fileBufferList: dict):
        """
        This function grabs temperature from the RTD
        by taking the recorded voltage from the RTD and using  
        the "lineraized" relationship between the voltage that 
        a PT100 RTD outputs and temeperature.
            
        This process is ran repeatedly on the GUI code. the function outputs 
        four lists. the first tracks each second the code is being ran the second
        is a list with as many lists as analog inputs being used with RTD's, storing 
        temperature from each RTD in a seperate list, but all lists are bundled together
        in 

        The relationship between voltage and temperature for a PT100
        can be found here https://blog.beamex.com/pt100-temperature-sensor#Pt100-sensors

        parameters are:

         AIN - list of analog inputs connected to a RTD

         Data - list with as many empty lists at analog inputs used

         ResValues - list containing the resistence values each wire contributes at each input; this MUST correspond
         exactly with the order of the list AIN

         filelist - list that will be used to write csv files contianing the data (uploads once a minute containing an average
         of the data over that minute)

         list - a buffer list which will be used to create the averages needed in filelist

        """


        self.stop = datetime.now()
        self.time = (self.stop-self.start).seconds + float((self.stop-self.start).microseconds)/1000000
       
        #stores the time this iteration of the loop was ran
        self.timeDataT.append(self.time)
        self.spikeTimeT.append(self.stop.strftime('%H:%M:%S'))

        # initializes constants used in the Callendar Van-Durst equation
        A = 3.9083e-3
        B = -5.775e-7
        Rfixed = 1000
        Res0 = 100
        
        # For each input, convert the voltage received to temperature, storing them in seperate lists for each sensor
        for sensor in AIN:
            voltage = ljm.eReadName(self.handle,sensor)
            Rtd = (Rfixed*(2.5-voltage))/voltage
            Res = Rtd - ((3/2)*ResValues[sensor])
            TempC = (-A+sqrt(A**2-4*B*(1-Res/Res0)))/(2*B)

            # All lists dealing with acquiring data
            Data[sensor].append(TempC)
            spikeData[sensor].append(TempC)
            #"fileBufferList" is a list that is used to average out data used in the file
            fileBufferList[sensor].append(TempC)


        # regulates the list to not store values longer then 15min
        if self.time >= 60*15:
            self.timeDataT.pop(0)
            for sensor in Data.values():
                sensor.pop(0)
            

        # appends data to file lists every minute
        if self.stop.second == 0:
            self.filelistT1.append(self.stop.strftime('%H:%M'))
            for sensor in AIN:
                #stores the averaged out values of list in filelist
                filelist[sensor].append(
                    round(sum(fileBufferList[sensor])/len(fileBufferList[sensor]),3)
                    )

        # this loop sets the size of the lists being written to the spike file as well as the list used to take derivatives
        if self.time>= 60*2:
            self.spikeTimeT.pop(0)      
            for sensor in AIN:
                
                # the derAvg sensor sums up the all the data from the sensor in the previous 2 minutes, averages them out to clear out any noise,
                # appends it, and then stores them into a list which will later take the derivative of this
                derAvg[sensor].append(sum(spikeData[sensor])/len(spikeData[sensor]))

                spikeData[sensor].pop(0)

                # at any given time the list will only have 2 min worth of derivative Data
                if self.time >= 4*60:
                    derAvg[sensor].pop(0)

                    

        #sets size of fileBuffer list to only have a minute worth of Data
        if self.time>= 60:
            for sensor in fileBufferList.values():
                sensor.pop(0)
                    
 
        # since filelistx is only storing the minute each point is being appended to file list, at the beginning of the hour it must be reset, with file list as well
        # this is because a new file gets created every hour
        if self.stop.minute == 0 and self.stop.second==0:
            self.filelistT1.clear()
            for sensor in filelist.values():
                sensor.clear()
        
        # Resets all graphical data at the beginning of the day
        if (self.stop.hour, self.stop.minute, self.stop.second) == (0,0,0):
            self.timeDataT.clear()
            for sensor in Data.values():
                sensor.clear()
            self.start = datetime.now()


        #function for checking spike is called here
        self.derivativeFunction(spikeData,derAvg,AIN)
        
        return self.timeDataT, Data, self.filelistT1, filelist

    def PData(self,AIN : dict, Data: dict, filelist: dict, fileBufferList: dict,spikeData : dict):

        """
        This class is used to convert the voltage given by the TP-020 Ion pump to a pressure. 
        The analog input range of the Labjack must be kept at +-0.01V for the best resoltution.
    
        The class works by aquiring the voltage from the ion pump and using the linear relationship 
        between voltage and current to find current. we then use the logarithmic relationship between 
        current and pressure to find pressure.
    
        Similar to the DAQ, this process is ran repeatedly in the GUI code
        """
        
        self.stop = datetime.now()
        self.time = (self.stop-self.start).seconds + float((self.stop-self.start).microseconds)/1000000

        #stores the time this iteration of the loop was ran        
        self.timeDataP.append(self.time)        
        self.spikeTimeP.append(self.stop.strftime('%H:%M:%S'))
        
        # For each input, convert the voltage received to pressure, storing them in seperate lists for each sensor
        for sensor in AIN:
            voltage = ljm.eReadName(self.handle,sensor)
            pressure = (10**(-0.74))*(voltage)
            Data[sensor].append(pressure)
            # "fileBufferList" is a buffer list whos purpose is just to get an average of all the values inside it, to then store it in filelist
            fileBufferList[sensor].append(pressure)

            # this list is only used when a spike is recorded in the graph
            
            spikeData[sensor].append(pressure)
            if pressure >= self.threshold:
                spikeThread = Timer(60,self.storeSpike,args=[spikeData,self.spikeTimeP,AIN, 'Pressure'])
                if self.spikeThreadRunningP == True:
                    self.spikeThreadRunningP = False
                    print('Pressure spike detected at %s!' %self.stop.strftime('%H:%M:%S'))

                    spikeThread.start()

        #print(len(spikeData[0]),len(self.spikeTime))

        
        # regulates the list to not store values longer then 15min                 
        if self.time >= 60*15:
            self.timeDataP.pop(0)
            for sensor in Data.values():
                sensor.pop(0)

        # appends data to file lists every minute
        if self.stop.second == 0:
            self.filelistP1.append(self.stop.strftime('%H:%M'))
            #stores the averaged out values of list in filelist
            for sensor in AIN:
                filelist[sensor].append(
                    round(sum(fileBufferList[sensor])/len(fileBufferList[sensor]),1)
                    
                    )

        #sets size of fileBuffer list to only have a minute worth of Data
        if self.time>= 60:
            for sensor in AIN:
                fileBufferList[sensor].pop(0)

        # since filelistx is only storing the minute each point is being appended to file list, at the beginning of the hour it must be reset, with file list as well
        # this is because a new file gets created every hour
        if self.stop.minute == 0 and self.stop.second==0:
            self.filelistP1.clear()
            for sensor in filelist.values():
                sensor.clear()
        
        # Resets all graphical data at the beginning of the day
        if (self.stop.hour, self.stop.minute, self.stop.second) == (0,0,0):
            self.timeDataP.clear()
            for sensor in Data.values():
                sensor.clear()
            self.start = datetime.now()



        # stores spike data only up to 3 minutes
        if self.time>= 60*3:
            self.spikeTimeP.pop(0)
            for sensor in spikeData.values():
                sensor.pop(0)

        # if a spike is recorded trigger a thread to store the data
            
        return self.timeDataP, Data, self.filelistP1, filelist

    
    def MData(self,AIN : list, Data: list, filelist: list, fileBufferList: list):
        """
        This function converts analog input voltage into a Gaussian measurement. the correlation between
        received voltage and field strength ois given on the magcheck-95, which states 1mV AC= 1mG

        this is also looped in the GUI to produce a graph
        """
        
        #stores the time this iteration of the loop was ran
        self.stop = datetime.now()
        self.time = (self.stop-self.start).seconds + float((self.stop-self.start).microseconds)/1000000
        self.timeDataM.append(self.time)
        
        # For each input, convert the voltage received to field strength, storing them in seperate lists for each sensor
        for sensor in AIN:

            voltage = ljm.eReadName(self.handle,sensor)
            flux = voltage
            Data[sensor].append(flux)

            # "fileBufferList" is a buffer list whos purpose is just to get an average of all the values inside it, to then store it in filelist
            fileBufferList[sensor].append(flux)

           
        #self.MagData.append(flux)

        # regulates the list to not store values longer then 15min   
        if self.time >= 60*15:
            self.timeDataM.pop(0)
            for sensor in Data.values():
                sensor.pop(0)

        # appends data to file lists every minute
        if self.stop.second == 0:
            self.filelistM1.append(self.stop.strftime('%H:%M'))
            #stores the averaged out values of list in filelist
            for sensor in AIN:
                filelist[sensor].append(
                    (round((sum(fileBufferList[sensor])/len(fileBufferList[sensor])),6))*1000
                    )

        #sets size of fileBuffer list to only have a minute worth of Data
        if self.time>= 60:
            for sensor in fileBufferList.values():
                sensor.pop(0)

        # since filelistx is only storing the minute each point is being appended to file list, at the beginning of the hour it must be reset, with file list as well
        # this is because a new file gets created every hour
        if self.stop.minute == 0 and self.stop.second==0:
            self.filelistM1.clear()
            for sensor in filelist.values():
                sensor.clear()
        
        # Resets all graphical data at the beginning of the day
        if (self.stop.hour, self.stop.minute, self.stop.second) == (0,0,0):
            self.timeDataM.clear()
            for sensor in Data.values():
                sensor.clear()

            self.start = datetime.now()

        return self.timeDataM, Data, self.filelistM1, filelist

    

    def storeSpike(self,spikeData: dict, timeData: list, AIN: list, type: str):
        """
        This function is responsible for what happens when a spike is recorded, whether by value in the case of 
        pressure, or by derivative in the case of temp. 

        The function adds data to a spike folder and spikefile formatted in similar fashion to the fileWriter function in the GUI
        but instead it logs data everysecond as apposed to every minute
        
        
        """

        row = spikeData.copy()

        now = datetime.now()

        row.update({'Time': timeData.copy()})

    
        df = DataFrame(row)

        mypath = 'C:\\Users\\Bentim\\Documents\\TEM Data\\%s Data\\Spike Data\\%s' %(type,now.strftime('%b %d, %Y'))
        if not os.path.exists(mypath):
            os.makedirs(mypath)
        
        with open(mypath + '\\ %s Data at %s;%s .csv' %(type, now.strftime('%H'), now.strftime('%M')), 'w+') as csvfile:
            df.to_csv(csvfile, index=False)
  

        print('Spike has been recorded')


        if self.spikeThreadRunningP == False:
            self.spikeThreadRunningP = True
        if self.spikeThreadRunningT == False:
            self.spikeThreadRunningT = True

    def derivativeFunction(self,spikeData, derAvg, AIN):
        """
        This function is used exclusively for temperature.
        
        the goal of this funciton is to take the derivatve of "derAvg" and depedning on its value 
        it will pass the data from "spikeData" into the "storeSpike" function"""
        for sensor in AIN:
            if len(derAvg[sensor])>=3:
                dydx = np.gradient(derAvg[sensor])
                # find a way to delete data so that the same element in dydx doesnt keep triggering the spike funciton

                if dydx[-1]>= 0.02 or dydx[-1]<=-0.02:
                        spikeThread = Timer(60, self.storeSpike, args = [spikeData,self.spikeTimeT,AIN, 'Temp'])
                        if self.spikeThreadRunningT == True:
                            self.spikeThreadRunningT = False
                            print('Temperature spike detected at %s!' %self.stop.strftime('%H:%M:%S'))
                            spikeThread.start()



    def stopRun(self):
        """
        resets all time-related data, when used in conjunction with the stop run of the GUI, it will reset the graphs and their data
        """
        # FOR TEMP
        self.timeDataT.clear()
        #self.filelistT1.clear()


        # FOR PRESSURE
        self.timeDataP.clear()
        #self.filelistP1.clear()

        # FOR MAG
        self.timeDataM.clear()
        #self.filelistM1.clear()


