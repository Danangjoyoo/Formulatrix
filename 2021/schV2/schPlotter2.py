import numpy as np
import time, threading, sys, os
import matplotlib.pyplot as plt
from visualize import printg, printr, printy, printb
import pandas as pd
from matplotlib.animation import FuncAnimation
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg

"""
============ ### NOTES ### ====================

!!!!!!!!!! README !!!!!!!!!!
- You can stream sensors reading by just using liveplot()
- If you want to execute a function while liveplotting, use run() but with caution:
    - These plotters can't be executed in subthread, only able to be executed in main thread
    - So your executed function will be executed in the subthread.
    - Make sure your executed function is able to execute in subthread instead of main thread.
    - Make sure you have safety break in your function (Highly recommended for function with iterations (loop))
    - To increase the safety, there is a function to stop liveplotting --> terminate()
- This plotter might only works with FLO v2 single channel, your object should be pointing to firmware call (p or c.p)
- You have to override autoUpdate() method For any plotting outside the defaults.

Plotter --> Matplotlib Plotter (Python Build)
+ Saver use
+ No disturb other event hooks
- Low Speed (70-300 ms/tick)

CPlotter --> PyQt Plotter (C/C++ Wrapper)
+ High Speed (10 - 70 ms/tick)
- Usually Disturbs other event hooks (pyreadline, etc)
- This disturbance make some function of other event hooks is disabled (Keyboard Interrupt)
- To recover from this error, just manually exit your program and start your script again.


## FUTURE
The safer plotter is being developed..

"""

