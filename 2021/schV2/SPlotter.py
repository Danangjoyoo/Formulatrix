import numpy as np
import time, threading, sys, os, json
import matplotlib.pyplot as plt
import seaborn as sns
from visualize import *
import pandas as pd
import tkinter as tk
from tkinter import filedialog as fd
from matplotlib.animation import FuncAnimation
from pyqtgraph.Qt import QtGui, QtCore, QtWidgets
import pyqtgraph as pg

"""
Shadow or ghost... it's unreachable...

"""
container, label, showStat, scale, offset, plotClass, streamLabel, plotStream = 0, 1, 2, 3, 4, 5, 6, 7

class SPlotter():
	#============================= LIVE PLOTTER USING QT ===============================
	# SetUp
	def __init__(self, obj):
		self.object = obj
		self.__init = False
		self.__plotStat = False
		self.__transmitterStat = False
		self.__init_t = time.time()
		self.avgTime = []
		self.__x = []
		self.thread = None
		self.__func = None
		self.__funcReturn = None
		self.__args = None
		self.quit = True
		self.__clean = True
		self.__win = None
		self.__current_t = 0
		self.__before_t = 0
		self.__init_pos = 0
		self.__before_pos = 0
		self.__current_vel = 0
		self.__before_vel = 0
		self.__current_acc = 0
		self.__before_acc = 0
		config = self.getConfig()
		self.staticVar = config['staticVar']
		self.varPack = config['varPack']
		self.__limit = config['limit']
		self.__sideStream = False
		self.logname = None
		self.__n = 0
		self.timer = None
		self.__lastVals = np.zeros(8)

	# Multiprocessing Communication
	def getConfig(self):
		with open('splotterConfig/config.json') as config:
			x = json.load(config)
			return x

	def __setConfig(self,key,dic):
		recentConf = self.getConfig()
		with open('splotterConfig/config.json', 'w') as config:
			recentConf[key] = dic
			json.dump(recentConf, config)

	def resetConfig(self,key=None,warn=True):
		with open('splotterConfig/originalConfig.json') as origin:
			recentConf = json.load(origin)
			if key:
				return recentConf[key]
			else:
				self.varPack = recentConf['varPack']
				self.__setConfig('varPack',self.varPack)
				self.staticVar = recentConf['staticVar']
				self.__setConfig('staticVar',self.staticVar)
				self.limit = recentConf['limit']
				self.__setConfig('limit',self.limit)
				if warn: printg("[SPlotter] All config changed to default..")

	def default(self,warn=True):
		self.resetConfig(warn=warn)

	@property
	def limit(self):
		return self.__getLimit
	@limit.setter
	def limit(self, val):
		self.__limit = int(val)
		self.__setConfig('limit', self.__limit)
	@limit.getter
	def __getLimit(self):
		return self.__limit

	@property
	def sideStream(self):
		return self.__getSideStream
	@sideStream.setter
	def sideStream(self,state):
		with open('splotterConfig/sideStreamStat.flo','w') as f:
			f.write(str(int(bool(state))))
	@sideStream.getter
	def __getSideStream(self):
		with open('splotterConfig/sideStreamStat.flo','r') as f:
			self.__sideStream = bool(int(f.read()))
		return self.__sideStream	

	@property
	def plotStat(self):
		return self.__getplotStat

	@plotStat.setter
	def plotStat(self, state):
		self.__plotStat = state
		try:
			with open('splotterConfig/plotStat.flo','w') as f:
				f.write(str(int(bool(state))))
		except: pass

	@plotStat.getter
	def __getplotStat(self):
		for i in range(10):
			try:
				with open('splotterConfig/plotStat.flo','r') as f:
					stat = bool(int(f.read()))
					self.__plotStat = True if stat else False
					break
			except: pass
		return self.__plotStat

	@property
	def transmitterStat(self):
		return self.__getTransmitterStat

	@transmitterStat.setter
	def transmitterStat(self, state):
		try:
			with open('splotterConfig/transmitter.flo','w') as f:
				f.write(str(int(bool(state))))
		except: pass

	@transmitterStat.getter
	def __getTransmitterStat(self):
		try:
			with open('splotterConfig/transmitter.flo','r') as f:
				stat = bool(int(f.read()))
				self.__transmitterStat = True if stat else False
		except: pass
		return self.__transmitterStat	

	def __sendValue(self,*vals):
		s = ''
		with open('splotterConfig/data.flo','w') as file:
			for i, data in enumerate(vals):
				s += str(data) + ',' if i+1 < len(vals) else str(data)
			file.write(s)

	def __receiveValue(self):
		try:
			with open('splotterConfig/data.flo','r') as file:
				data = file.read()
				data = data.split(',')
				if len(data) == 11:
					self.__lastVals = [float(i) for i in data]
		except:
			pass
		return self.__lastVals

	# Plotting
	def run(self,*args,**kargs): #function, param1, param2, dll
		if self.object:
			if args:
				newArgs = list(args)
				self.__func = newArgs.pop(0)
				self.__args = tuple(newArgs) if len(args) > 1 else None                
				if kargs:
					if 'quit' in kargs: self.quit = kargs['quit']
					self.setSensor(**kargs)
				else:
					self.quit = True
				self.liveplot()
				self.__execute()
			else:
				printr('Please input function!')
		else:
			printg('Realtime Plotter Started..')				
			time.sleep(0.1)
			self.resetVariables()
			printg('Live Plotter Finished.. ')

	def __execute(self):
		time.sleep(2)
		self.__funcReturn = self.__func(*self.__args) if self.__args else self.__func()
		time.sleep(2)
		if self.quit: 
			self.terminate()

	def __shadowProcess(self): # Conventional Multiprocessing, you cant grab anything from the shadow xD
		printb("Shadow Plotter initialized..")
		def shade(): os.system(f"python3 {__name__}.py")
		shadowThread = threading.Thread(target=shade)
		shadowThread.start()
		while not self.transmitterStat: pass		

	def getReturn(self):
		return self.__funcReturn

	def liveplot(self,*s,**show):
		if self.object:
			self.plotStat = True
			self.setSensor(*s,**show)
			self.__thread1 = threading.Thread(target=self.__autoUpdate)
			self.__thread1.start()
			self.__shadowProcess()
		else:
			self.__init = True
			self.plotStat = True
			QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_Use96Dpi, True)
			#QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseSoftwareOpenGL, True)
			QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
			self.__win = pg.GraphicsLayoutWidget(show=True)
			self.__win.resize(850,450)
			self.__win.setWindowTitle('Live Plotter')
			#pg.setConfigOptions(antialias=True)
			self.__wiplot = self.__win.addPlot(title='SPlotter',rowspan=10) #for side stream
			#self.__wiplot = self.__win.addPlot(title='SPlotter')
			self.__wiplot.showGrid(True,True,0.3)
			self.__wiplot.addLegend()
			self.__wiplot.setLabel('bottom','Ticks','n')			
			self.logname = 'PlotterLog/SPlotter_{}.csv'.format(int(time.time()))
			self.__current_t = 0
			self.__before_t = 0
			self.__init_pos = 0
			self.__before_pos = 0
			self.__current_vel = 0
			self.__before_vel = 0
			self.__current_acc = 0
			self.__before_acc = 0
			self.__x = []
			self.__n = 0
			container, label, showStat, scale, offset, plotClass, streamLabel, plotStream = 0, 1, 2, 3, 4, 5, 6, 7
			labelValve, labelTravel, labelVel, labelAcc, labelCol, labelRes, labelP1, labelP2, labelTemp1, labelTemp2, labelBreach = [None for i in range(11)]
			self.labels = [labelValve, labelTravel, labelVel, labelAcc, labelCol, labelRes, labelP1, labelP2, labelTemp1, labelTemp2, labelBreach]
			self.colors = [(247,169,169),(255,150,25),'y','b','g','c',(100,40,250),(220,60,19),(230,20,10),(230,200,80),(255,255,200)]
			for i, key in enumerate(self.varPack.keys()): 
				self.labels[i] = self.varPack[key][label] if (self.varPack[key][scale] == 1 and not self.varPack[key][offset]) else self.varPack[key][label]+' (scaled)'
				if self.varPack[key][showStat]:
					self.varPack[key].append(self.__wiplot.plot(pen=self.colors[i], name=self.labels[i]))					
				else:
					self.varPack[key].append(None)
				if self.sideStream:
					self.varPack[key].append(self.__win.addLabel(text=f'{key}\t: ',row=i,col=1))
					self.varPack[key].append(self.__win.addLabel(text='',row=i,col=2))
			if self.staticVar:
				for var in self.staticVar: self.staticVar[var].append(self.__wiplot.plot(pen=self.staticVar[var][5], name=var))
			self.__writeLog(['tick','time',*self.varPack.keys()])
			self.timer = QtCore.QTimer()
			self.timer.timeout.connect(self.__autoUpdate)
			self.timer.start(0)
			try: QtGui.QApplication.instance().exec_()
			except: pass
			self.terminate()

	def __autoUpdate(self):
		container, label, showStat, scale, offset, plotClass, streamLabel, plotStream = 0, 1, 2, 3, 4, 5, 6, 7
		t1 = time.perf_counter()
		if self.object:
			if not self.transmitterStat:
				self.transmitterStat = True
				while self.plotStat:
					# start to add data =======================
					if self.__init:
						self.__init_t = time.perf_counter()
						self.__current_t = time.perf_counter() - self.__init_t
						self.__before_t = 0
						self.__init_pos = abs(self.object.get_encoder_position(0))
						self.__before_pos = 0
						self.__current_vel = 0
						self.__before_vel = 0
						self.__current_acc = 0
						self.__before_acc = 0
						self.__init = False
						time.sleep(0.1)
					# Movement
					self.__current_t = time.perf_counter() - self.__init_t
					self.__current_pos = abs(self.object.get_encoder_position(0))-self.__init_pos
					self.__current_vel = (self.__current_pos-self.__before_pos)/(self.__current_t-self.__before_t)
					self.__current_acc = (self.__current_vel - self.__before_vel)/(self.__current_t-self.__before_t)
					self.__before_t = self.__current_t
					self.__before_pos = self.__current_pos
					self.__before_vel = self.__current_vel
					self.__before_acc = self.__current_acc
					# Sensors
					valve = int(self.object.get_valve())
					col = self.object.read_sensor(1)
					res = self.object.read_sensor(0)
					p1 = self.object.read_sensor(6)
					p2 = self.object.read_sensor(7)
					temp1 = self.object.read_sensor(4)
					temp2 = self.object.read_sensor(5)
					breach = self.object.read_sensor(8)
					vals = [valve, self.__current_pos, self.__current_vel, self.__current_acc, col, res, p1, p2, temp1, temp2, breach]
					self.__sendValue(*vals)
					t1 = time.perf_counter()
				if self.__clean: self.default(warn=False)
		else:
			if self.plotStat:
				vals = self.__receiveValue()
				# set limit
				if len(self.varPack['pos'][0]) > self.limit:
					for var in self.varPack: del self.varPack[var][0][0]
					if self.staticVar:
						for var in self.staticVar: del self.staticVar[var][0][0]
					del self.__x[0]
				self.__x.append(self.__n)
				# ADD DATA
				for i, key in enumerate(self.varPack): 
					self.varPack[key][container].append(vals[i]*self.varPack[key][scale]+self.varPack[key][offset])
					# Side Stream
					if self.sideStream: self.varPack[key][plotStream].setText(f'{round(vals[i], 2)}')
				if self.staticVar:
					for var in self.staticVar: self.staticVar[var][0].append(self.staticVar[var][1]*self.staticVar[var][scale]+self.staticVar[var][offset])
				# start to plot
				for var in self.varPack: 
					self.varPack[var][plotClass].setData(self.__x,self.varPack[var][container]) if self.varPack[var][showStat] else None					
				if self.staticVar:
					for var in self.staticVar: self.staticVar[var][-1].setData(self.__x, self.staticVar[var][container])
				# end of plotting ======================= save to logs
				spd = round((time.perf_counter() - t1)*1000.0,1)				
				self.__writeLog([self.__n,round(time.perf_counter(),2),*vals])
				self.__wiplot.setLabel('top',f'{spd} ms/tick')
				self.__n += 1
			else:
				self.terminate()

	def terminate(self):		
		self.plotStat = False	
		self.transmitterStat = False
		self.sideStream = False
		try:
			self.timer.stop()
			self.__win.close()
		except:
			pass

	def __writeLog(self,vals):
		dataStr = ''
		with open(self.logname, 'a') as f:
			for val in vals: dataStr += str(val)+','
			f.write(dataStr+'\n')

	def readLog(self,*sensor):
		root = tk.Tk()
		fname = fd.askopenfilename(initialdir='D:/Job/2021 H1/Job 1_LLD P1000/Python Scripts/V2 Python3/DeviceScripts/PlotterLog/')
		root.destroy()
		df = pd.read_csv(fname)
		ticks = df.pop('tick')
		sns.set()
		for x, key in enumerate(df.keys()):
			if x <= 10:
				if not sensor:
					plt.plot(ticks,[float(i) for i in df[key]],label=key)
				else:
					if key in sensor:
						plt.plot(ticks, [float(i) for i in df[key]],label=key)
		plt.legend(loc='upper left')
		plt.title(fname.split('/')[-1])
		plt.show()


	def resetVariables(self):
		self.varPack = self.resetConfig('varPack')

	def addStaticChart(self,key,val,scale=1,offset=0,color=[int(i) for i in np.random.randint(50,255,3)],copyScaling=None):
		if copyScaling:
			self.staticVar[key+' (static)'] = [[], val,  True, self.varPack[copyScaling][3], self.varPack[copyScaling][4], color]
		else:
			self.staticVar[key+' (static)'] = [[], val,  True, scale, offset, color]
		self.__setConfig('staticVar',self.staticVar)

	def resetStaticChart(self):
		self.staticVar = self.resetConfig('staticVar')

	def setSensor(self,*s,**sens): # untuk set sensor dari terminal dan limit
		container, label, showStat, scale, offset = 0, 1, 2, 3, 4		
		if 'clean' in sens: 
			if sens['clean']: self.__clean = True
			else: self.__clean = False
		if self.__clean: self.default()
		if s:
			for var in self.varPack:
				if 7 in s: 
					self.varPack[var][showStat] = True
				else: 
					self.varPack[var][showStat] = True if var in s else self.varPack[var][showStat]
			if 'press' in s or 'p' in s: 
				self.varPack['p1'][showStat] = True
				self.varPack['p2'][showStat] = True
			if 'temp' in s:
				self.varPack['temp1'][showStat] = True
				self.varPack['temp2'][showStat] = True
			if 'llt' in s:
				sens['p1'] = (True,3,-2000)
				sens['p2'] = (True,3,-2000)
				sens['res'] = (True,0.4,0)
				sens['vel'] = (True,20,0)
			if 'dpc' in s:
				self.varPack['p1'][showStat] = True
				self.varPack['p2'][showStat] = True
				self.varPack['valve'][showStat] = True
		if 'limit' in sens: self.limit = sens['limit']
		if not self.transmitterStat:
			if 'side' in sens: self.sideStream = True if sens['side'] else False
		if sens:
			for sensor in sens:
				if sensor in self.varPack:
					if type(sens[sensor]) == tuple:
						self.varPack[sensor][showStat], self.varPack[sensor][scale], self.varPack[sensor][offset] = sens[sensor]
						print(sens[sensor])
					else:
						self.varPack[sensor][showStat] = sens[sensor]					
					if self.varPack[sensor][showStat]: print(sensor+" plot enabled")
		self.__setConfig('varPack',self.varPack)

	def setScale(self,**vars): # untuk scaling chart
		container, label, showStat, scale = 0, 1, 2, 3
		if vars:
			for var in vars:
				if var in self.varPack:
					self.varPack[var][scale] = vars[var]
					print(var+"'s scale:", vars[var])
			self.__setConfig('varPack',self.varPack)
		else:
			print('No Scale is Changed')

	def setOffset(self,**vars): # untuk offsetting chart
		container, label, showStat, offset = 0, 1, 2, 4
		if vars:
			for var in vars:
				if var in self.varPack:
					self.varPack[var][offset] = vars[var]
					print(var+"'s offset:", vars[var])
			self.__setConfig('varPack',self.varPack)
		else:
			print('No Offset is Changed')

	def checkVariables(self):
		print('SPlotter Variables')
		container, label, showStat, scale, offset = 0, 1, 2, 3, 4
		for var in self.varPack:
			print(var,'\t:', f' Plot: {self.varPack[var][showStat]} | Scale: {self.varPack[var][scale]} | Offset: {self.varPack[var][offset]}')

	@staticmethod # Dont touch this, this function to generate the new config for new pc
	def generateConfig(self):
		if 'PlotterLog' not in os.listdir(os.getcwd()): 
			os.system("mkdir PlotterLog")
		if "splotterConfig" not in os.listdir(os.getcwd()):
			os.system("mkdir splotterConfig")
			os.chdir("splotterConfig")
			f = open('plotStat.flo','w'); f.write('1'); f.close()
			f = open('data.flo','w'); f.write('0,0,0,0,0,0,0'); f.close()
			os.chdir('..')
		config ={"varPack":{
					"valve"	: [[], "valve (OFF: 930 | ON: 935)", false, 5, 930],
					"pos"	: [[], "pos", false, 1, 0],
					"vel"	: [[], "vel", false, 1, 0],
					"acc"	: [[], "acc", false, 1, 0],
					"col"	: [[], "col", false, 1, 0],
					"res"	: [[], "res", false, 1, 0],
					"p1"	: [[], "p1", false, 1, 0],
					"p2"	: [[], "p2", false, 1, 0],
					"temp1"	: [[], "temp1", false, 1, 0],
					"temp2"	: [[], "temp2", false, 1, 0],
					"breach": [[], "breach", false, 1, 0]},
				"staticVar":{},
				"limit":500 }
		with open('splotterConfig/originalConfig.json','w') as f1: json.dump(config, f1)
		with open('splotterConfig/Config.json','w') as f2: json.dump(config, f2)


if __name__ == '__main__':
	ghost = SPlotter(None)
	ghost.liveplot()