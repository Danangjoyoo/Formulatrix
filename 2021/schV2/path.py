import sys, os, clr, importlib, time
import serial.tools.list_ports
from visualize import *
sys.path.append(r"..\Include")
sys.path.append(r"..\FmlxDeviceUtils")
clr.AddReference("Formulatrix.Core.Protocol")


from Formulatrix.Core.Protocol import IFmlxDriver
from Formulatrix.Core.Protocol.Serial.Ftdi.Win import FtdiFmlxDriver, FtdiFmlxDriverProvider
from Formulatrix.Core.Protocol.Can.KVaser.Win import KvaserFmlxDriver
from FmlxDevice import FmlxDevice

#FVASER
from Formulatrix.Core.Protocol.SLCan.Win  import SlcanFlmxDriver# SlcanFlmxDriver as sl

print("Path imported..")
print("Connecting to SingleCH V2..")

class Device(FmlxDevice):
	device_address = {
			'channel'	: 30,
			'regulator'	: 11,
			'deck'		: 1 }

	def __init__(self,deviceObject,finder=False):
		if str.lower(deviceObject) in Device.device_address:
			self.__com = 1#zul 1
			self.deviceObject = str.lower(deviceObject)
			self.address = Device.device_address[self.deviceObject]
			self.__checkDevice()
			self.__createConnection()
		else:
			printr(f"DEVICE '{deviceObject}' IS NOT REGISTERED!")
			printr(f'Registered DeviceS: {list(Device.device_address.keys())}')
			printr(f'Check on {__name__}.py at {os.getcwd()}')

	def __checkDevice(self):
		if self.deviceObject == 'channel' or self.deviceObject == 'ch':
			self.path_obj = r"../DeviceOpfuncs/FloV2.yaml"
		elif self.deviceObject == 'regulator' or self.deviceObject == 'reg':
			self.path_obj = r"../DeviceOpfuncs/PressureRegulatorAbs.yaml"
		elif self.deviceObject == 'wambo':
			self.path_obj = r"../DeviceOpfuncs/wambo_base.yaml"
		elif self.deviceObject == 'deck':
			self.path_obj = r"../DeviceOpfuncs/FloDeck.yaml"
		else:
			self.path_obj = None

	def __createConnection(self):
		if self.path_obj:
			comPorts = list(serial.tools.list_ports.comports())
			serial_port = str(comPorts[self.__com])[0:5]
			drv = SlcanFlmxDriver(self.address,serial_port)
			super(Device, self).__init__(drv, self.address, self.path_obj)			
			printg(f"Connecting {self.deviceObject} to address {self.address}..",end='\r')
			self.connect()
			printg(f"Connecting {self.deviceObject} to address {self.address}.. Connected : {self.deviceObject}")
		else:
			printr(f"No device named: {self.deviceObject}")