import sys
import clr
import imp
import serial.tools.list_ports
sys.path.append(r"..\Include")
sys.path.append(r"..\FmlxDeviceUtils")
clr.AddReference("Formulatrix.Core.Protocol")


from Formulatrix.Core.Protocol import IFmlxDriver
from Formulatrix.Core.Protocol.Serial.Ftdi.Win import FtdiFmlxDriver, FtdiFmlxDriverProvider
from Formulatrix.Core.Protocol.Can.KVaser.Win import KvaserFmlxDriver
from FmlxDevice import FmlxDevice

#FVASER
from Formulatrix.Core.Protocol.SLCan.Win  import SlcanFlmxDriver# SlcanFlmxDriver as sl

path_reg = r"../DeviceOpfuncs/PressureRegulatorAbs.yaml"
path_ch = r"../DeviceOpfuncs/FloV2.yaml"
path_wam = r"../DeviceOpfuncs/wambo_base.yaml"
path_deck = r"../DeviceOpfuncs/FloDeck.yaml"

print("path imported")
def deletes():
    del sys.path[0]
    del sys.path[1]
    del sys.modules['Formulatrix.Core.Protocol']
    print('module deleted')
comNum = 1#zul 1

class Device(FmlxDevice):
	device_list = ['channel','regulator','deck','wambo']

	def __init__(self,address,deviceObject):
		self.__connectStat = False
		self.__checkDevice(deviceObject)
		if self.path_obj:
			comPorts = list(serial.tools.list_ports.comports())
			serial_port = str(comPorts[comNum])[0:5]
			drv = SlcanFlmxDriver(address,serial_port)
			FmlxDevice.__init__(self, drv, address, self.path_obj)			
			self.connect()	

	def __checkDevice(self,deviceObject):
		if deviceObject == 'channel' or deviceObject == 'ch':
			self.path_obj = r"../DeviceOpfuncs/FloV2.yaml"
		elif deviceObject == 'regulator' or deviceObject == 'reg':
			self.path_obj = r"../DeviceOpfuncs/PressureRegulatorAbs.yaml"
		elif deviceObject == 'wambo':
			self.path_obj = r"../DeviceOpfuncs/wambo_base.yaml"
		elif deviceObject == 'deck':
			self.path_obj = r"../DeviceOpfuncs/FloDeck.yaml"
		else:
			self.path_obj = None

	@property
	def connectStat(self):
		return self.getConnectStat
	@connectStat.setter
	def connectStat(self,state):
		with open('connectStat.flo','w') as f:
			f.write(str(int(bool(state))))		
	@connectStat.getter
	def getConnectStat(Self):
		with open('connectStat.flo','r') as f:
			self.__connectStat = bool(int(str(f.read())))
		return self.__connectStat