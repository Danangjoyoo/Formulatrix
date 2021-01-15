from path import*
import time
from numpy import corrcoef
import threading
from subprocess import call
from winsound import Beep
from math import pi
import imp
import numpy as np

p = None
driver = None
address = None
inputadd = 36
PIPETTE_ADDRESS = inputadd
stem_eng = 100

def connect_to(sufic,add,path,flavor='1'):
	global address
	global driver
	address = add

	if flavor=='1':
		import serial.tools.list_ports   # import serial module
		comPorts = list(serial.tools.list_ports.comports())    # get list of all devices connected through serial port
		for i in sorted(comPorts):
			print i
		if len(comPorts)==0:
			exit("No COM port found!, abort...")
		else:
			for x,i in enumerate(comPorts[comNum:]):
				serial_port = str(i)[0:5]
				print serial_port
				#driver=SlcanFlmxDriver().clear()
				driver=SlcanFlmxDriver(address,serial_port)
				globals()[sufic] = FmlxDevice(driver, address, path)
				try :
					#p.connect()
					globals()[sufic].connect()
					print "connecting to address %s"% address
					#print p.get_app_name()

					print globals()[sufic].get_app_name()

				except:
					driver = None
					print "fail connect to address %s"% address
					print "try again"

				else:
					print 'Connected succesfully'
					break

	elif flavor=='2':
		driver = KvaserFmlxDriver(address)	
		globals()[sufic] = FmlxDevice(driver, address, path)
		try :
			globals()[sufic].connect()
			
			print "connecting to address %s"% address
			#print p.get_app_name()
			print globals()[sufic].get_app_name()

		except:
			print "fail connect to address %s"% address
			print "try another address"




connect_to('p',inputadd,path_ch)


CAL_ASP = None
CAL_DSP = None

CAL_OFF_ASP = 2e-06
CAL_OFF_DSP = -3.518723588058492e-07
DP_HIGH_THRES = 1.0
DP_LOW_THRES = 0.5
EXTRA_OFF_ASP = -0.019929999485611916
EXTRA_OFF_DSP = 0.04100000113248825
EXTRA_SCALE_ASP = 0.017550000920891762
EXTRA_SCALE_DSP = 0.018272100016474724
SLOPE_THRES = 9.999999747378752e-05
SENSOR_ID = 1

#averaging variable
AverageP1 = 0.0
AverageP2 = 0.0
AverageT1 = 0.0
AverageT2 = 0.0
Min_p1 = 0.0
Max_p1 = 0.0
Min_p2 = 0.0
Max_p2 = 0.0
Average_done = False

# tare pressure variable
Tare_done = False
ATM_pressure = 930.0
Dp_Offset = 0.0
Temp_P1 = 30.0
Temp_P2 = 30.0
# calibrate variable
Calibrate_done = False
Press_P1 = 930.0
Press_P2 = 930.0
Press_Dp = 0.0
IsFound = False
# count volume variable
Count_volume_done = False
Total_time_ms = 0.0
Sensed_vol = 0.0
# pipetting variable
Pipetting_done = False
Total_time_ms = 0
Alc_time_ms = 0
Sampling_vol = 0
Total_sampling = 0
Last_flow = 0.0
P1_off = 0.0
P2_off = 0.0
Res_vacuum = 0.0
Selected_p2 = False
Tau_time = 0
Pressure_peak = 0.0
Avg_window = 1
Slope_window = 1
Threshold = 0.0
Sensed_vol = 0.0

Target_flow_rel= [630,-630]
Target_flow = [0,0]
Pipetting_error = False
List_aspirateX=[]
List_aspirateY=[]
List_dispenseX=[]
List_dispenseY=[]

last_vol = None
#----- LOGGER ----------------------
class MotorMask:
	Nothing = 0
	CurrentA = 1
	CurrentB = 2
	CurrentError = 4
	dlcControlOut = 8
	PwmA = 16
	dlcPwmB = 32
	PosCommand = 64
	PosError = 128
	PosActual = 256
	I2tAcc = 512
	I2tLimit = 1024

class SensorMask:
	Nothing = 0
	ZMotorCurrentSense = 1
	PressureSensor1 = 2
	PressureSensor2 = 4
	Collision = 8
	LiquidLevelSensor = 16
	Valve = 32
	Processing = 64
	Flow = 128
	ControlOut = 256
	Temp1 = 512
	Temp2 = 1024
	TargetFlow = 2048
	CalcVolume = 4096
	ActualFlow = 8192

class AbortID:
	NormalAbortZ = 0
	HardZ = 1
	WithReleaseZ = 2
	EstopOut = 3
	TouchOffOut = 4
	ValvePV = 5
	ValveClose = 6
	PipAbortBlow = 7

class InputAbort:
	PressureSensor1 = 0
	PressureSensor2 = 1
	CollisionEstop = 2
	CollisionTouch = 3
	WLLDs = 4
	EStop = 5
	Touchoff = 6
	CurrentMotorZ = 7
	LiquidLevelSensor = 8
	LiquidBreachDetection = 9

class SensorID:
	Collision = 0
	DLLT = 1
	Pressure1 = 2
	Pressure2 = 3




log_codes_ZM = { 0: "None", 1: "CurrentA_ZM", 2: "CurrentB_ZM", 4: "CurrentError_ZM", 8: "ControlOut_ZM", 16: "PwmA_ZM", 32: "PwmB_ZM", 64: "PosCommand_ZM", 128: "PosError_ZM", 256: "PosActual_ZM", 512: "I2tAcc_ZM", 1024: "I2tAcc_ZM" }
log_codes_ZM_scale = { 0: 0.0, 1: 0.001, 2: 0.0, 4: 0.0, 8: 0.0, 16: 0.1, 32: 0.0, 64: 1.0/stem_eng, 128: 1.0/stem_eng, 256: 1.0/stem_eng, 512: 0.01, 1024: 0.01 }
log_codes_ZM_offset = { 0: 0.0, 1: -5.0, 2: 0.0, 4: 0.0, 8: 0.0, 16: -32768.0, 32: 0.0, 64: -32768.0, 128: -32768.0, 256: -32768.0, 512: 0.0, 1024: 0.0 }

log_codes_sens = { 0: "None", 1:"ZMotorCurrentSense", 2: "PressureSensor1", 4: "PressureSensor2", 8: "Collision", 16: "LiquidLevelSensor", 32: "Valve", 64: "Processing", 128: "Flow", 256: "ControlOut", 512: "Temp1", 1024: "Temp2", 2048: "TargetFlow", 4096: "CalcVolume", 8192: "ActualFlow", 16384: "Triangle"}
log_codes_sens_scale = { 0: 0.0, 1: 0.002685546875, 2: 0.1, 4: 0.1, 8: 1.0, 16: 1.0, 32: 0.01, 64: 0.01, 128: 0.01, 256: 0.1, 512: 0.01, 1024: 0.01, 2048: 0.01, 4096: 0.01, 8192: 0.01, 16384: 1.0}
log_codes_sens_offset = { 0: 0.0, 1: -2048, 2: 0.0, 4: 0.0, 8: 0.0, 16: 0.0, 32: 0.0, 64: 0.0, 128: -32768.0, 256: -32768.0, 512: 0.0, 1024: 0.0, 2048:-32768.0, 4096:-32768.0, 8192: -32768.0, 16384: 1.0}



def chunks(l, n):
	n = max(1, n)
	return [l[i:i + n] for i in range(0, len(l), n)]

table_pos = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 210, 220, 230, 240, 250, 260, 270, 280, 290, 300, 310, 320, 330, 340, 350, 360, 370, 380, 390, 400, 410, 420, 430, 440, 450, 460, 470, 480, 490, 500, 510, 520, 530, 540, 550, 560, 570, 580, 590, 600, 610, 620, 630, 640, 650, 660, 670, 680, 690, 700, 710, 720, 730, 740, 750, 760, 770, 780, 790, 800, 810, 820, 830, 840, 850, 860, 870, 880, 890, 900, 910, 920, 930, 940, 950, 960, 970, 980, 990, 1000, 1010, 1020, 1030, 1040, 1050, 1060, 1070, 1080, 1090, 1100, 1110, 1120, 1130, 1140, 1150, 1160, 1170, 1180, 1190, 1200, 1210, 1220, 1230, 1240, 1250, 1260, 1270, 1280, 1290, 1300, 1310, 1320, 1330, 1340, 1350, 1360, 1370, 1380, 1390, 1400, 1410, 1420, 1430, 1440, 1450, 1460, 1470, 1480, 1490, 1500, 1510, 1520, 1530, 1540, 1550, 1560, 1570, 1580, 1590, 1600, 1610, 1620, 1630, 1640, 1650, 1660, 1670, 1680, 1690, 1700, 1710, 1720, 1730, 1740, 1750, 1760, 1770, 1780, 1790, 1800, 1810, 1820, 1830, 1840, 1850, 1860, 1870, 1880, 1890, 1900, 1910, 1920, 1930, 1940, 1950, 1960, 1970, 1980, 1990, 2000]

thread_run = True

def chunks(l, n):
	n = max(1, n)
	return [l[i:i + n] for i in range(0, len(l), n)]

def start_logger(motorm=0,sensorm=6):
	global thread_run
	thread_run = True
	thread1 = threading.Thread(name='logger 1', target=thread_logger, args=(motorm,sensorm))
	thread1.start()

def stop_logger():
	global thread_run
	p.stop_log()
	thread_run = False
lastline = None
loggername = None
def thread_logger(motorm=0,sensorm=6):
	global thread_run
	global lastline
	global loggername
	scale = []
	offset = []
	#p.set_log_items(0,SensorMask.PressureSensor1 + SensorMask.PressureSensor2)
	#p.set_log_items(0,SensorMask.Valve + SensorMask.Processing + SensorMask.Flow + SensorMask.ControlOut)
	#p.set_log_items(0,SensorMask.PressureSensor1+ SensorMask.PressureSensor2)
	p.set_log_items(motorm,sensorm)
	#p.set_log_items(0,SensorMask.PressureSensor1)
	p.start_log()
	t = time.time()
	file_name = 'data_log_' + str(PIPETTE_ADDRESS) + '_' + time.strftime('%Y%m%d%H%M%S', time.localtime(t)) + '.csv'
	loggername = file_name
	with open(file_name, 'w') as f:
		header = "Tick, "
		sum = 0
		items = p.get_log_items()['motorZ_mask']
		for x in range(0, 15):
			if ((1 << x) & items) != 0:
				header += log_codes_ZM[1 << x] + ", "
				sum = sum + 1
				scale.append(log_codes_ZM_scale[1 << x])
				offset.append(log_codes_ZM_offset[1 << x])
		len_motor_Z = sum
		items = p.get_log_items()['sensors_mask']
		for x in range(0, 15):
			if ((1 << x) & items) != 0:
				header += log_codes_sens[1 << x] + ", "
				sum = sum + 1
				scale.append(log_codes_sens_scale[1 << x])
				offset.append(log_codes_sens_offset[1 << x])
		all_data = []
		header += "\n"
		f.write(header)
		while thread_run:
			get_data = p.read_log_stream_data()['data']
			all_data += get_data
			#time.sleep(0.05)
		while(1):
			get_data = p.read_log_stream_data()['data']
			all_data += get_data
			if len(get_data) == 0:
				break
			#time.sleep(0.05)
		data = chunks(all_data, sum)
		data_length = len(data)
		print data_length
		lastline=[]
		for i in range(data_length):
			line = str(i) + ","
			for j in range(len(data[i])):
				line += str( (data[i][j] + offset[j]) *  scale[j]) + ", "
				datas = (data[i][j] + offset[j]) *  scale[j]
				lastline.append(datas)
			line += "\n"
			f.write(line)
		f.close()
	call(["..\Include\log_plot.exe", file_name])

