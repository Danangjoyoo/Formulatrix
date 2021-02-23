######################### LIBRARY CHECKER #########################
#Installing required modules/libraries to run FLO V2 Single Channel
import LibraryInstaller

######################### FOLDER CHECKING #########################
#Adding required folder if there aren't exist yet
import os
if 'PlotterLog' not in os.listdir(os.getcwd()): 
	os.system("mkdir PlotterLog")
	os.chdir("PlotterLog")
	if "conf" not in os.listdir(os.getcwd()):
		os.system("mkdir conf")
	os.chdir('..')
if 'Level' not in os.listdir(os.getcwd()): os.system("mkdir Level")
if 'FirmwareLog' not in os.listdir(os.getcwd()): os.system("mkdir FirmwareLog")


######################### VERSION UPDATER #########################
#Keep the scripts UP-TO-DATE with the developer
from local_updater import *

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
** Under Development **
"""

from FLOPlotter2 import *