class Plotter():
    def __init__(self, obj):
        # Live Plot
        self.object = obj
        self.plotStat = False
        self.func = None
        self.init_t = time.perf_counter()
        self.tick = 0
        self.tickPack = []
        self.thread = None
        self.init_travel = 0
        self.avgTime = []
        self.x = []
        self.limit = 50
        self.init = True
        self.current_t = 0
        self.before_t = 0
        self.init_travel = 0
        self.before_travel = 0
        self.current_vel = 0
        self.before_vel = 0
        self.current_acc = 0
        self.before_acc = 0
        self.varPack = { 
            'travel': [[], 'travel' , False, 1, 0],
            'vel'   : [[], 'vel'    , False, 1, 0],
            'acc'   : [[], 'acc'    , False, 1, 0],
            'col'   : [[], 'col'    , False, 1, 0],
            'res'   : [[], 'res'    , False, 1, 0],
            'p1'    : [[], 'p1 '    , False, 1, 0],
            'p2'    : [[], 'p2 '    , False, 1, 0] }  

    #==================== REALTIME PLOTTER =====================
    def run(self,*args): #function, param1, param2, dll
        if args:
            printg('Realtime Plotter Started..')
            newArgs = list(args)
            func = newArgs.pop(0)
            if len(args) > 1:
                params = tuple(newArgs)
                self.thread1 = threading.Thread(target=func,args=params)                
            else:
                self.thread1 = threading.Thread(target=func)
            self.thread1.start()
            time.sleep(0.1)
            # set sensor yang mau diplot <nama sensor>=True di parameter
            self.liveplot(p2=True)
            printg('Realtime Plotter Finished..')
            self.reset_realtime()
        else:
            printr('Please input function!')

    def raiseProcess(self):
        if self.thread1.isAlive():
            printy('Raising the background process to the foregound! Please wait..')
            printy('Check the blocking status at Terminal/Console/CMD!')
            self.thread1.join()
            printy(self.func, 'is Raised.. now u can terminate')
        else:
            printr('Background is unregistered!')       
        self.thread1 = None

    @staticmethod
    def forceKill():
        printr('FORCE KILL MAIN APP')
        sys.exit()

    def reset_realtime(self):
        printy('Variables changed to default')
        self.plotStat = False
        self.init_t = time.perf_counter()
        self.tick = 0
        self.tickPack = []
        self.init_travel = 0
        self.avgTime = []
        self.x = []
        self.init = True
        for var in self.varPack: self.varPack[var][0] = []

    def resetVariables(self):
        self.varPack = { 
            'travel': [[], 'travel' , False, 1, 0],
            'vel'   : [[], 'vel'    , False, 1, 0],
            'acc'   : [[], 'acc'    , False, 1, 0],
            'col'   : [[], 'col'    , False, 1, 0],
            'res'   : [[], 'res'    , False, 1, 0],
            'p1'    : [[], 'p1 '    , False, 1, 0],
            'p2'    : [[], 'p2 '    , False, 1, 0] }
    
    def setSensor(self,**sens): # untuk set sensor dari terminal dan limit
        container, label, showStat, scale = 0, 1, 2, 3
        if 'limit' in sens: self.limit = sens['limit']
        for sensor in sens:
            if sensor in self.varPack:
                self.varPack[sensor][showStat] = sens[sensor]
                print(sensor+" plot:", sens[sensor])

    def setScale(self,**vars): # untuk scaling chart
        container, label, showStat, scale = 0, 1, 2, 3
        if vars:
            for var in vars:
                if var in self.varPack:
                    self.varPack[var][scale] = vars[var]
                    print(var+"'s scale:", vars[var])
        else:
            print('No Scale is Changed')

    def setOffset(self,**vars): # untuk offsetting chart
        container, label, showStat, offset = 0, 1, 2, 4
        if vars:
            for var in vars:
                if var in self.varPack:
                    self.varPack[var][offset] = vars[var]
                    print(var+"'s offset:", vars[var])
        else:
            print('No Offset is Changed')
    
    def checkVar(self):
        print("Tick Limit in frame :", self.limit)
        for var in self.varPack:
            val = self.varPack[var]
            print("Var: {}\t| Plot: {}\t| Scale: {}\t| Offset: {}\t".format(val[1],val[2],val[3],val[4]))

    def liveplot(self,**show):
        container, label, showStat, offset = 0, 1, 2, 4
        if show:
            for key in self.varPack.keys(): self.varPack[key][showStat] = False
            for key in self.varPack.keys(): self.varPack[key][container] = []
            self.x = []
            self.setSensor(**show)
            self.plotStat = True
            ani = FuncAnimation(plt.gcf(), self.autoUpdate, interval=5)
            plt.show()
        else:
            printr("Input sensor that you want to plot! (Ex: p2=True, p1= True)")

    def autoUpdate(self,i):
        if self.plotStat:
            t1 = time.perf_counter()
            # Initialization =======================
            container, label, showStat, scale, offset = 0, 1, 2, 3, 4
            if self.init:
                self.init_t = time.perf_counter()
                self.current_t = time.perf_counter() - self.init_t
                self.before_t = 0
                self.init_travel = abs(self.object.get_encoder_position(0))
                self.before_travel = 0
                self.current_vel = 0
                self.before_vel = 0
                self.current_acc = 0
                self.before_acc = 0
                self.init = False
                time.sleep(0.1)
            # set limit
            if len(self.x) >= self.limit:
                self.tickPack.pop(0)
                self.x.pop(0)
                for var in self.varPack: self.varPack[var][container].pop(0)
            # movement
            self.tick += 1
            self.current_t = round(time.perf_counter() - self.init_t, 3)                 
            self.current_travel = abs(self.object.get_encoder_position(0))-self.init_travel
            self.current_vel = (self.current_travel-self.before_travel)/(self.current_t-self.before_t)
            self.current_acc = (self.current_vel - self.before_vel)/(self.current_t-self.before_t)
            self.before_t = self.current_t
            self.before_travel = self.current_travel
            self.before_vel = self.current_vel
            self.before_acc = self.current_acc
            # other sensor
            col = self.object.read_sensor(1)
            res = self.object.read_sensor(0)
            p1 = self.object.read_sensor(16)
            p2 = self.object.read_sensor(32)
            # ADD DATA
            self.tickPack.append(self.tick)
            self.x.append(self.current_t)
            self.varPack['travel'][container].append(self.current_travel*self.varPack['travel'][scale]+self.varPack['travel'][offset])
            self.varPack['vel'   ][container].append(self.current_vel*self.varPack['vel'][scale]+self.varPack['vel'][offset])
            self.varPack['acc'   ][container].append(self.current_acc*self.varPack['acc'][scale]+self.varPack['acc'][offset])
            self.varPack['col'   ][container].append(col*self.varPack['col'][scale]+self.varPack['col'][offset])
            self.varPack['res'   ][container].append(res*self.varPack['res'][scale]+self.varPack['res'][offset])
            self.varPack['p1'    ][container].append(p1*self.varPack['p1'][scale]+self.varPack['p1'][offset])
            self.varPack['p2'    ][container].append(p2*self.varPack['p2'][scale]+self.varPack['p2'][offset])
            # starting to plot
            plt.cla()
            for var in self.varPack:
                if self.varPack[var][showStat]:
                    plt.plot(self.x, self.varPack[var][container], linewidth=1, label=var)
            elapsedTime = round((time.perf_counter() - t1)*1000.0, 4)
            plt.legend(loc='upper left')
            plt.xlabel('time (s)')
            plt.title('Sensor Plotter | {} ms/tick'.format(elapsedTime))
            plt.text(100,100,str(self.limit))
            # end of plotting =======================
            #print(1/elapsedTime,end='\r')
        else:
            plt.close()
            plt.close('all')

    def terminate(self):
        self.plotStat = False