#------- End Logger ---------------

# =========================================== EVENT =========================================================================================
def handle_move_done(motor_id,status,position):
	global move_done
	#print "Move Done:id=" + str(motor_id) + ", Status=" + str(status) + ", position=" + str(position)
	if(motor_id == 0):
		move_done = True

def handle_average_done(pressure1,pressure2,temp1,temp2,min_P1, max_P1, min_P2, max_P2):
	global AverageP1
	global AverageP2
	global AverageT1
	global AverageT2
	global Average_done
	global Min_p1
	global Max_p1
	global Min_p2
	global Max_p2
	AverageP1 = pressure1
	AverageP2 = pressure2
	AverageT1 = temp1
	AverageT2 = temp2
	Min_p1 = min_P1
	Max_p1 = max_P1
	Min_p2 = min_P2
	Max_p2 = max_P2
	#print "Averaging Done:"
	#print "	P1 = " + str(AverageP1)
	#print "	P2 = " + str(AverageP2)
	#print "	T1 = " + str(AverageT1)
	#print "	T2 = " + str(AverageT2)
	#print "	Min P1 = " + str(Min_p1)
	#print "	Max P1 = " + str(Max_p1)
	#print "	Min P2 = " + str(Min_p2)
	#print "	Max P2 = " + str(Max_p2)
	Average_done = True
tare_done_req = True
def handle_tare_done(atm_pressure,dp_offset,temp1,temp2,cal_asp,cal_dsp):
	global ATM_pressure
	global Dp_Offset
	global Temp_P1
	global Temp_P2
	global Tare_done
	global CAL_ASP
	global CAL_DSP



	ATM_pressure = atm_pressure
	Dp_Offset = dp_offset
	Temp_P1 = temp1
	Temp_P2 = temp2
	CAL_ASP = cal_asp
	CAL_DSP = cal_dsp
	if tare_done_req:
		print "Tare Done:"
		print "	ATM=" + str(atm_pressure)
		print "	dp_offset=" + str(Dp_Offset)
		print "	temp1=" + str(Temp_P1)
		print "	temp2=" + str(Temp_P2)
		print "	cal_asp=" + str(cal_asp)
		print "	cal_dsp=" + str(cal_dsp)
		global Target_flow
	else:
		print '*** evt: Tare done--'
	if atm_pressure <940 and atm_pressure>925:
		Target_flow[0] = Target_flow_rel[0] + atm_pressure
		Target_flow[1] = Target_flow_rel[1] + atm_pressure
		#print Target_flow
	Tare_done = True

def handle_calibrate_finish(is_found,press1,press2,dp):
	global Press_P1
	global Press_P2
	global Press_Dp
	global Calibrate_done
	global IsFound
	global Temp_P1
	global Temp_P2
	IsFound = is_found
	if is_found == 1:
		Press_P1 = press1
		Press_P2 = press2
		Press_Dp = dp

		print "Calibrate finish:"
		print "	P1 = " + str(Press_P1)
		print "	P2 = " + str(Press_P2)
		print "	dp = " + str(Press_Dp)
		print "	T1 = " + str(Temp_P1)
		print "	T1 = " + str(Temp_P2)
	else:
		print "calibrate fail"
	Calibrate_done = True

def handle_vol_count_finish(total_time_ms, sens_vol):
	global Total_time_ms
	global Sensed_vol
	global Count_volume_done
	Total_time_ms = total_time_ms
	Sensed_vol= sens_vol
	print "Volume Count finish:"
	print "	Total Time = " + str(Total_time_ms)
	print "	Sens Vol = " + str(Sensed_vol)
	Count_volume_done = True
pipetting_done_req=True
def handle_pipetting_done(total_time_ms, alc_time_ms, sampling_vol, total_sampling, last_flow, p1_off, p2_off, res_vacuum, selected_p2, tau_time, pressure_peak, avg_window, slope_window, threshold,sens_volume):
	global Total_time_ms
	global Alc_time_ms
	global Sampling_vol
	global Total_sampling
	global Last_flow
	global P1_off
	global P2_off
	global Res_vacuum
	global Pipetting_done
	global Selected_p2
	global Tau_time
	global Pressure_peak
	global Avg_window
	global Slope_window
	global Threshold
	global Sensed_vol
	Total_time_ms = total_time_ms
	Alc_time_ms = alc_time_ms
	Sampling_vol = sampling_vol
	Total_sampling = total_sampling
	Last_flow = last_flow
	P1_off = p1_off
	P2_off = p2_off
	Res_vacuum = res_vacuum
	Selected_p2 = selected_p2
	Tau_time = tau_time
	Pressure_peak = pressure_peak
	Avg_window = avg_window
	Slope_window = slope_window
	Threshold = threshold
	Sensed_vol = sens_volume
	if pipetting_done_req:
		print "Pipetting Done:"
		print "	total time = " + str(Total_time_ms)
		print "	Alc time = " + str(Alc_time_ms)
		print "	Sampling vol = " + str(Sampling_vol)
		print "	Total Sampling = " + str(Total_sampling)
		print "	Last Flow = " + str(Last_flow)
		print "	P1 Off = " + str(P1_off)
		print "	P2 Off = " + str(P2_off)
		print "	Residual vacuum = " + str(Res_vacuum)
		print "	Selected P2 = " + str(Selected_p2)
		print "	Tau Time = " + str(Tau_time)
		print "	Pressure Peak = " + str(Pressure_peak)
		print "	Average Window = " + str(Avg_window)
		print "	Slope Window = " + str(Slope_window)
		print "	Threshold = " + str(Threshold)
		print "	Sensed volume = " + str(Sensed_vol)
	else:
		print '*** evt: Pipetting done--'
	Pipetting_done = True

nn = 0

def handle_pipetting_error(error_code,sampling_vol,total_sampling,last_flow,p1_off,p2_off,res_vacuum,selected_p2,tau_time,pressure_peak,avg_window,slope_window,threshold,sens_volume,pip_state):
	global nn
	#time.sleep(1)
	if 0==1:
		global Pipetting_done
		global Pipetting_error

		# Tambahan untuk error ALC reporting:
		global ALC_error_code #Tambahan untuk demo
		global Sampling_vol
		global Total_sampling
		global Last_flow
		global P1_off
		global P2_off
		global Res_vacuum
		global Selected_p2
		global Tau_time
		global Pressure_peak
		global Avg_window
		global Slope_window
		global Threshold
		global Sensed_vol

		global Alc_time_ms
		global Sampling_vol

		ALC_error_code = error_code
		Sampling_vol = sampling_vol
		Total_sampling = total_sampling
		Last_flow = last_flow
		P1_off = p1_off
		P2_off = p2_off
		Res_vacuum = res_vacuum
		Selected_p2 = selected_p2
		Tau_time = tau_time
		Pressure_peak = pressure_peak
		Avg_window = avg_window
		Slope_window = slope_window
		Threshold = threshold
		Sensed_vol = sens_volume

		if pipetting_done_req:
			print "Pipetting Error:"
			print "	1 Pipetting Error code\t= " + str(ALC_error_code)
			print "	2 Sampling vol\t\t= " + str(Sampling_vol)
			print "	3 Total Sampling\t= " + str(Total_sampling)
			print "	4 Last Flow\t\t= " + str(Last_flow)
			print "	5 P1 Off\t\t= " + str(P1_off)
			print "	6 P2 Off\t\t= " + str(P2_off)
			print "	7 Residual vacuum\t= " + str(Res_vacuum)
			print "	8 Selected P2\t\t= " + str(Selected_p2)
			print "	9 Tau Time\t\t= " + str(Tau_time)
			print "	10 Pressure Peak\t= " + str(Pressure_peak)
			print "	11 Average Window\t= " + str(Avg_window)
			print "	12 Slope Window\t\t= " + str(Slope_window)
			print "	13 Threshold\t\t= " + str(Threshold)
			print "	14 Sensed volume\t= " + str(Sensed_vol)
		else:
			print '*** evt: Pipetting Error--'

		Alc_time_ms = 'N/A'
		Sampling_vol = 'N/A'

		Pipetting_done = True
		Pipetting_error = True
		p.stop_dllt()


def handle_motor_error(motor_id,motor_error_code):
	global move_done

	#print 'motor_error_code',motor_error_code

	move_done = True
	#print 'movedone',move_done


def handle_target_reach(monitor_id):
	global move_done
	move_done = True
custom = False	
phase2_fly = False
def handle_on_valve_closed(closed_time):
	global custom
	global phase2_fly
	if custom:phase2_fly = True
	#print custom,'custoooooooooooooooooooooooom'

	#print "Valve Closed time=" + str(closed_time)
def handle_on_regulate_pressure_aborted():
	print "Regulate pressure function aborted by vol limit"
def handle_motor_move_started(motor_id):
	print "Motor Move Started on id " + str(motor_id)

def handle_on_regulate_pressure_limit_reach():
	print "Regulate pressure function volume reached"

P2_valve_close = None
P2_t1 = None
P2_t2 = None

class AirTransfer:
	a = 0.6
	b = 3
	c = 3
	d = 1.5

phase1_air_tr = False
phase2_air_tr = False
No_liquid = False

air_transfer_by_flow = 0
air_transfer_by_p2 = 0
air_transfer_count = air_transfer_by_flow + air_transfer_by_p2

def handle_on_average_clog_detect_finish(p2_valve_close, p2_t1, p2_t2):
	global P2_valve_close
	global P2_t1
	global P2_t2
	global No_liquid
	global phase1_air_tr
	global Pipetting_done
	global air_transfer_by_p2
	
	#print "clog detect average done ATM = ",ATM_pressure, "p2_valve_close=",  p2_valve_close, ", p2_t1=", p2_t1, ", p2_t2=", p2_t2
	
	P2_valve_close = p2_valve_close
	P2_t1 = p2_t1
	P2_t2 = p2_t2

	
	Pipetting_done = True


def handle_on_air_transfer_detected(flow, time_ms):
	global phase1_air_tr
	global air_transfer_by_flow
	air_transfer_by_flow += 1
	print "air transfer detected flow =", flow, ", time=", time_ms
	phase1_air_tr = True
	
	

