import numpy as np
import time, threading, sys, os, json
import matplotlib.pyplot as plt
from visualize import *
import pandas as pd
import multiprocessing as mp
from matplotlib.animation import FuncAnimation
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg

"""
Shadow or ghost... it's unreachable...

"""
container, label, showStat, scale, offset, plotClass = 0, 1, 2, 3, 4, 5
class SPlotter():
	#============================= LIVE PLOTTER USING QT ===============================
	# SetUp
	def __init__(self, obj):
		self.object = obj
		self.init = False
		self.__plotStat = False
		self.init_t = time.time()
		self.avgTime = []
		self.x = []
		self.thread = None
		self.func = None
		self.funcReturn = None
		self.args = None
		self.quit = True
		self.win = None
		self.current_t = 0
		self.before_t = 0
		self.init_travel = 0
		self.before_travel = 0
		self.current_vel = 0
		self.before_vel = 0
		self.current_acc = 0
		self.before_acc = 0
		config = self.getConfig()
		self.staticVar = config['staticVar']
		self.varPack = config['varPack']
		self.__limit = config['limit']
		self.logname = None
		self.n = 0
		self.timer = None
		self.lastVals = np.zeros(8)

	# Multiprocessing Communication
	def getConfig(self):
		with open('splotterConfig/config.json') as config:
			x = json.load(config); config.close()
			return x

	def __setConfig(self,key,dic):
		recentConf = self.getConfig()
		with open('splotterConfig/config.json', 'w') as config:
			recentConf[key] = dic
			json.dump(recentConf, config); config.close()

	def resetConfig(self,key=None):
		with open('splotterConfig/originalConfig.json') as origin:
			recentConf = json.load(origin); origin.close()
			if key:
				return recentConf[key]
			else:
				self.varPack = recentConf['varPack']
				self.__setConfig('varPack',self.varPack)
				self.staticVar = recentConf['staticVar']
				self.__setConfig('staticVar',self.staticVar)
				self.limit = recentConf['limit']
				printg("[SPlotter] All config changed to default..")

	def default(self):
		self.resetConfig()

	@property
	def limit(self):
		return self.getLimit

	@limit.setter
	def limit(self, val):
		self.__limit = int(val)
		self.__setConfig('limit', self.__limit)

	@limit.getter
	def getLimit(self):
		return self.__limit

	@property
	def plotStat(self):
		return self.getplotStat

	@plotStat.setter
	def plotStat(self, state):
		self.__plotStat = state
		try:	
			with open('splotterConfig/plotStat.flo','w') as f:
				f.write(str(int(bool(state))))
		except: pass

	@plotStat.getter
	def getplotStat(self):
		for i in range(10):
			try:
				with open('splotterConfig/plotStat.flo','r') as f:
					stat = bool(int(f.read()))
					self.__plotStat = True if stat else False
					break
			except: pass
		return self.__plotStat

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
			if len(data) == 8:
				self.lastVals = [float(i) for i in data]
		except:
			pass
		return self.lastVals

	# Plotting
	def run(self,*args,**kargs): #function, param1, param2, dll
		if self.object:
			if args:
				newArgs = list(args)
				self.func = newArgs.pop(0)
				self.args = tuple(newArgs) if len(args) > 1 else None                
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
		self.funcReturn = self.func(*self.args) if self.args else self.func()
		time.sleep(2)
		if self.quit: 
			self.terminate()

	def __shadowProcess(self): # Conventional Multiprocessing, you cant grab anything from the shadow xD
		printb("Shadow Plotter initialized..")
		def shade(): os.system(f"python3 {__name__}.py")
		shadowThread = threading.Thread(target=shade)
		shadowThread.start()

	def getReturn(self):
		return self.funcReturn

	def liveplot(self,*s,**show):
		if self.object:
			self.plotStat = True
			self.setSensor(*s,**show)
			self.thread1 = threading.Thread(target=self.__autoUpdate)
			self.thread1.start()
			self.__shadowProcess()
		else:
			self.init = True
			self.plotStat = True
			self.win = pg.GraphicsLayoutWidget(show=True)
			self.win.resize(1000,600)
			self.win.setWindowTitle('Live Plotter')
			self.wiplot = self.win.addPlot(title='SPlotter')
			self.wiplot.addLegend()
			self.wiplot.setLabel('bottom','Ticks','n')
			self.logname = 'PlotterLog/SPlotter_{}.csv'.format(int(time.time()))
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
			labelValve, labelTravel, labelVel, labelAcc, labelCol, labelRes, labelP1, labelP2 = [None for i in range(8)]
			self.labels = [labelValve, labelTravel, labelVel, labelAcc, labelCol, labelRes, labelP1, labelP2]
			self.colors = [(247,169,169),(255,150,25),'y','b','g','c',(100,40,250),(220,60,19)]
			for i, key in enumerate(self.varPack.keys()): 
				self.labels[i] = self.varPack[key][label] if (self.varPack[key][scale] == 1 and not self.varPack[key][offset]) else self.varPack[key][label]+' (scaled)'
				if self.varPack[key][showStat]:
					self.varPack[key].append(self.wiplot.plot(pen=self.colors[i], name=self.labels[i]))
			if self.staticVar:
				for var in self.staticVar: self.staticVar[var].append(self.wiplot.plot(pen=self.staticVar[var][5], name=var))
			self.__writeLog(['tick','time',*self.varPack.keys()])
			self.timer = QtCore.QTimer()
			self.timer.timeout.connect(self.__autoUpdate)
			self.timer.start(0)
			QtGui.QApplication.instance().exec_()
			self.terminate()
			for key in self.varPack.keys():
				self.varPack[key][0] = []
				if len(self.varPack[key])-1 == plotClass:
					self.varPack[key].pop(plotClass)
			if self.staticVar:
				for var in self.staticVar: 
					self.staticVar[var][0] = []
					self.staticVar[var].pop(-1)

	def __autoUpdate(self):
		container, label, showStat, scale, offset, plotClass = 0, 1, 2, 3, 4, 5         
		t1 = time.perf_counter()
		if self.object:
			while self.plotStat:
				# start to add data =======================
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
				valve = int(self.object.get_valve())
				vals = [valve, self.current_travel, self.current_vel, self.current_acc, col, res, p1, p2]
				self.__sendValue(*vals)
				t1 = time.perf_counter()
		else:
			if self.plotStat:
				vals = self.__receiveValue()
				# set limit
				if len(self.varPack['travel'][0]) > self.limit:
					for var in self.varPack: self.varPack[var][0].pop(0)
					if self.staticVar:
						for var in self.staticVar: self.staticVar[var][0].pop(0)
				else:
					self.x = [i+1 for i in range(len(self.varPack['travel'][0])+1)]
				# ADD DATA
				for i, key in enumerate(self.varPack): self.varPack[key][0].append(vals[i]*self.varPack[key][scale]+self.varPack[key][offset])
				if self.staticVar:
					for var in self.staticVar: self.staticVar[var][0].append(self.staticVar[var][1]*self.staticVar[var][scale]+self.staticVar[var][offset])
				# start to plot
				for var in self.varPack: self.varPack[var][plotClass].setData(self.x,self.varPack[var][container]) if self.varPack[var][showStat] else None
				if self.staticVar:
					for var in self.staticVar: self.staticVar[var][-1].setData(self.x, self.staticVar[var][container])
				# end of plotting ======================= save to logs
				self.n += 1
				spd = round((time.perf_counter() - t1)*1000.0,1)
				self.__writeLog([self.n,round(time.perf_counter(),2),*vals])
				self.wiplot.setLabel('top',f'{spd} ms/tick')
			else:
				self.terminate()

	def terminate(self):		
		self.plotStat = False		
		try:
			self.timer.stop()
			self.win.close()
		except:
			pass

	def __writeLog(self,vals):
		dataStr = ''
		with open(self.logname, 'a') as f:
			for val in vals: dataStr += str(val)+','
			f.write(dataStr+'\n')

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
		if 'limit' in sens: self.limit = sens['limit']
		if sens:
			for sensor in sens:
				if sensor in self.varPack:
					if type(sens[sensor]) == tuple:
						self.varPack[sensor][showStat], self.varPack[sensor][scale], self.varPack[sensor][offset] = sens[sensor]
					else:
						self.varPack[sensor][showStat] = sens[sensor]					
					if self.varPack[sensor][showStat]: print(sensor+" plot enabled")
		if s:
			for var in self.varPack:
				if 7 in s: 
					self.varPack[var][showStat] = True
				else: 
					self.varPack[var][showStat] = True if var in s else self.varPack[var][showStat]
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

	@staticmethod # Dont touch this, this function to generate the new config on folder
	def generateConfig(self):
		if 'PlotterLog' not in os.listdir(os.getcwd()): 
			os.system("mkdir PlotterLog")
		if "splotterConfig" not in os.listdir(os.getcwd()):
			os.system("mkdir splotterConfig")
			os.chdir("splotterConfig")
			f = open('plotStat.flo','w'); f.write('1'); f.close()
			f = open('data.flo','w'); f.write('0,0,0,0,0,0,0'); f.close()
			os.chdir('..')
		config = {"varPack":{
						"valve": [[], "valve (OFF: 930 | ON: 935)", false, 5, 930],
						"travel": [[], "travel", false, 1, 0],
						"vel": [[], "vel", false, 1, 0],
						"acc": [[], "acc", false, 1, 0],
						"col": [[], "col", false, 1, 0],
						"res": [[], "res", false, 1, 0],
						"p1": [[], "p1", false, 1, 0],
						"p2": [[], "p2", false, 1, 0]},
					"staticVar":{},
					"limit":250}
		with open('splotterConfig/originalConfig.json','w') as f1: json.dump(config, f1)
		with open('splotterConfig/Config.json','w') as f2: json.dump(config, f2)


if __name__ == '__main__':
	ghost = SPlotter(None)
	ghost.liveplot()