class CPlotter():
    #============================= LIVE PLOTTER USING QT ===============================
    def __init__(self, obj):
        self.object = obj
        self.init = False
        self.plotStat = False
        self.init_t = time.time()
        self.avgTime = []
        self.x = []
        self.thread = None
        self.func = None
        self.args = None
        self.quit = True
        self.limit = 100
        self.win = None
        self.current_t = 0
        self.before_t = 0
        self.init_travel = 0
        self.before_travel = 0
        self.current_vel = 0
        self.before_vel = 0
        self.current_acc = 0
        self.before_acc = 0
        self.logs = [[]]
        self.varPack = {
            'travel': [[], 'travel', False, 1.0, 0.0],
            'vel': [[], 'vel', False, 20.0, 0.0],
            'acc': [[], 'acc', False, 1.0, 0.0],
            'col': [[], 'col', False, 1.0, 0.0],
            'res': [[], 'res', False, 0.4, 0.0],
            'p1': [[], 'p1', False, 3.0, -2000.0],
            'p2': [[], 'p2', False, 3.0, -2000.0]
        }

        self.fname = None
        self.n = 0

    def run(self,*args,**kargs): #function, param1, param2, dll
        if args:
            if kargs:
                if 'quit' in kargs: self.quit = kargs['quit']
            else:
                self.quit = True
            printg('Realtime Plotter Started..')
            newArgs = list(args)
            self.func = newArgs.pop(0)
            self.args = tuple(newArgs) if len(args) > 1 else None                
            self.thread1 = threading.Thread(target=self.execute)
            self.thread1.start()
            time.sleep(0.1)
            # set sensor yang mau diplot <nama sensor>=True di parameter
            self.liveplot(p1=True,p2=True,vel=True,res=True)
            if self.thread1.isAlive(): 
                printg('waiting for thrad to be done')
                self.thread1.join()
            printg('Live Plotter Finished.. ')
        else:
            printr('Please input function!')

    def execute(self):
        time.sleep(2)
        self.func(*self.args) if self.args else self.func()
        time.sleep(2)
        if self.quit: self.plotStat = False

    def liveplot(self,*s,**show):
        self.init = True
        self.plotStat = True
        self.win = pg.GraphicsLayoutWidget(show=True)
        self.win.resize(1000,600)
        self.win.setWindowTitle('Live Plotter')
        self.wiplot = self.win.addPlot(title='CPlotter')
        self.wiplot.addLegend()
        self.wiplot.setLabel('bottom','Ticks','n')
        self.fname = 'PlotterLog/CPlotter_{}.csv'.format(int(time.time()))
        self.current_t = 0
        self.before_t = 0
        self.init_travel = 0
        self.before_travel = 0
        self.current_vel = 0
        self.before_vel = 0
        self.current_acc = 0
        self.before_acc = 0
        self.x = []
        self.n = 1
        container, label, showStat, scale, offset, plotClass = 0, 1, 2, 3, 4, 5
        if 'limit' in show: self.limit = show['limit']
        for var in self.varPack:
            if show:
                self.varPack[var][showStat] = show[var] if var in show else False
            if s:
                if 7 in s: self.varPack[var][showStat] = True
                else: self.varPack[var][showStat] = True if var in s else False
        labelTravel, labelVel, labelAcc, labelCol, labelRes, labelP1, labelP2 = [None for i in range(7)]
        labels = [labelTravel, labelVel, labelAcc, labelCol, labelRes, labelP1, labelP2]
        colors = [(255,150,25),'y','b','g','c',(100,40,250),(220,60,19)]
        for i, key in enumerate(self.varPack.keys()): 
            labels[i] = key if (self.varPack[key][scale] == 1 and not self.varPack[key][offset]) else key+' (scaled)'
            if self.varPack[key][showStat]:
                self.varPack[key].append(self.wiplot.plot(pen=colors[i], name=labels[i]))
        self.writeLog(['tick','time',*self.varPack.keys()])
        printy("IGNORE ANY ERROR..")
        timer = QtCore.QTimer()
        timer.timeout.connect(self.autoUpdate)
        timer.start(0)
        try:
            QtGui.QApplication.instance().exec_()
        except:
            pass
        for key in self.varPack.keys():
            self.varPack[key][0] = []
            if len(self.varPack[key])-1 == plotClass:
                self.varPack[key].pop(plotClass)
        printy("IGNORE ANY ERROR..")

    def autoUpdate(self):
        if self.plotStat:
            t1 = time.perf_counter()
            # start to add data =======================
            container, label, showStat, scale, offset, plotClass = 0, 1, 2, 3, 4, 5         
            if self.init:
                self.init_t = time.perf_counter()
                self.current_t = time.perf_counter() - self.init_t
                self.before_t = 0
                self.init_travel = abs(self.object.get_encoder_position(0))
                self.before_travel = 0
                self.current_vel = 0
                self.before_vel = 0
                self.current_acc = 0
                self.before_acc = 0
                self.init = False
                time.sleep(0.1)
            # set limit
            if len(self.varPack['travel'][0]) > self.limit:
                for var in self.varPack: self.varPack[var][container].pop(0)
            else:
                self.x = [i+1 for i in range(len(self.varPack['travel'][0])+1)]
            # Movement
            self.current_t = round(time.perf_counter() - self.init_t, 3)
            self.current_travel = abs(self.object.get_encoder_position(0))-self.init_travel
            self.current_vel = (self.current_travel-self.before_travel)/(self.current_t-self.before_t)
            self.current_acc = (self.current_vel - self.before_vel)/(self.current_t-self.before_t)
            self.before_t = self.current_t
            self.before_travel = self.current_travel
            self.before_vel = self.current_vel
            self.before_acc = self.current_acc
            # Sensors
            col = self.object.read_sensor(1)
            res = self.object.read_sensor(0)
            p1 = self.object.read_sensor(6)
            p2 = self.object.read_sensor(7)
            vals = [self.current_travel, self.current_vel, self.current_acc, col, res, p1, p2]
            # ADD DATA
            for i, key in enumerate(self.varPack): self.varPack[key][container].append(vals[i]*self.varPack[key][scale]+self.varPack[key][offset])
            # start to plot
            for var in self.varPack: self.varPack[var][plotClass].setData(self.x,self.varPack[var][container]) if self.varPack[var][showStat] else None
            # end of plotting ======================= save to logs
            self.writeLog([self.n,self.current_t,*vals])
            self.n += 1
            spd = round((time.perf_counter() - t1)*1000.0,1)
            self.wiplot.setLabel('top',f'{spd} ms/tick')
        else:
            self.win.close()

    def terminate(self):
        self.plotStat = False

    def writeLog(self,vals):
        dataStr = ''
        f = open(self.fname, 'a')
        for val in vals: dataStr += str(val)+','
        f.write(dataStr+'\n')
        f.close()

    def setSensor(self,**sens): # untuk set sensor dari terminal dan limit
        container, label, showStat, scale = 0, 1, 2, 3
        if 'limit' in sens: self.limit = sens['limit']
        for sensor in sens:
            if sensor in self.varPack:
                self.varPack[sensor][showStat] = sens[sensor]
                print(sensor+" plot enabled")

    def setScale(self,**vars): # untuk scaling chart
        container, label, showStat, scale = 0, 1, 2, 3
        if vars:
            for var in vars:
                if var in self.varPack:
                    self.varPack[var][scale] = vars[var]
                    print(var+"'s scale:", vars[var])
        else:
            print('No Scale is Changed')

    def setOffset(self,**vars): # untuk offsetting chart
        container, label, showStat, offset = 0, 1, 2, 4
        if vars:
            for var in vars:
                if var in self.varPack:
                    self.varPack[var][offset] = vars[var]
                    print(var+"'s offset:", vars[var])
        else:
            print('No Offset is Changed')

    def checkStatus(self):
        print('check')
        for var in self.varPack:
            print(var,'\t:', self.varPack[var][2])