def handle_on_clog_detected(flow, time_ms):
	print "clog detected flow =", flow, ", time=", time_ms

#============== INIT ================================================================================================
#p.motor_move_started += handle_motor_move_started
p.motor_move_done += handle_move_done 
p.on_tare_done += handle_tare_done
p.on_calibrate_finish += handle_calibrate_finish
p.on_count_vol_done += handle_vol_count_finish
p.on_pipetting_done += handle_pipetting_done
p.on_average_done += handle_average_done
p.on_pipetting_error += handle_pipetting_error
p.on_regulate_pressure_limit_reach += handle_on_regulate_pressure_limit_reach
p.on_average_clog_detect_finish += handle_on_average_clog_detect_finish
p.on_valve_closed += handle_on_valve_closed
p.on_air_transfer_detected += handle_on_air_transfer_detected
p.on_clog_detected += handle_on_clog_detected

print p.get_app_name() + " Version = "+ p.get_version()


#p.on_pipetting_error += handle_pipetting_error
p.motor_error_occured += handle_motor_error
p.motor_target_reached +=handle_target_reach
#p.on_regulate_pressure_aborted += handle_on_regulate_pressure_aborted
#p.on_valve_closed += handle_valve_closed
#preg.controller_reach_limit += handle_controller_reach_limit
#print p.get_app_name() + " Version = "+ p.get_version()

#============== BASIC FUNCTION ================================================================================================
def enable_z():
	p.clear_motor_fault(0)
	clear_abort_config()
	p.set_motor_enabled(0,1)

def home_z():
	clear_abort_config()
	clear_motor_fault()
	enable_z()
	p.home_motor(0,0,1,1,stem_eng,stem_eng*10,stem_eng*100)
	status=1
	while (status & 1):
		status=p.get_motor_status(0)
		#print p.get_motor_pos(0)
		#print p.get_encoder_position(0)

def move_abs_z(abs,velc,acc,wait=1):

	global move_done
	move_done = False
	pos = p.get_motor_pos(0)/stem_eng
	upper = pos+2
	lower = pos-2
	#print p.get_abort_config(1)
	if lower<abs<upper:
		move_done = True
	p.move_motor_abs(0,abs*stem_eng,velc*stem_eng,acc*stem_eng)
	#print p.get_abort_config(1)
	if not move_done and wait==1:
		n=0
		while(move_done==False):
			print 'wait {}'.format(n)+'\r',
			n+=1
			time.sleep(0.1)
	return True

def move_rel_z(rel,velc,acc,wait=1):
	target_pos = (p.get_encoder_position(0) /stem_eng)  + rel
	move_abs_z(target_pos,velc,acc,wait)

def tare_pressure():
	abort_flow()
	global Tare_done
	Tare_done = False
	p.tare_pressure()
	while(1):
		time.sleep(0.1)
		if Tare_done:
			break
	if abs(Dp_Offset) > 3:
		return False
	if ATM_pressure < 900:
		return False
	if ATM_pressure > 1100:
		return False
	return True

def average_pressure(sample):
	#print "Averaging BEGIN"
	global Average_done
	global AverageP1
	global AverageP2
	Average_done = False
	p.averaging_pressure(sample)
	while(1):
		time.sleep(0.1)
		if Average_done:
			break
	dp = AverageP2 - AverageP1
	print "Averaging DONE"

def average_pressure_preg(id,sample):
	preg_sense=0
	for i in range(0,sample):
		preg_sense += preg.read_feedback_sensor(id)
	preg_sense = preg_sense/sample
	return preg_sense

def flush_pipetting_stat():
	global Total_time_ms
	global Alc_time_ms
	global Sampling_vol
	global Total_sampling
	global Last_flow
	global P1_off
	global P2_off
	global Res_vacuum
	global Pipetting_done
	global Selected_p2
	global Tau_time
	global Pressure_peak
	global Avg_window
	global Slope_window
	global Threshold
	global Sensed_vol
	Total_time_ms = '---'
	Alc_time_ms = '---'
	Sampling_vol = '---'
	Total_sampling = '---'
	Last_flow = '---'
	P1_off = '---'
	P2_off = '---'
	Res_vacuum = '---'
	Selected_p2 = '---'
	Tau_time = '---'
	Pressure_peak = '---'
	Avg_window = '---'
	Slope_window = '---'
	Threshold = '---'
	Sensed_vol = '---'

def wait_count_volume():
	global Count_volume_done
	x=0
	while(1):

		if Count_volume_done == True:
			break
		time.sleep(0.1)
		x+=1
		if x>600:
			Count_volume_done=True
			print "timeout wait"
			break

def calculate_flow(vol,tip):
	MaxFlowScale_P200 = 0.670
	MinFlowScale_P200 = 0.615
	DecelVolScale_P200 = 0.75

predicted_residual = 0
air_phase1 = False
def start_pipetting(vol,flow,flowmin=0,tip=200,timeout=120):
	global Pipetting_done
	global Pipetting_error
	global nn
	global predicted_residual
	global last_vol
	global phase2_fly
	global phase1_air_tr
	
	valve_res = 1000 if vol <5 else 60
	p.set_valve_open_response_ms(valve_res)
	phase1_air_tr = False
	phase2_fly = False
	
	nn = 0
	Pipetting_done = False
	Pipetting_error = False
	abort_flow()
	flush_pipetting_stat()
	
	if CAL_ASP==None or CAL_DSP==None:
		tare_pressure()
	last_vol = vol
	if vol<0:
		CAL = CAL_ASP
	else:
		CAL = CAL_DSP
	#p.set_alc_config(0.01,1,50,-50,1.7,-20,100,0.369,78,100,-0.0000819,0.2099155,0.0001,0.21,5000)
	AlcHi = {
		"TauThreshold"       : 0.63,
		"TauTimeMultiply"    : 3.42,
		"ThresPresSelect"    : 10.0,
		"ThresVacSelect"     : -10.0,
		"AvgWindowScale"     : 0.045,
		"AvgWindowOffset"    : 48,
		"AvgWindowLowLimit"  : 50,
		"SlopeWindowScale"   : 0.098,
		"SlopeWindowOffset"  : 21,
		"SlopeWindowLowLimit": 25,
		"ThresholdScale"     : -0.000000134453967,
		"ThresholdOffset"    : 0.001386783593667,
		"ThresholdLowLimit"  : 0.0000097,
		"ThresholdMaxLimit"  : 0.0008,
		"AlcTimeoutMs"       : 200000}

	AlcLo = {
		"TauThreshold"       : 0.63,
		"TauTimeMultiply"    : 3.42,
		"ThresPresSelect"    : 4.0,
		"ThresVacSelect"     : -4.0,
		"AvgWindowScale"     : 0.045,
		"AvgWindowOffset"    : 48,
		"AvgWindowLowLimit"  : 50,
		"SlopeWindowScale"   : 0.098,
		"SlopeWindowOffset"  : 21,
		"SlopeWindowLowLimit": 25,
		"ThresholdScale"     : -0.000000134453967,
		"ThresholdOffset"    : 0.001386783593667,
		"ThresholdLowLimit"  : 0.0000097,
		"ThresholdMaxLimit"  : 0.0008,
		"AlcTimeoutMs"       : 200000}
	#vvv new ALC speed optimized for viscous
	
	if abs(vol)<=20:
		Alc = AlcLo
	else:
		Alc = AlcHi
	
	p.set_alc_config(
		Alc["TauThreshold"],       
		Alc["TauTimeMultiply"],   
		Alc["ThresPresSelect"],    
		Alc["ThresVacSelect"],     
		Alc["AvgWindowScale"],     
		Alc["AvgWindowOffset"],    
		Alc["AvgWindowLowLimit"],  
		Alc["SlopeWindowScale"],   
		Alc["SlopeWindowOffset"],  
		Alc["SlopeWindowLowLimit"],
		Alc["ThresholdScale"],     
		Alc["ThresholdOffset"],    
		Alc["ThresholdLowLimit"],  
		Alc["ThresholdMaxLimit"],
		Alc["AlcTimeoutMs"],)       
	if tip == 200:
		res_pres_off=0.1*((((1*0.98*((3*((abs(vol))-0.06283+0.1642))/(0.0026*pi))**(1/3.0)-3.42)*1))+5)
		res_vac_off=-0.1*((((1*0.98*((3*((abs(vol))-0.06283+0.1642))/(0.0026*pi))**(1/3.0)-3.42)*1))+0)
		#print "Start Pipetting using Tip = P200"
	elif tip ==20:
		res_vac_off=-0.1*((((1*0.98*((3*((abs(vol))-0.06283+0.2823))/(0.00088*pi))**(1/3.0)-6.24)*1))+8)
		res_pres_off=0.1*((((1*0.98*((3*((abs(vol))-0.06283+0.2823))/(0.00088*pi))**(1/3.0)-6.24)*1))+8)
		#print "Start Pipetting using Tip = P20"
	else:
		res_vac_off=0
		res_pres_off=0
		
	
	if(vol < 0): # after Aspirate --> vacuum
		predicted = res_vac_off
	else: # after Dispense --> pressure
		predicted = res_pres_off
	predicted_residual = predicted
	#predicted=0
	#print p.start_pipetting(1, 0, vol,flow,0,400)['target_p1']
	max_flow = flow
	min_flow = max_flow if flowmin==0 else flowmin
	#print min_flow
	
	decel_vol = vol*2 if flowmin==0 else 0.75
	decel_vol = decel_vol*vol
	dead_vol = 200+tip #420.69
	
	#p2high_limit = 1400
	#p2low_limit = 300
	
	if vol < 0 : # aspirate
		p2high_limit = 100 * 68.948
		p2low_limit = 100 * 68.948
	else: # dispense
		p2high_limit = 0.4 * 68.948 # = 27.58
		p2low_limit = 0.3 * 68.948 # = 20.68
	
	start_ave_t1_ms = 100
	ave_window_p2t1 = 50
	start_ave_t2_ms = 1000
	ave_window_p2t2 = 100
	if vol > 0:
		start_ave_t1_ms = 0
		ave_window_p2t1 =1
		start_ave_t2_ms = 0
		ave_window_p2t2 = 1
	
	start = time.time()
	pipetting_time = 0
	p.start_pipetting(1, 0, vol, max_flow, min_flow, decel_vol, predicted, dead_vol,p2high_limit, p2low_limit,start_ave_t1_ms,ave_window_p2t1,start_ave_t2_ms,ave_window_p2t2)
	#print max_flow,min_flow,decel_vol
	if air_phase1:
		move_rel_z(5,20,1000,0)
	
	timeout=20 #override khusus gravimetric
	#timeout=60 #override khusus platereader 

	t2 = 0
	while not Pipetting_done:
		if phase2_fly:
			#pipetting_time = time.time()
			pos = p.get_motor_pos(0)/stem_eng +3
			p.move_motor_abs(0,pos*stem_eng,100*stem_eng,10000*stem_eng)
			#move_rel_z(10,100,10000,1)
			phase2_fly = False
		if (time.time()-start)>=timeout:
			#pipetting_time = time.time()
			print "Pipetting Timeout!!\n"
			abort_flow()
			Pipetting_done = True
		else:
			t1 = time.time()-start
			if t1%1 == 0 and t2 != t1:
				t2 = t1
				print int(time.time()-start), "timeout at", timeout
	#return round((pipetting_time-start),3)
	
	p.stop_dllt()
