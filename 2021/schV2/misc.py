######################### LIBRARY CHECKER #########################
#Installing required modules/libraries (dependencies) to run FLO V2 Single Channel
#import 

######################### THREAD WORKER #########################
from worker import *

######################### FOLDER CHECKING #########################
#Adding required folder if there aren't exist yet
import os
if 'Level' not in os.listdir(os.getcwd()): os.system("mkdir Level")
if 'FirmwareLog' not in os.listdir(os.getcwd()): os.system("mkdir FirmwareLog")


######################### VERSION UPDATER #########################
#Keep the scripts UP-TO-DATE with the developer
try: from local_updater import *
except: pass


######################### VISUALIZATION #########################
from visualize import *

######################### PLOTTER #########################
from pyqtgraph import QtGui, QtCore
import numpy as np
import time, threading, sys, os
import matplotlib.pyplot as plt
import pyqtgraph as pg
import pandas as pd

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

SPlotter --> Safe PyQt Plotter (Manual Multiprocessing)
+ High Speed (5-30 ms/tick)
+ Run in different GIL (multiprocess)
- Manual SetUp and reset
"""

#from schPlotter2 import *
from SPlotter import *


######################### PID TUNER #########################
class Tuner():
	def __init__(self):
		self.execFunc = None
		self.targetGetter = None
		self.runTargetGetter = False
		self.targetArgs = None
		self.targetVal = None
		self.targetData = {
			'data':[],
			'error':[],
			'peakIdx':[],
			'peakCount':0,
			'amplitudes':[],
			'noise':0,
		}
		self.refVal = None
		self.tunerThread = None
		self.p, self.i, self.d = 0,0,0
		self.pidConfig = [None, None, None]

	def setExecution(self,**kargs):
		if 'target' in kargs and not 'args' in kargs:
			self.execFunc = kargs['target']
		elif 'target' in kargs and 'args' in kargs:
			func = kargs['target']
			args = kargs['args']
			self.execFunc = lambda: func(*args)

	def setTarget(self,**kargs):
		if 'target' in kargs: self.targetGetter = kargs['target']
		if 'args' in kargs: self.targetArgs = kargs['args']
		if 'noise' in kargs: self.targetData['noise'] = kargs['noise']

	def setRef(self,ref):
		self.refVal = ref

	def setTargetPIDconfig(self,**kargs):
		if 'kp' in kargs: self.pidConfig[0] = kargs['kp']
		if 'ki' in kargs: self.pidConfig[1] = kargs['ki']
		if 'kd' in kargs: self.pidConfig[2] = kargs['kd']

	def run(self):
		self.runTargetGetter = True
		self.tunerThread = threading.Thread(target=self.getTargetData)
		self.tunerThread.start()

	def getTargetData(self):
		while self.runTargetGetter:
			self.targetData['data'].append(self.targetGetter)
			self.targetData['error'].append(self.ref - self.targetData['data'][len(self.targetData['data']-1)])

	def calculate(self):
		noise = self.targetData['noise']
		for i, val in enumerate(self.targetData['data']):
			if i > 0:
				if self.targetData['peakCount'] % 2 == 0:
					if (val[i] + noise) < (val[i-1] + noise):
						self.targetData['peakCount'] += 1
						self.targetData['peakIdx'].append(i-1)
				elif self.targetData['peakCount'] % 2 == 1:
					if (val[i] + noise) > (val[i-1] + noise):
						self.targetData['peakCount'] += 1
						self.targetData['peakIdx'].append(i-1)
		devPacks = []
		idx = self.targetData['peakIdx']
		for i in range(1, self.targetData['peakCount']+1):
			devPacks.append(self.targetData['error'][idx[i-1]:idx[i]])