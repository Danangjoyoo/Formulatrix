import sys
import clr
import imp
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
#imp.reload(sys.modules[" Formulatrix.Core.Protocol"])
def deletes():
    del sys.path[0]
    del sys.path[1]
    del sys.modules['Formulatrix.Core.Protocol']
    print('module deleted')
comNum = 0#zul 1