def cek_p2_average():
	global No_liquid
	global air_transfer_by_p2
	No_liquid_by_avp2 = False
	No_liquid_by_res= False
	
	if last_vol < 0: #only aspirate case
		No_liquid = ATM_pressure - P2_t1 <= AirTransfer.d 
		No_res = Res_vacuum > -1.
		
		if No_liquid and not phase1_air_tr and not phase2_air_tr : 
			print 'aspirate udara'
			No_liquid_by_avp2 = True
			air_transfer_by_p2 += 1	
		if No_res : 
			print 'aspirate udara by res'
			No_liquid_by_res= True
			#air_transfer_by_p2 += 1
		return No_liquid_by_avp2 or No_liquid_by_res
			
			

def aspirate(vol,flow,flowmin=5,log=0,timeout=5000,tip=200):
	#p.set_abort_config(7,0,512,0,0)
	start = time.time()
	
	if log == 1:
		start_logger(0,SensorMask.PressureSensor1+SensorMask.PressureSensor2)
		time.sleep(1)
	start_pipetting(-1*vol, flow,flowmin,tip,timeout)
	pipetting_time = (time.time() - start)*1000
	print "Pip time asp", pipetting_time,'ms'
	if log == 1:
		stop_logger()
		time.sleep(1)
	return pipetting_time

def dispense(vol,flow,flowmin=5,log=0,timeout= 5000,tip=200):
	start = time.time()
	if log == 1:
		start_logger()
		time.sleep(1)
	start_pipetting(vol, flow,flowmin,tip,timeout)
	pipetting_time = (time.time() - start)*1000
	print "Pip time dsp", pipetting_time,'ms'
	if log == 1:
		time.sleep(1)
		stop_logger()
	return pipetting_time

def dpc_on():
	#start_logger(0,294)
	'''
	Make sure do DPC On after aspirate
	'''
	global AverageP2
	time.sleep(0.2)
	average_pressure(100)
	p_dpc = AverageP2
	p.start_regulator_mode(1,p_dpc,2,1,10)

	print("DPC ON at P2 = {}".format(p_dpc))

def dpc_off():
	p.abort_flow_func()
	print("DPC OFF")
	time.sleep(0.2)

def start_pipetting2(vol,flow,flowmin=0,timeout=10000):
	global Pipetting_done
	global Pipetting_error
	global nn
	nn = 0
	Pipetting_error = False
	Pipetting_done = False
	p.set_alc_config(0.63,9.0,25.0,-25.0,1.7,-20,100,0.369,78,100,-0.0000819,0.2099155,0.0001,0.21,200000)

	predicted = 0
	#print p.start_pipetting(1, 0, vol,flow,0,400)['target_p1']
	max_flow = flow
	if flowmin == 0:
		min_flow = max_flow
	else:
		min_flow = flowmin
	decel_vol = 0.75 if flowmin != 0 else 100000
	dead_vol = 650
	p2high_limit = 1400
	p2low_limit = 300

	start_ave_t1_ms = 100
	ave_window_p2t1 = 50
	start_ave_t2_ms = 1000
	ave_window_p2t2 = 100
	
	
	p.start_pipetting(0, 0, vol, max_flow, min_flow, decel_vol, predicted, dead_vol, p2high_limit, p2low_limit,start_ave_t1_ms,ave_window_p2t1,start_ave_t2_ms,ave_window_p2t2)

	#timeout=2000
	start = time.time()
	end = 0
	while(1):
		#time.sleep(0.01)
		end = time.time()-start
		if Pipetting_done == True:
			print "bar"
			break
		if end==timeout:
			print "Pipetting Timeout!!\n"
			Pipetting_done = True
			abort_flow()

def aspirate_2(vol,flow,log=0,timeout=2000):
	#p.set_abort_config(7,0,512,0,0)
	if log == 1: start_logger()
	time.sleep(1)
	start_pipetting2(-1*vol, flow,flow,timeout)
	time.sleep(1)
	if log == 1: stop_logger()

def dispense_2(vol,flow,log=0,timeout=2000):
	if log == 1: start_logger()
	time.sleep(1)
	start_pipetting2(vol, flow,flow,timeout)
	time.sleep(1)
	if log == 1: stop_logger()


#============== USER FUNCTION ================================================================================================
def set_sensor_config():
	p.set_sensor_config(CAL_ASP,CAL_DSP,CAL_OFF_ASP,CAL_OFF_DSP,DP_HIGH_THRES,DP_LOW_THRES,EXTRA_OFF_ASP,EXTRA_OFF_DSP,EXTRA_SCALE_ASP,EXTRA_SCALE_DSP,SLOPE_THRES,SENSOR_ID)
	p.save_configuration()

def aspirate_dpc(vol,flow):
	global AverageP1
	aspirate(vol,flow)
	average_pressure(1000)
	p.start_regulator_mode(0,AverageP1)


def solenoid_test(x=150):
	print "== SOLENOID TEST BEGIN =="

	for i in range(0,x):
		# print "p.set_valve(1) --> Chip Valve Vacuum --> OPEN"
		p.set_valve(1)
		time.sleep(0.25)
		# print "p.set_drain(1) --> E-Reg Drain OPEN --> P/V LEAK"
		p.set_drain(1)
		time.sleep(0.25)

		# print "p.set_valve(0) --> Chip Valve Pressure --> CLOSE"
		p.set_valve(0)
		time.sleep(0.25)
		# print "p.set_drain(0) --> E-Reg Drain CLOSE --> P/V HOLD"
		p.set_drain(0)
		time.sleep(0.25)
		print "loop : ",i+1,"/",x

	print "-- OK --"
	print "== SOLENOID TEST END =="
	beep(1)

def beep(s=1):
	if s==1:
		for i in range(0,3):
			Beep(1000,1000)

	else:
		for i in range(0,20):
			Beep(5000,200)

def config_set(*args):
	Change=False
	if len(args)!=2:
		Change=False
	else:
		if (-1<args[0]<14):
			Change=True
		else: False

	# 0 'cal_static_asp'
	# 1 'cal_static_dsp',
	# 2 'flow_drift_asp',
	# 3 'flow_drift_dsp',
	# 4 'DpHighThreshold',
	# 5 'DpLowThreshold',
	# 6 'ExtraOffsetAsp',
	# 7 'ExtraOffsetDsp',
	# 8 'ExtraScaleAsp',
	# 9 'ExtraScaleDsp',
	# 10 'SlopeThreshold',
	# 11 'vicous_scale',
	# 12 'viscous_offset',
	# 13 'SensorId'


	data= str(p.get_sensor_config())
	print"==============================================================="
	#decode


	for c in "()[]' ": data=data.replace(c,'')
	data=data[11:]
	data=data.split(',')
	item=[]
	value=[]
	for i in range(0,28,2):
		item.append(data[i])
	for i in range(1,28,2):
		value.append(data[i])
	for i in range(0,len(value)-1):
		value[i]=float(value[i])
	#print
	#for i in range(0,len(item)):
	#	print item[i]," = ",value[i]

	if Change:
		value[args[0]]=args[1]
		p.set_sensor_config(value[0],value[1],value[2],value[3],value[4],value[5],value[6],value[7],value[8],value[9],value[10],value[11],value[12],value[13])
		p.save_configuration()
		print " "
		print ">>>> Config Changed <<<<<<"
		print " "

		for i in range(0,len(item)):
			if i==args[0]:
				print item[i]," = ",value[i], " <<<< "
			else:
				print item[i]," = ",value[i]

	return value


def flow_start(flow):
	ereg_source()
	p.set_valve(1)
	p.start_regulator_flow(flow)
	stream_p(3)


def calculate_linear_scale_offset(X,Y):
	nX=len(X)
	nY=len(Y)
	#print nX
	#print nY

	limitz=0
	if(nX>nY):
		limitz=nY
	else :
		limitz=nX

	XY=[]
	X2=[]
	Y2=[]
	sumX=0
	sumY=0
	sumXY=0
	sumX2=0
	sumY2=0

	for i in range(0,limitz):
		XY.append(X[i]*Y[i])
		X2.append(X[i]*X[i])
		Y2.append(Y[i]*Y[i])

		sumX+=X[i]
		sumY+=Y[i]
		sumXY+=XY[i]
		sumX2+=X2[i]
		sumY2+=Y2[i]

	offset=((sumY*sumX2)-(sumX*sumXY))/(limitz*sumX2-sumX*sumX)
	scale=(limitz*sumXY-sumX*sumY)/(limitz*sumX2-sumX*sumX)


	#print "scale= ", scale
	#print "offset= ", offset
	return [scale,offset]



extra_p1_off_asp=[]
extra_vol_asp=[]
extra_p1_off_dsp=[]
extra_vol_dsp=[]
extra_asp=[0,0]
extra_disp=[0,0]

def abort_flow():
	p.abort_flow_func()
	p.stop_dllt()

def test_extra_vol_asp2(flows,volume=100):
	global extra_p1_off_asp
	global extra_vol_asp
	global extra_asp
	#volume = 100
	tare_pressure()
	print "flow: ", flows
	for flow in flows:
		
		#print "flow:" + str(flow) + ", End Flow:" + str(end_flow)
		tare_pressure()
		print "Generate flow: ",flow
		aspirate_2(volume,flow)
		time.sleep(2)
		extra_p1_off_asp.append(P1_off)
		extra_vol_asp.append(Sensed_vol+volume)

	print "finish extra aspirate test"
	extra_asp=calculate_linear_scale_offset(extra_p1_off_asp,extra_vol_asp)
	correl = format_float(corrcoef(extra_p1_off_asp,extra_vol_asp)[0,1])

	print correl
	extra_p1_off_asp=[]
	extra_vol_asp=[]

def test_extra_vol_dsp2(flows,volume=100):
	global extra_p1_off_dsp
	global extra_vol_dsp
	global extra_disp
	#volume = 100

	tare_pressure()
	print "flow: ", flows
	for flow in flows:
		
		tare_pressure()
		print "Generate flow: ",flow
		dispense_2(volume,flow)
		time.sleep(2)
		extra_p1_off_dsp.append(P1_off)
		extra_vol_dsp.append(Sensed_vol-volume)
		

	print "finish extra dispense test"
	extra_disp=calculate_linear_scale_offset(extra_p1_off_dsp,extra_vol_dsp)
	correl = format_float(corrcoef(extra_p1_off_dsp,extra_vol_dsp)[0,1])

	print correl
	print extra_p1_off_dsp
	print extra_vol_dsp
	extra_p1_off_dsp=[]
	extra_vol_dsp=[]