class SPlotter():
    #============================= LIVE PLOTTER USING QT ===============================
    def __init__(self, obj):
        self.object = obj
        self.init = False
        self.plotStat = False
        self.init_t = time.time()
        self.avgTime = []
        self.x = []
        self.thread = None
        self.func = None
        self.args = None
        self.quit = True
        self.limit = 100
        self.win = None
        self.current_t = 0
        self.before_t = 0
        self.init_travel = 0
        self.before_travel = 0
        self.current_vel = 0
        self.before_vel = 0
        self.current_acc = 0
        self.before_acc = 0
        self.logs = [[]]
        self.varPack = {
            'travel': [[], 'travel', False, 1.0, 0.0],
            'vel': [[], 'vel', False, 20.0, 0.0],
            'acc': [[], 'acc', False, 1.0, 0.0],
            'col': [[], 'col', False, 1.0, 0.0],
            'res': [[], 'res', False, 0.4, 0.0],
            'p1': [[], 'p1', False, 3.0, -2000.0],
            'p2': [[], 'p2', False, 3.0, -2000.0]
        }

        self.fname = None
        self.n = 0

    def run(self,*args,**kargs): #function, param1, param2, dll
        if args:
            if kargs:
                if 'quit' in kargs: self.quit = kargs['quit']
            else:
                self.quit = True
            printg('Realtime Plotter Started..')
            newArgs = list(args)
            self.func = newArgs.pop(0)
            self.args = tuple(newArgs) if len(args) > 1 else None                
            self.thread1 = threading.Thread(target=self.execute)
            self.thread1.start()
            time.sleep(0.1)
            # set sensor yang mau diplot <nama sensor>=True di parameter
            self.liveplot(p1=True,p2=True,vel=True,res=True)
            if self.thread1.isAlive(): 
                printg('waiting for thrad to be done')
                self.thread1.join()
            printg('Live Plotter Finished.. ')
        else:
            printr('Please input function!')

    def execute(self):
        time.sleep(2)
        self.func(*self.args) if self.args else self.func()
        time.sleep(2)
        if self.quit: self.plotStat = False

    def liveplot(self,*s,**show):
        self.init = True
        self.plotStat = True
        self.win = pg.GraphicsLayoutWidget(show=True)
        self.win.resize(1000,600)
        self.win.setWindowTitle('Live Plotter')
        self.wiplot = self.win.addPlot(title='CPlotter')
        self.wiplot.addLegend()
        self.wiplot.setLabel('bottom','Ticks','n')
        self.fname = 'PlotterLog/CPlotter_{}.csv'.format(int(time.time()))
        self.current_t = 0
        self.before_t = 0
        self.init_travel = 0
        self.before_travel = 0
        self.current_vel = 0
        self.before_vel = 0
        self.current_acc = 0
        self.before_acc = 0
        self.x = []
        self.n = 1
        container, label, showStat, scale, offset, plotClass = 0, 1, 2, 3, 4, 5
        if 'limit' in show: self.limit = show['limit']
        for var in self.varPack:
            if show:
                self.varPack[var][showStat] = show[var] if var in show else False
            if s:
                if 7 in s: self.varPack[var][showStat] = True
                else: self.varPack[var][showStat] = True if var in s else False
        labelTravel, labelVel, labelAcc, labelCol, labelRes, labelP1, labelP2 = [None for i in range(7)]
        labels = [labelTravel, labelVel, labelAcc, labelCol, labelRes, labelP1, labelP2]
        colors = [(255,150,25),'y','b','g','c',(100,40,250),(220,60,19)]
        for i, key in enumerate(self.varPack.keys()): 
            labels[i] = key if (self.varPack[key][scale] == 1 and not self.varPack[key][offset]) else key+' (scaled)'
            if self.varPack[key][showStat]:
                self.varPack[key].append(self.wiplot.plot(pen=colors[i], name=labels[i]))
        self.writeLog(['tick','time',*self.varPack.keys()])
        printy("IGNORE ANY ERROR..")
        timer = QtCore.QTimer()
        timer.timeout.connect(self.autoUpdate)
        timer.start(0)
        try:
            QtGui.QApplication.instance().exec_()
        except:
            pass
        for key in self.varPack.keys():
            self.varPack[key][0] = []
            if len(self.varPack[key])-1 == plotClass:
                self.varPack[key].pop(plotClass)
        printy("IGNORE ANY ERROR..")

    def autoUpdate(self):
        if self.plotStat:
            t1 = time.perf_counter()
            # start to add data =======================
            container, label, showStat, scale, offset, plotClass = 0, 1, 2, 3, 4, 5         
            if self.init:
                self.init_t = time.perf_counter()
                self.current_t = time.perf_counter() - self.init_t
                self.before_t = 0
                self.init_travel = abs(self.object.get_encoder_position(0))
                self.before_travel = 0
                self.current_vel = 0
                self.before_vel = 0
                self.current_acc = 0
                self.before_acc = 0
                self.init = False
                time.sleep(0.1)
            # set limit
            if len(self.varPack['travel'][0]) > self.limit:
                for var in self.varPack: self.varPack[var][container].pop(0)
            else:
                self.x = [i+1 for i in range(len(self.varPack['travel'][0])+1)]
            # Movement
            self.current_t = round(time.perf_counter() - self.init_t, 3)
            self.current_travel = abs(self.object.get_encoder_position(0))-self.init_travel
            self.current_vel = (self.current_travel-self.before_travel)/(self.current_t-self.before_t)
            self.current_acc = (self.current_vel - self.before_vel)/(self.current_t-self.before_t)
            self.before_t = self.current_t
            self.before_travel = self.current_travel
            self.before_vel = self.current_vel
            self.before_acc = self.current_acc
            # Sensors
            col = self.object.read_sensor(1)
            res = self.object.read_sensor(0)
            p1 = self.object.read_sensor(6)
            p2 = self.object.read_sensor(7)
            vals = [self.current_travel, self.current_vel, self.current_acc, col, res, p1, p2]
            # ADD DATA
            for i, key in enumerate(self.varPack): self.varPack[key][container].append(vals[i]*self.varPack[key][scale]+self.varPack[key][offset])
            # start to plot
            for var in self.varPack: self.varPack[var][plotClass].setData(self.x,self.varPack[var][container]) if self.varPack[var][showStat] else None
            # end of plotting ======================= save to logs
            self.writeLog([self.n,self.current_t,*vals])
            self.n += 1
            spd = round((time.perf_counter() - t1)*1000.0,1)
            self.wiplot.setLabel('top',f'{spd} ms/tick')
        else:
            self.win.close()

    def terminate(self):
        self.plotStat = False

    def writeLog(self,vals):
        dataStr = ''
        f = open(self.fname, 'a')
        for val in vals: dataStr += str(val)+','
        f.write(dataStr+'\n')
        f.close()

    def setSensor(self,**sens): # untuk set sensor dari terminal dan limit
        container, label, showStat, scale = 0, 1, 2, 3
        if 'limit' in sens: self.limit = sens['limit']
        for sensor in sens:
            if sensor in self.varPack:
                self.varPack[sensor][showStat] = sens[sensor]
                print(sensor+" plot enabled")

    def setScale(self,**vars): # untuk scaling chart
        container, label, showStat, scale = 0, 1, 2, 3
        if vars:
            for var in vars:
                if var in self.varPack:
                    self.varPack[var][scale] = vars[var]
                    print(var+"'s scale:", vars[var])
        else:
            print('No Scale is Changed')

    def setOffset(self,**vars): # untuk offsetting chart
        container, label, showStat, offset = 0, 1, 2, 4
        if vars:
            for var in vars:
                if var in self.varPack:
                    self.varPack[var][offset] = vars[var]
                    print(var+"'s offset:", vars[var])
        else:
            print('No Offset is Changed')

    def checkStatus(self):
        print('check')
        for var in self.varPack:
            print(var,'\t:', self.varPack[var][2])



if __name__ == '__main__':
    print("Main")    