def extra_vol_test(flows=[1000,800,500,200,100],volume=100): #KHUSUS 1ML
	global pipetting_done_req
	global tare_done_req
	#pipetting_done_req = False
	#tare_done_req = False
	global extra_asp

	global extra_disp
	#ereg_source()
	#set_plug(0)
	abort_flow()
	tare_pressure()
	test_extra_vol_asp2(flows,volume)

	print "Ext_asp scale: ",extra_asp[0], " ","offset",extra_asp[1]
	config_set(8,extra_asp[0])
	config_set(6,extra_asp[1])
	time.sleep(2)

	test_extra_vol_dsp2(flows,volume)
	config_set(9,extra_disp[0])
	config_set(7,extra_disp[1])

	print "Extra volume test -- DONE --"
	print "Ext_asp scale: ",extra_asp[0], " ","offset",extra_asp[1]
	print "Ext_disp scale: ",extra_disp[0], " ","offset",extra_disp[1]

	extra_asp=[0,0]
	extra_disp=[0,0]

	status = [False,False]
	asp_c = abs(p.get_sensor_config()['ExtraScaleAsp']*-0.5+p.get_sensor_config()['ExtraOffsetAsp'])
	dsp_c = p.get_sensor_config()['ExtraScaleDsp']*0.5+p.get_sensor_config()['ExtraOffsetDsp']

	if asp_c < 2:
		status[0] = True
	if dsp_c <2:
		status[1] = True
	pipetting_done_req = True
	tare_done_req = True
	print "Aspirate:", status[0], '---- Dispense:',status[1]
	return status




def valve_bukatutup(a=100):
	for i in range(a):
		p.set_valve(0)
		time.sleep(0.1)
		p.set_valve(1)
		time.sleep(0.1)

def read_breach(iter):

	while(1):
		ready=raw_input("enter jika siap ambil data tanpa liquid ")
		if ready=='':
			break

	print "lanjut"
	baseline=[]
	for i in range(iter*1000):
		baseline.append(p.read_breach_capacitance())
		time.sleep(0.01)
	baseline=1.0*sum(baseline)/len(baseline)

	print "baseline = ", baseline

	while(1):
		ready=raw_input("enter untuk lanjut dengan liquid ")
		if ready=='':
			break
	print "lanjut"
	max=[]
	for i in range(iter*1000):
		max.append(p.read_breach_capacitance())
		time.sleep(0.01)
	max=1.0*sum(max)/len(max)

	print "max = ", max

	threshold=((max-baseline)/2)+baseline
	print "threshld: ", threshold
	p.set_breach_threshold(threshold)
	time.sleep(1)
	p.set_breach_threshold(threshold)
	time.sleep(1)
	p.set_breach_threshold(threshold)

	print "threshold set :", p.get_breach_threshold()


def print_flash(a):

	print " %s \r" % a,
	time.sleep(0.1)
	sys.stdout.flush()

def cek_pid_ereg():
	abort_flow()
	tare_pressure()
	status = True
	vol = [5,20,200,]
	flow = [15,20,150]

	for i in range(0,len(vol)):
		start_logger(0,128+2048)
		tare_pressure()
		time.sleep(1)
		aspirate(vol[i],flow[i],flow[i])
		if Pipetting_error == True:
			status = False
			break
		time.sleep(1)

		tare_pressure()
		time.sleep(1)
		dispense(vol[i],flow[i],flow[i])
		if Pipetting_error == True:
			status = False
			break
		stop_logger()

		time.sleep(1)
	abort_flow()
	return status
def set_pid_ereg():
	origin = [p.get_regulator_pid(0),p.get_regulator_pid(1),p.get_regulator_pid(2)]

	id_ = int(raw_input('ID? vac=0, pres=1, dpc=2 : '))
	print p.get_regulator_pid(id_)
	print ''
	print 'Enter to SKIP'
	print''

	consP = (raw_input('kP : '))
	consP = origin[id_]['kp'] if consP == '' else consP

	consI = (raw_input('kI : '))
	consI = origin[id_]['ki'] if consI == '' else consI

	consD = (raw_input('kD : '))
	consD = origin[id_]['kd'] if consD == '' else consD

	offset = (raw_input('offset : '))
	offset = origin[id_]['o'] if offset == '' else offset

	thdrain= (raw_input('thres drain : '))
	thdrain= origin[id_]['thres_idrain'] if thdrain == '' else thdrain

	iLim = (raw_input('i limit : '))
	iLim = origin[id_]['i_limit'] if iLim == '' else iLim

	p.set_regulator_pid(id_,consP,consI,consD,offset,thdrain,iLim)
	print p.get_regulator_pid(id_)
	p.save_configuration()



def default_pid_mini():
	set1 = p.get_regulator_pid(1)
	set0 = p.get_regulator_pid(0)
	p.set_regulator_pid(0,0.01,1e-5,0,0,2,2)
	p.set_regulator_pid(1,0.01,1e-5,0,0,2,2)
	print p.get_regulator_pid(0)
	print p.get_regulator_pid(1)



def cek_flow(max=0.6):
	abort_flow()

	A = [1,0] #pressure dulu aja
	average_pressure(200)
	time.sleep(1)
	side = ['Vacuum','Pressure']
	peak = [AverageP1,AverageP1]
	peak2 = [AverageP2,AverageP2]
	Target_flow_rel2 = [600,600]
	status = [False,False]
	status2 = [False,False]
	rate = [0,0]
	rate2 = [0,0]
	print "cek flow start"
	print 'ATM: ',format_float(AverageP2)
	print "set out = ",format_float(max)
	for i in A:
		abort_flow()
		p.set_drain(0)
		p.set_valve(1)
		time.sleep(5)
		average_pressure(200)
		time.sleep(1)
		idle = format_float(AverageP1)
		idle2 = format_float(AverageP2)
		p.set_prop_valve_out(i,max)

		for x in range(50):

			open = format_float(p.read_pressure_sensor(0))
			open2 = format_float(p.read_pressure_sensor(1))

			if i == 1 :
				if open>peak[1]: peak[1] = open
				if open2>peak2[1]:peak2[1] = open2
			else :
				if open<peak[0]: peak[0] = open
				if open2<peak2[0]:peak2[0] = open2

			a = side[i]+' >>'+' output: '+str(format_float(p.get_prop_valve_out(i)))+'\tP1: '+str(open)+'\tP2: '+str(open2)
			if x==(50-1): a = a + '---------\n'
			print " %s \r" % a,
			time.sleep(0.1)
			sys.stdout.flush()

		rate[1] = format_float((peak[1]-idle)/ Target_flow_rel[0]*100)
		rate[0] = format_float((idle - peak[0])/ Target_flow_rel[1]*100)

		if rate[1]> 80: status[1] = True
		if abs (rate[0]) > 80: status[0] = True



		if  0 < peak2[1]-idle2 <= 10: status2[1] = True
		if 0 < idle2-peak2[0] <= 10: status2[0] = True

	print 'rateP1', str(rate[0])+'%',str(rate[1])+'%'
	print 'P1: ', status, 'P2: ',status2
	print 'All should be True to continue'

	abort_flow()
	final_stat = status[0] and status[1] and status2[0] and status2[1]
	return final_stat

def ready_to_flow():
	abort_flow()
	p.set_valve(0)
	time.sleep(0.5)
	p.set_drain(1)
	time.sleep(0.5)

	p.set_valve(1)
	time.sleep(0.5)
	p.set_drain(0)
	time.sleep(0.5)

def set_mini2():

	abort_flow()
	tare_pressure()

	status = False
	rough_tune = 0.05
	fine_tune = 0.01

	tolerance = 1
	max_set = 0.48
	max_out = 0.667

	leaks = False
	stuck = False
	state = False

	stuck = not cek_flow()
	time.sleep(2)
	tare_pressure()
	range0 = [p.get_prop_valve_range(0)['min_duty'],p.get_prop_valve_range(0)['max_duty']]
	range1 = [p.get_prop_valve_range(1)['min_duty'],p.get_prop_valve_range(1)['max_duty']]

	print 'Vac range\t:', range0
	print 'Pres range\t:', range1

	id=[0,1]
	for i in id:
		if leaks or stuck:
			print "FAIL"
			break
		set = 0
		inc = rough_tune

		p.set_prop_valve_range(i,0,1)
		print "Range Limit 0-1"
		#start_logger()
		ready_to_flow()
		time.sleep(3)
		average_pressure(200)
		#stop_logger()
		time.sleep(2)
		idle = format_float(AverageP1)

		print 'idle', idle
		print "Tuning start"

		while(1):
			ready_to_flow()
			p.set_prop_valve_out(i,set)
			time.sleep(3)
			average_pressure(200)

			time.sleep(1)
			open = format_float(AverageP1)
			a = 'id: '+ str(i)+', set: '+str(set)+', idle: '+str(idle)+', open: '+str(open)
			#print "id: ", i,", set: ",set,", idle: ",idle,", open: ",open
			print_flash(a)
			abort_flow()

			set += inc
			if set >= max_set:
				print "Max set point reach, tuning fail"
				break

			is_lower = open < idle-tolerance
			is_higher =  open > idle+tolerance
			is_stable = idle-tolerance <= open <=idle+tolerance


			is_other_leak = (is_lower and i==1) or (is_higher and i==0)
			is_this_leak = (is_lower or is_higher) and set == 0 and not is_other_leak
			is_leak = is_other_leak or is_this_leak

			is_open_found = (is_lower or is_higher) and set > 0

			if is_leak :
				leaks = True
				if is_other_leak:
					print "current id: ", i, " -other PV is leaking"

				if is_this_leak:
					print "current id: ", i, " -this PV is leaking"
				print "Config not saved"
				abort_flow()
				break


			if is_open_found:
				print "Found opening"
				if inc == rough_tune:
					set = set - inc - inc
					inc = fine_tune
					print "Fine Tune"

				elif inc == fine_tune:
					set = set -inc-inc
					p.set_prop_valve_range(i,set,max_out)
					p.set_prop_valve_range(i,set,max_out)
					print "Value set for id = ", i , set
					print p.get_prop_valve_range(i)
					time.sleep(1)
					p.save_configuration()
					abort_flow()
					status = True
					break
		abort_flow()
	abort_flow()
	#print p.get_prop_valve_range(0),p.get_prop_valve_range(1)
	beep()
	return status

def set_breach_in():
	a = 0
	for i in range(100):
		b = p.read_breach_capacitance()
		if b > a:
			a = b
			print a

		time.sleep(0.1)

	time.sleep(1)
	print "breach: ", a
	print "threshold: ", p.get_breach_threshold()
	new_th=a+25000
	p.set_breach_threshold(new_th)
	time.sleep(1)
	p.set_breach_threshold(new_th)
	time.sleep(1)
	print "new_th: ", p.get_breach_threshold()
	time.sleep(2)
	p.save_configuration()
	p.save_configuration()
	p.save_configuration()


def set_averaging_col():
	p.set_sensor_averaging_window_size(0,128)
	p.save_configuration()

def wlldxx():
	p.set_abort_threshold(4,100)
	p.set_abort_config(1,0,16,16,0)
	p.set_abort_config(6,0,16,16,0)
	move_abs_z(-125,15,1000)
	p.set_abort_config(1,0,0,0,0)
	p.set_abort_config(6,0,0,0,0)

def set_estop_abort(thres):
	sensor_mask = InputAbort.CollisionEstop
	abort_id = AbortID.EstopOut
	thres = p.read_collision_sensor() - thres
	p.set_abort_threshold(sensor_mask,thres)
	p.set_abort_config(abort_id,0,1<<sensor_mask,1<<sensor_mask,0)
	p.set_abort_config(AbortID.HardZ,0,1<<sensor_mask,1<<sensor_mask,0)

def clear_estop():
	p.set_abort_config(AbortID.EstopOut,0,0,0,0)
	p.set_abort_config(AbortID.HardZ,0,0,0,0)

def clear_abort_config(abort_id=1):
	p.set_abort_config(abort_id,0,0,0,0)

def clear_motor_fault():
	 p.clear_motor_fault(0)
	 p.set_motor_enabled(0,1)

def set_current_abort(thres):
	sensor_mask = InputAbort.CurrentMotorZ
	abort_id = AbortID.HardZ

	p.set_abort_threshold(sensor_mask,thres)
	p.set_abort_config(abort_id,0,1<<sensor_mask,0,0)

def set_pressure_abort(thres=4):
	sensor_mask = InputAbort.PressureSensor2
	abort_id = AbortID.HardZ
	thres = p.read_pressure_sensor(1) + thres
	p.set_abort_threshold(sensor_mask,thres)
	p.set_abort_config(abort_id,0,1<<sensor_mask,0,0)

def set_collision_abort(thres):
	sensor_mask = InputAbort.CollisionTouch
	abort_id = AbortID.HardZ
	thres = p.read_collision_sensor() - thres
	p.set_abort_threshold(sensor_mask,thres)
	p.set_abort_config(abort_id,0,1<<sensor_mask,1<<sensor_mask,0)


def set_picktip_abort(col=100,curr=0.5):
	abort_id = AbortID.HardZ
	threscol = p.read_collision_sensor()-col
	threscur = curr
	#print threscol,threscur
	p.set_abort_threshold(InputAbort.CollisionTouch,threscol)
	p.set_abort_threshold( InputAbort.CurrentMotorZ,threscur)
	sensor_mask = (1<<InputAbort.CollisionTouch) +(1<< InputAbort.CurrentMotorZ)
	p.set_abort_config(abort_id,1,sensor_mask,1<<InputAbort.CollisionTouch,0)
	#p.set_abort_config(abort_id,0,1<<sensor_mask,0,0)

class PLLDConfig():
	flow = 10
	flow_delay = 250
	stem_vel = 15
	stem_acc = 1000
	colThres = 100
	currentThresh = 1.3
	pressThres = 4.5
	resThres = 500
	freq = 500
	freq_delay = 250/1000.0
	windowSize = 5
	useDynamic = True
	pAvgSample = 1000.0
	stripGap = 0.4
	decel = (stem_vel**2)/(2*stripGap)

class WLLDConfig():
	stem_vel = 15
	stem_acc = 1000
	colThres = 40
	currentThresh = 1.3
	resThres = 50
	freq = 510
	freq_delay = 250/1000.0

class PrereadingConfig():
	stem_vel = 10
	stem_acc = 1000
	stepDown = 1
	readDelay = 200/1000.0
	freq = 120
	freq_delay = 250/1000.0
	thresMultiplier = 0.25
	dlltMinAspThres = 200
	dlltMinDspThres = 200
	dlltMinThres = -700
	dlltMaxThres = 700

class DLLTConfig():
	class Res:
		stepSize = 0.5
		bigStep = 2
		kp = 1.5
		ki = 0
		kd = 10
		samplingTime = 15
		inverted = False
		stem_vel = 40
		stem_acc = 10000
		colThres = 40

	class Geo:
		trackFactor = 6.36
		stem_vel = 150
		stem_acc = 2000
		inverted = False
		startVolThres = 0
		colThres = 40
		trackProfile = 'ProfileLookUpTable'

class PipettingConfig():
	NonPipettingResponseMS = 60

class chipCalibrationConfig():
	upperlimit = 9.0
	lowerLimit = -148.0
	colCompressTolerance = 4.0

def setUp_plld(lowSpeed=False):
	p.set_valve_open_response_ms(PipettingConfig.NonPipettingResponseMS)
	p.start_regulator_mode(2,PLLDConfig.flow,1,0,0)
	p.set_AD9833_Frequency(PLLDConfig.freq)
	time.sleep(PLLDConfig.freq_delay)
	# Find threshold
	p.set_sensor_averaging_window_size(SensorID.Pressure1, PLLDConfig.windowSize)
	p.set_sensor_averaging_window_size(SensorID.Pressure2, PLLDConfig.windowSize)
	average_pressure(PLLDConfig.pAvgSample)
	global AverageP2; p_ref = AverageP2
	pressThres = 0
	if PLLDConfig.useDynamic:
		global Max_p2, Min_p2
		print 'P2 Value', Max_p2, Min_p2
		pressThres = (Max_p2 - Min_p2)/2.0*PLLDConfig.pressThres
	else:
		pressThres = PLLDConfig.pressThres
	print p_ref, pressThres
	p_ref += pressThres
	print 'Dynamic:',PLLDConfig.useDynamic,'| pressThres:',p_ref,'| resThres:',p.read_dllt_sensor()-PLLDConfig.resThres

	# Clear All Abort
	clear_motor_fault()
	clear_estop()
	clear_abort_config(AbortID.NormalAbortZ)
	clear_abort_config(AbortID.HardZ)
	clear_abort_config(AbortID.ValveClose)
	# Set Abort PLLD
	p.set_abort_threshold(InputAbort.CollisionTouch,p.read_collision_sensor()-PLLDConfig.colThres)
	p.set_abort_threshold(InputAbort.PressureSensor2,p_ref)
	p.set_abort_threshold(InputAbort.CurrentMotorZ,PLLDConfig.currentThresh)
	p.set_abort_threshold(InputAbort.LiquidLevelSensor,p.read_dllt_sensor()-PLLDConfig.resThres)
	collision = 1<<InputAbort.CollisionTouch
	pressure = 1<<InputAbort.PressureSensor2
	current = 1 <<InputAbort.CurrentMotorZ
	wlld = 1 << InputAbort.LiquidLevelSensor
	#p.set_abort_config(AbortID.TouchOffOut,0,current+collision+wlld,collision+wlld,0)
	p.set_abort_config(AbortID.ValveClose,0,pressure+current+collision,collision,0)
	if lowSpeed:
		p.set_abort_config(AbortID.HardZ,0,pressure+collision+wlld+current,collision+wlld,0)
	else: # normal PLLD
		p.set_abort_config(AbortID.NormalAbortZ,0,pressure+current+collision,collision,0)
		p.set_abort_config(AbortID.HardZ,0,collision+wlld+current,collision+wlld,0)
	return p_ref

def setUp_wlld():
	p.set_AD9833_Frequency(WLLDConfig.freq)
	time.sleep(WLLDConfig.freq_delay)
	# Clear All Abort
	clear_abort_config(AbortID.HardZ)
	clear_abort_config(AbortID.ValveClose)
	# Set Abort PLLD
	p.set_abort_threshold(InputAbort.CollisionTouch,p.read_collision_sensor()-PLLDConfig.colThres)	
	p.set_abort_threshold(InputAbort.CurrentMotorZ,PLLDConfig.currentThresh)
	p.set_abort_threshold(InputAbort.LiquidLevelSensor,p.read_dllt_sensor()-PLLDConfig.resThres)
	collision = 1<<InputAbort.CollisionTouch
	current = 1 <<InputAbort.CurrentMotorZ
	wlld = 1 << InputAbort.LiquidLevelSensor
	#p.set_abort_config(AbortID.TouchOffOut,0,current+collision+wlld,collision+wlld,0)
	p.set_abort_config(AbortID.HardZ,0,current+collision+wlld,collision+wlld,0)
	p.set_abort_config(AbortID.ValveClose,0,current+collision+wlld,collision+wlld,0)
	return p.read_dllt_sensor()-PLLDConfig.resThres

def setUp_dllt():
	p.set_motor_tracking_running(False)
	if get_triggered_input(AbortID.NormalAbortZ) or get_triggered_input(AbortID.HardZ):
		clear_abort_config(AbortID.NormalAbortZ)
		clear_abort_config(AbortID.HardZ)

def set_plld(press=3,col=100,cur=1,thres=2000,freq=510,freq_delay=250,dynamic=False,pAvgSample=10,init=False):#resistance val dibesarkan dulu
	if not init:
		col = PLLDConfig.colThres
		cur = PLLDConfig.currentThresh
		press = PLLDConfig.pressThres
		thres = PLLDConfig.resThres
		freq = PLLDConfig.freq
		freq_delay = PLLDConfig.freq_delay
		global Avg_window; Avg_window = PLLDConfig.windowSize
		dynamic = PLLDConfig.useDynamic
		pAvgSample = PLLDConfig.pAvgSample

	if dynamic:
		p_col, pmax, pmin = [], 0, 0
		t1 = time.time()
		while time.time()-t1 <=2:
			p_col.append(p.read_pressure_sensor(1))
		pmax, pmin = max(p_col), min(p_col)
		press = (pmax-pmin)*PLLDConfig.pressThres/2.0
	set_freq(freq)
	abort_id = AbortID.HardZ
	abort_id2 = AbortID.ValveClose
	average_pressure(pAvgSample)
	col = p.read_collision_sensor() - col
	press = AverageP2 + press
	thres = p.read_dllt_sensor() - thres

	p.set_abort_threshold(InputAbort.PressureSensor2,press)
	p.set_abort_threshold(InputAbort.CollisionTouch,col)
	p.set_abort_threshold(InputAbort.CurrentMotorZ,cur)
	p.set_abort_threshold(InputAbort.LiquidLevelSensor,thres)

	pressure = 1<<InputAbort.PressureSensor2
	collision = 1<<InputAbort.CollisionTouch
	current = 1 <<InputAbort.CurrentMotorZ
	wlld = 1 << InputAbort.LiquidLevelSensor

	p.set_abort_config(abort_id,0,pressure+current+collision+wlld,collision+wlld,0)
	p.set_abort_config(abort_id2,0,pressure+current+collision+wlld,collision+wlld,0)
	return press, dynamic

def set_wlld_abort(thres):
	set_freq(210)
	abort_id = AbortID.HardZ
	col = p.read_collision_sensor() - 30
	thres = p.read_dllt_sensor() - thres
	p.set_abort_threshold(InputAbort.CollisionTouch,col)
	p.set_abort_threshold(InputAbort.CurrentMotorZ,0.9)
	p.set_abort_threshold(InputAbort.LiquidLevelSensor,thres)
	collision = 1<<InputAbort.CollisionTouch
	current = 1 <<InputAbort.CurrentMotorZ
	wlld = 1 << InputAbort.LiquidLevelSensor
	p.set_abort_config(abort_id,0,current+collision+wlld,collision+wlld,0)

def get_triggered_input(id):
	return p.get_triggered_inputs(id)

def format_float(input_data):
	return float("{0:.2f}".format(input_data))

def stream_sensor(limit = 10000):
	print "\n_____________________________________________________________\n",
	print "Timer\t|P1\t|P2\t|Col\t|Res\t|PosC\t|PosM\t|Breach"
	print "_____________________________________________________________\n",
	data_0 = []
	data_1 = []
	data_2 = []
	data_3 = []
	data_4 = []
	data_5 = []
	data_6 = []
	while(limit>0):
		data=["NA"]*7
		data[0]=float("{0:.2f}".format(p.read_pressure_sensor(0)))
		data[1]=float("{0:.2f}".format(p.read_pressure_sensor(1)))
		data[2]=int(p.read_collision_sensor())
		data[3]=int(p.read_dllt_sensor())
		data[4]=int(p.get_encoder_position(0))
		data[5]=float("{0:.1f}".format(p.get_encoder_position(0)/stem_eng))
		data[6]=p.read_breach_capacitance()

		data_0.append(data[0])
		data_1.append(data[1])
		data_2.append(data[2])
		data_3.append(data[3])
		data_4.append(data[4])
		data_5.append(data[5])
		data_6.append(data[6])

		a= "\t|".join([str(x) for x in data])
		a= str(limit)+'\t|'+str(a)
		try:
			if limit==1:
				print " %s \r" % a
			else:
				print " %s \r" % a,
				time.sleep(0.1)
				sys.stdout.flush()

		except KeyboardInterrupt:
			#sys.stdout.flush()
			print " %s \r" % a
			break
		limit-=1
	P1_avg = format_float(sum(data_0)/len(data_0))
	P2_avg = format_float(sum(data_1)/len(data_1))
	Col_avg = int(sum(data_2)/len(data_2))
	Res_avg = int(sum(data_3)/len(data_3))
	Br_avg = int(sum(data_6)/len(data_6))

	all_sensor = [P1_avg,P2_avg,Col_avg,Res_avg,Br_avg]
	return all_sensor

def resistance_check(win = 100):
	freq = [2000,510,120]
	val = []
	for i in freq:
		r = []
		p.set_AD9833_Frequency(i)
		time.sleep(1)
		for x in range(win):
			r.append(p.read_dllt_sensor())
		r_av = int(sum(r)/float(len(r)))
		dev = max(r)-min(r)
		val.append(r_av)
		val.append(dev)
		print str(i)+' hz\t: '+str(r_av)+'\tdev\t: '+str(dev)
	return val

def get_motor_pos():
	pos = p.get_encoder_position(0)/stem_eng
	pos = format_float(pos)
	return pos

def set_ejector(duty,timeout):
	p.set_ejector(duty,timeout)
def clr_ejector():
	p.clr_ejector()

class PicktipConfig:
	firstMoveAcc = 1000
	firstMoveVel = 80
	secondMoveAcc = 300
	secondMoveVel = 3
	picktipRetractAccel = 1000
	picktipRetractVel = 100
	picktipSafeRetractDist = 60
	waitPosOffset = 5
	delayBeforeValidate = 100/1000
	abortColThres = 100
	firstCurrentThres = 2.5
	secondCurrentThres = 2
	secondMoveDist = 13.8
	tipPosTolerance = 2.8
	thirdCurrentThres = 1
	freq = 1500
	freq_delay = 250/1000
	folErrorLimit = 1000
	targetReachedWindow = 100
	flow = 150
	collisionCompressTolerance = 4
	validColMin = 1000
	validColMax = 3000
	validResMin = 50
	validResMax = 12000
	validSampleNum = 5
	validSamplingDelay = 20
	validPress2Limit = {20 : {'min':-6.0, 'max':20.0},
						200: {'min':-6.0, 'max':15.0}}

def setUp_picktip(targetZ, safeZ, tip=20):
	p.get_fol_error_config(0)
	p.set_fol_error_config(0,True,PicktipConfig.folErrorLimit)
	p.get_target_reached_parameter(0)
	p.set_target_reached_parameter(0, PicktipConfig.targetReachedWindow, 0)
	p.start_regulator_mode(2,PicktipConfig.flow,1,0,0)
	set_freq(PicktipConfig.freq,freq_delay)
	targetZ -= PicktipConfig.collisionCompressTolerance
	firstmove, secondmove = False, False
	firstmove = picktip_firstmove(targetZ)
	if firstmove:
		secondmove = picktip_secondmove(safeZ,tip)
		if secondmove: return True
	else: return False

def picktip_firstmove(targetZ):
	colThres = c.p.read_dllt_sensor() - PicktipConfig.abortColThres
	p.set_abort_threshold(InputAbort.CollisionTouch, colThres)
	p.set_abort_threshold(InputAbort.CurrentMotorZ, PicktipConfig.firstCurrentThres)
	collision = 1 << InputAbort.CollisionTouch
	current = 1 << InputAbort.CurrentMotorZ
	HardZ_triggerOnAll = False
	HardZ_abortDelay = 0
	p.set_abort_config(AbortID.HardZ,HardZ_triggerOnAll,current+collision,collision,HardZ_abortDelay)
	if move_abs_z(targetZ*stem_eng, PicktipConfig.firstMoveVel*stem_eng, PicktipConfig.firstMoveAcc*stem_eng):
		clear_abort_config(AbortID.HardZ)
	status = p.get_triggered_inputs(AbortID.HardZ)
	if status == (1 << InputAbort.CollisionTouch): return True		
	else: return False

def picktip_secondmove(targetZ,tip=20):
	p.set_abort_threshold(InputAbort.CurrentMotorZ, PicktipConfig.secondCurrentThres)
	current = 1 << InputAbort.CurrentMotorZ
	HardZ_triggerOnAll = False
	HardZ_abortDelay = 0
	p.set_abort_config(AbortID.HardZ, HardZ_triggerOnAll, current, current, HardZ_abortDelay)
	if move_abs_z(targetZ*stem_eng,PicktipConfig.secondMoveVel*stem_eng,PicktipConfig.secondMoveAcc*stem_eng):
		clear_abort_config(AbortID.HardZ)
	status = p.get_triggered_inputs(AbortID.HardZ)
	if status == (1 << InputAbort.CurrentMotorZ):
		clear_abort_config(AbortID.HardZ)
		pos = p.get_motor_pos(0)/stem_eng
		targetRetractPos = pos + PicktipConfig.picktipSafeRetractDist
		move_abs_z(targetRetractPos, PicktipConfig.picktipRetractVel*stem_eng, PicktipConfig.picktipRetractAccel*stem_eng)
	clear_abort_config(AbortID.HardZ)
	pos = p.get_motor_pos(0)/stem_eng
	targetRetractPos = pos + PicktipConfig.picktipSafeRetractDist
	time.sleep(PicktipConfig.delayBeforeValidate)
	press2, col, res = 0,0,0
	p2Valid, colValid, resValid = False, False, False
	for i in range(PicktipConfig.validSampleNum):
		press2 += p.read_pressure_sensor(2)
		col += p.read_collision_sensor()
		res += p.read_dllt_sensor()
		time.sleep(PicktipConfig.validSamplingDelay)
	global ATM_pressure
	press2 /= PicktipConfig.validSampleNum
	p2min, p2max = PicktipConfig.validPress2Limit[tip]['min'], PicktipConfig.validPress2Limit[tip]['max']
	delta_press = press2 - ATM_pressure
	p2Valid = p2min <= delta_press <= p2max
	col /= PicktipConfig.validSampleNum
	colValid = PicktipConfig.validColMin <= col <= PicktipConfig.validColMax
	res /= PicktipConfig.validSampleNum
	resValid = PicktipConfig.validResMin <= res <= PicktipConfig.validResMax
	print"p2Valid: {}, colValid: {}, resValid: {}".format(p2Valid,colValid,resValid)
	if p2Valid and colValid and resValid: return True
	else: return False

p20targetpick= -139
p200targetpick= -129 #50,2
def picktip(target=-114,col=50,curr=1.2,saferet=30):
	tolerance_res = [80,200]
	firstmove, secondmove,res_check = False,False,False


	#print 'picktip'
	p.set_AD9833_Frequency(2000)
	time.sleep(0.2)
	resA = 0
	for i in range(6):
		resA+=p.read_dllt_sensor()
	resA = resA/6
	set_picktip_abort(col,curr)
	move_abs_z(target+1,50,500)
	status1  = get_triggered_input(1)
	if status1 != 8:
		print 'collision not triggered'
		firstmove = False
		clear_abort_config(1)
		move_abs_z(target+20,50,500)
	else:
		firstmove = True

	#print 'firstmovedone',firstmove, status1

	if firstmove:
		clear_abort_config(1)
		set_current_abort(2)
		move_abs_z(target,50,500)
		status2  = get_triggered_input(1)
		print '2nd move done',status2
		if status2 == 1<<7:
			print 'current limit triggered'
			secondmove = False
			clear_abort_config(1)
			move_abs_z(target+50,50,500)
		else:
			secondmove = True
			#print 'picktip success'
			clear_abort_config(1)
			move_abs_z(target+saferet,50,500)
	resB = 0
	if secondmove:


		for i in range(6):
			resB+=p.read_dllt_sensor()
		resB = resB/6
	res = resA-resB

	if tolerance_res[0] < res < tolerance_res[1]:
		res_check = True
	#if firstmove and secondmove and res_check:
		#print 'Picktip Success'
	p.set_AD9833_Frequency(100)
	return [firstmove,secondmove,res_check]

def eject(dist=8,duty=1,timeout=5000):
	#move_abs_z(initialpos,50,500)
	#time.sleep(0.3)
	#print "eject"
	#move_rel_z(3,50,500)
	set_ejector(duty,timeout)
	time.sleep(0.5)
	move_rel_z(dist,100,1000)
	time.sleep(0.1)
	move_rel_z(-1*dist,50,500)
	clr_ejector()

def config_status():
	print 'belum'

def start_flow(flow,delay=250/1000.0):
	p.start_regulator_mode(2,flow,1,0,0)
	time.sleep(delay)

def release_to_atm(prints=False):
	p.set_valve(1)
	time.sleep(5)
	abort_flow()

def leak_press():
	global pipetting_done_req
	global  tare_done_req
	pipetting_done_req = False
	tare_done_req = False
	limit = 200

	release_to_atm()
	time.sleep(5)
	abort_flow()
	tare_pressure()
	p.set_regulator_p1_limits(ATM_pressure+limit,ATM_pressure-limit)
	dispense(100,150,150,0,100)
	P1start = format_float(p.read_pressure_sensor(0))
	P2start = format_float(p.read_pressure_sensor(1))

	if P1start < ATM_pressure+limit-10 or P2start < ATM_pressure+limit-10:
		start_status = False
	else:
		start_status = True

	print 'Start press: ', P1start,P2start
	start = time.time()
	end = 0
	while(end<60):
		time.sleep(0.01)
		end = time.time()-start
		P1 = format_float(p.read_pressure_sensor(0))
		P2 = format_float(p.read_pressure_sensor(1))
		progress = str(int(end/60*100))+'%'
		stat = 'Progress : '+progress+'\t'+str(P1)+'\t'+str(P2)
		print_flash(stat)
		if start_status == False: break


	print "----------------------------------------------------------------"
	leak_rate1 = (P1start-p.read_pressure_sensor(0))*60/end
	leak_rate2 = (P2start-p.read_pressure_sensor(1))*60/end
	leak_rate = format_float(max(leak_rate1,leak_rate2))
	if leak_rate <5 and start_status == True: status = True
	else: status = False
	print 'Leak rate\t: '+str(leak_rate)+' / min -- '+str(status)
	release_to_atm()
	time.sleep(3)
	abort_flow()

	pipetting_done_req = True
	tare_done_req = True
	p.set_regulator_p1_limits(ATM_pressure+limit,ATM_pressure-limit)
	return status,leak_rate

def leak_vac():
	global pipetting_done_req
	global tare_done_req
	pipetting_done_req = False
	tare_done_req = False

	limit = 200
	release_to_atm()
	time.sleep(5)
	abort_flow()
	tare_pressure()
	p.set_regulator_p1_limits(ATM_pressure+400,ATM_pressure-400)
	aspirate(100,150,150,0,100)
	P1start = format_float(p.read_pressure_sensor(0))
	P2start = format_float(p.read_pressure_sensor(1))

	if P1start > ATM_pressure-limit+10 or P2start > ATM_pressure-limit+10:
		start_status = False
	else:
		start_status = True

	print 'Start press: ', P1start,P2start
	start = time.time()
	end = 0

	while(end<60):
		time.sleep(0.01)
		end = time.time()-start
		P1 = format_float(p.read_pressure_sensor(0))
		P2 = format_float(p.read_pressure_sensor(1))
		progress = str(int(end/60*100))+'%'
		stat = 'Progress : '+progress+'\t'+str(P1)+'\t'+str(P2)
		print_flash(stat)
		if start_status == False: break


	print "----------------------------------------------------------------"
	leak_rate1 = (p.read_pressure_sensor(0)-P1start)*60/end
	leak_rate2 = (p.read_pressure_sensor(1)-P2start)*60/end
	leak_rate = format_float(max(leak_rate1,leak_rate2))
	if leak_rate <5 and start_status == True: status = True
	else: status = False
	print 'Leak rate\t: '+str(leak_rate)+' / min -- '+str(status)
	release_to_atm()
	time.sleep(3)
	abort_flow()
	pipetting_done_req = True
	tare_done_req = True
	return status,leak_rate

def find_min_col(n=15):
	start = time.time()
	end = 0
	init_val = p.read_collision_sensor()

	print "Initial\t: ",init_val

	min_val = init_val
	while (end<n):
		a = p.read_collision_sensor()
		if a < min_val:
			min_val = a
		end = time.time()-start
		print_flash(a)

	print '---------------------------'
	print 'Minimum value collision sensing :',min_val


def max_current():
	done = False
	home_z()


	init = p.read_current_sense(0)
	max_cur = init
	min_cur = init
	n=0
	for i in range(0,10):
		move_abs_z(-130,100,1000,0)
		while(move_done==False):
			a = abs(p.read_current_sense(0))
			if a>max_cur:
				max_cur = a

		time.sleep(0.5)
		move_abs_z(0,100,1000,0)
		while(move_done==False):
			a = abs( p.read_current_sense(0))
			if a>max_cur:
				max_cur = a

		time.sleep(0.5)

	print "max_curr: ",max_cur
	return max_cur

def get_motor_pos():
	pos = p.get_encoder_position(0)/stem_eng

	return pos

def set_freq(freq,delay=250/1000.0):
	p.set_AD9833_Frequency(freq)
	time.sleep(delay)

def DLLT_chek(freq=120):
	set_freq(freq)
	start_val = p.read_dllt_sensor()
	start_pos = get_motor_pos()
	res_diff=[0]
	depth = [0]
	start_logger(MotorMask.PosActual,SensorMask.LiquidLevelSensor)
	for i in range(0,4):
		move_rel_z(-0.5,1,10)
		time.sleep(0.2)
		depth.append(format_float(start_pos-get_motor_pos()))
		res_diff.append(int((start_val-p.read_dllt_sensor())))
	stop_logger()
	correl = format_float(corrcoef(depth,res_diff)[0,1])
	m = calculate_linear_scale_offset(depth,res_diff)
	m = [format_float(m[0]),format_float(m[1])]
	print res_diff,depth
	print 'Resistance function to depth : ',m
	print 'Linearity : ', correl
	return correl

def plld(depth=-10,speed=15,acc=500):
	#clear_motor_fault()
	#clear_abort_config()
	tare_pressure()
	#start_logger(256,38)
	start_flow(15)
	#time.sleep(0.1)
	set_plld()
	move_abs_z(depth,speed,acc)
	#stop_logger()
	pos =  get_motor_pos()
	sensor =  get_triggered_input(1)
	abort_flow()
	clear_motor_fault()
	clear_abort_config(1)
	clear_abort_config(6)
	return sensor,pos

def wlld(depth=-10,speed=15,acc=500):
	clear_motor_fault()
	clear_abort_config()
	set_wlld_abort(100)
	#set_collision_abort(30)
	move_rel_z(depth,speed,acc)
	#stop_logger()
	pos =  get_motor_pos()
	sensor =  get_triggered_input(1)

	clear_motor_fault()
	clear_abort_config(1)
	clear_abort_config(6)
	if (sensor == 8 or sensor==264 or  sensor==128):
		print "collision detected"
		move_rel_z(3,500,500)
	return sensor,pos

def DLLT_start(reverse=0,freq=510):
	set_collision_abort(40)
	set_freq(freq)
	val1 = p.read_dllt_sensor()

	move_rel_z(-1,10,1000)
	if get_triggered_input(1) !=0:
		clear_abort_config(1)
		move_rel_z(1,10,500)
	time.sleep(0.5)
	val2 = p.read_dllt_sensor()
	#print val1,val2
	p.set_dllt_move_profile(40*stem_eng,10000*stem_eng,False)
	p.set_dllt_pid(5,5,10,15)
	threshold = (val2-val1) / 4
	diff = val2-val1
	print 'Threshold:', threshold
	if threshold > -20:
			#cancel
			threshold = -250
			print("\n  Geometric LLT Start")
	#else:
		#print("\n  Resistnce LLT Start")
	if reverse:
		threshold = 1000
		print 'run reverse========================='
	p.start_dllt(threshold,0.3,1)
	clear_abort_config(1)

	return True,threshold,freq

def DLLT_stop():
	clear_motor_fault()
	clear_abort_config(1)
	p.stop_dllt()

def leak_v20(limits=[100],dur=60):
	#for FW 0.8.15
	global pipetting_done_req
	global  tare_done_req
	pipetting_done_req = False
	tare_done_req = False


	mode = [1,-1]
	vac_result = []
	press_result = []
	result = [None]*2
	n=0
	release_to_atm()
	tare_pressure()
	atm = ATM_pressure
	p.start_regulator_mode(0,ATM_pressure+(1*limits[0]),1,0,0)
	time.sleep(3)
	dead_vol = 1#count_vol(0)
	tare_pressure()

	print "Atm: ", atm
	for i in mode:
		for x in limits:
			release_to_atm()
			abort_flow()
			tare_pressure()
			p.start_regulator_mode(0,ATM_pressure+(i*x),1,0,0)
			time.sleep(3)
			abort_flow()
			time.sleep(0.2)

			average_pressure(200)

			P1start = format_float((AverageP1-atm))
			P2start = format_float((AverageP2-atm))
			start = time.time()
			end = 0

			print 'Initial : ', P1start,P2start
			while(end<dur):
				if not(i*x-50< P1start < i*x+50 and i*x-50< P2start < i*x+50):
					print 'Pressure/Vaccum not reach'
					print P1start,'/',x,'\t',P2start,'/',x
					start_status = False
					break
				else:
					start_status = True
				time.sleep(0.5)
				end = time.time()-start
				P1 = format_float((p.read_pressure_sensor(0)-atm))
				P2 = format_float((p.read_pressure_sensor(1)-atm))
				progress = str(int(end/60*100))+'%'
				stat = 'Progress '+str(n+1)+'/'+str(len(mode)*len(limits))+  ' :' +progress+'\t'+str(P1)+'\t'+str(P2)

				print_flash(stat)

			average_pressure(200)
			P1end = format_float(AverageP1-atm)
			P2end = format_float(AverageP2-atm)

			leak_rate1 = abs(dead_vol*(P1start-P1end)*60/end) if end>0 else 999
			leak_rate2 = abs(dead_vol*(P2start-P2end)*60/end) if end>0 else 999
			leak_rate = format_float(max(leak_rate1,leak_rate2))


			if leak_rate <10 and start_status == True: status = True
			else: status = False
			print ' '
			print 'Leak rate : ', leak_rate
			print 'Status : ', status
			print ' '



			mode_r = i
			limit_r = x
			start_r = [P1start,P2start]
			start_stat_r = start_status
			end_r = [P1end,P2end]
			rate_r = leak_rate
			sum_r = status

			result[n] = [mode_r,limit_r,start_r,start_stat_r,end_r,rate_r,sum_r]
			n += 1

	print 'Leak rate pressure\t: '+str(result[0][5])+' mbar/min at ',str(result[0][2][0])+' mbar'
	print 'Leak rate vacuum\t: '+str(result[1][5])+' mbar/min at ',str(result[1][2][0])+' mbar'
	pipetting_done_req = True
	tare_done_req = True

	return result
def count_vol(mode):
	#tare_pressure()
	global Count_volume_done
	Count_volume_done = False
	p.count_volume(mode)
	while(not Count_volume_done):
		pass
	abort_flow()
	print Sensed_vol
	return Sensed_vol

####################################################################################################################

def help(arg):
	if arg:
		if str(arg):
			if arg == 'plate':
				pass
			elif arg == 'gravi' or arg == 'gravimetric':
				pass
		else:
			print "Please use ''"
	else:
		print 'Help is not available now, please contact the developer '
