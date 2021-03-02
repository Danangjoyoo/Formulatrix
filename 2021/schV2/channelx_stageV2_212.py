from path import*
import time
from numpy import corrcoef
import numpy as np, pandas as pd
import threading
from subprocess import call
from winsound import Beep
from math import pi
import imp
from pandas import read_csv
from port import Device
import keyboard as kb, colorama as cora
from collections import OrderedDict as ordict
from visualize import *


address = 30
stem_eng = 5.0

p = Device(address)
p.connect()


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
class SensorMask:
	NOTHING 			= 0
	DLLT_RESISTANCE 	= 1
	COLLISION			= 2
	NTC_TEMP1 			= 4
	NTC_TEMP2 			= 8
	PRESSURE_P1 		= 16
	PRESSURE_P2 		= 32
	TEMP_P1				= 64
	TEMP_P2				= 128
	PIPETTING_RUN		= 256
	VALVE_IN_OPEN		= 512
	PIPETTING_FLOW		= 1024
	PREG_CONTROL_OUT	= 2048
	PIP_TARGET_FLOW		= 4096
	PIPETTING_VOL		= 8192
	COUNTER				= 16384

class SensorID:
	DLLT_RESISTANCE		= 0
	COLLISION 			= 1
	NTC_TEMP1 			= 2
	NTC_TEMP2 			= 3
	TEMP_P1 			= 4
	TEMP_P2 			= 5
	PRESSURE_P1 		= 6
	PRESSURE_P2 		= 7
	BREACH_CAPC 		= 8

class MotorMask:
	NOTHING 		= 0
	VELOCITY		= 1
	POS_COMMAND		= 2
	POS_ENCODER		= 4
	POS_ERROR		= 8

class AbortID:
	MOTORDECEL 		= 0
	MOTORHARDBRAKE  = 1
	ESTOP 			= 2
	TOUCHOFF 		= 3
	VALVEDRAIN 		= 4
	VALVECLOSE 		= 5
	PIPBREACHBLOW 	= 6

class InputAbort:
	MOTORFAULT 	= 0
	ESTOP 		= 1
	TOUCHOFF 	= 2
	BREACH 		= 3
	RESISTANCE 	= 4
	COLLISION1 	= 5
	COLLISION2	= 6
	NTEMP1 		= 7
	NTEMP2 		= 8
	PTEMP1 		= 9
	PTEMP2 		= 10
	PRESS1		= 11
	PRESS2		= 12

	
STRING_SENSOR_MASK = [
	"DlltResistance",
	"Collision",
	"NTC_Temp1",
	"NTC_Temp2",
	"Pressure_P1",
	"Pressure_P2",
	"Temp_P1",
	"Temp_P2",
	"Pipetting_run",
	"Valve_in_open",
	"Pipetting_flow",
	"Preg_control_out",
	"Pipetting_volume",
	"Counter"
	]
	
SCALE_OFFSET_SENSOR = [
	[0.1  , 0.0     ],
	[0.1  , 0.0     ],
	[0.01 , 0.0     ],
	[0.01 , 0.0     ],
	[0.1  , 0.0     ],
	[0.1  , 0.0     ],
	[0.01 , 0.0     ],
	[0.01 , 0.0     ],
	[1.0  , 0.0     ],
	[1.0  , 0.0     ],
	[0.01 , -32768.0],
	[0.001, -32768.0],
	[0.01 , -32768.0],
	[0.01 , -32768.0],
	[1.0  , 0.0     ]
]

STRING_MOTOR_MASK = [
	"Velocity",
	"Pos_command",
	"Pos_encoder",
	"Pos_error"
	]

SCALE_OFFSET_MOTOR = [
	[0.1  , -32768.0],
	[0.1  , -32768.0],
	[0.1  , -32768.0],
	[0.001, -32768.0]
]

def chunks(l, n):
	n = max(1, n)
	return [l[i:i + n] for i in range(0, len(l), n)]


thread_run = True

def chunks(l, n):
	n = max(1, n)
	return [l[i:i + n] for i in range(0, len(l), n)]

thread_run = True

def start_logger(motorm=0,sensorm=16+32,openui=True,maxTick=None):
	global thread_run
	thread_run = True
	thread1 = threading.Thread(name='logger 1', target=thread_logger, args=(motorm,sensorm,openui,maxTick))
	thread1.start()
	print("Logger Started..")

def stop_logger():
	global thread_run
	p.stop_log()
	thread_run = False
	print("Logger Stopped..")

file_name =  None
def thread_logger(motorm=0,sensorm=16+32,openui=True,maxTick=None):
	global thread_run,file_name
	scale = []
	offset = []
	p.set_log_items(motorm,sensorm)
	p.start_log()
	t = time.time()
	file_name = 'FirmwareLog/data_log_' + str(address) + '_' + time.strftime('%Y%m%d%H%M%S', time.localtime(t)) + '.csv'
	with open(file_name, 'w') as f:
		header = "Tick,"
		sum = 0
		items = p.get_log_items()['motor0_mask']
		for x in range(0, 15):
			if ((1 << x) & items) != 0:
				header += STRING_MOTOR_MASK[x] + ","
				sum = sum + 1
				scale.append(SCALE_OFFSET_MOTOR[x][0])
				offset.append(SCALE_OFFSET_MOTOR[x][1])
		items = p.get_log_items()['sensor_mask']
		for x in range(0, 15):
			if ((1 << x) & items) != 0:
				header += STRING_SENSOR_MASK[x] + ","
				sum = sum + 1
				scale.append(SCALE_OFFSET_SENSOR[x][0])
				offset.append(SCALE_OFFSET_SENSOR[x][1])
		all_data = []
		header += "\n"
		f.write(header)
		while thread_run:
			if maxTick:
				if len(all_data) >= 2*maxTick: 
					stop_logger()
					break
			get_data = p.read_log_stream_data()['data']
			all_data += get_data
			time.sleep(0.01)
		while(1):
			get_data = p.read_log_stream_data()['data']
			all_data += get_data
			if len(get_data) == 0:
				print("all data: ",len(all_data))
				break
			if maxTick: 
				if len(all_data) >= maxTick: break
			time.sleep(0.01) 
		data = chunks(all_data, sum)
		data_length = len(data)
		for i in range(data_length):
			if maxTick:
				if i >= maxTick: break
			line = str(i) + ","
			for j in range(len(data[i])):
				line += str( (data[i][j] + offset[j]) *  scale[j]) + ", "
			line += "\n"
			#print 'sensordata', line
			f.write(line)
		f.close()
	if openui: call(["..\Include\log_plot.exe", file_name])

#------- End Logger ---------------

# =========================================== EVENT =========================================================================================
def motor_status():
	print(decode_motor_status(p.get_motor_status))


def decode_motor_status(motor_status):
	if(motor_status==0):
		return "no error"
	else:
		string_array_status=["moving","homing","homed", "ScLowLimit", "ScUpLimit", "ScOvCurrent","ScAborted","ScFolErrIdle","ScFolErrMov","ScEncErr","MtrDsbld","MtrEmergncyStp","HardBrake","MtrDrvFault","stalled"] 
		string_status=""
		for i in range(16):
			if( (motor_status>>i) & 1):
				string_status+=string_array_status[i]
	return string_status
		
def decode_motor_error(motor_error_code):
	string_array_status=[" no error "," invalid motor id "," lower limit reached ", " upper limit reached ", " illegal position ", " illegal velocity "," illegal acceleration "," motor aborted  "," following error idle "," following error moving "," encoder error "," motor disabled "," motor homing "," emergency stop "," hard break "," driver fault "," no move "," move not supported "," illegal jerk "," motor stall "] 
	if(motor_error_code<20):
		return string_array_status[motor_error_code]
	else:
		return "unknown error"

def handle_motor_move_started(motor_id):
	print("Motor Move Started on id " + str(motor_id))

def handle_motor_error_occured(motor_id, motor_error_code):
	global motor_error
	print("Motor Error id=" + str(motor_id) + ", Status=" + decode_motor_error(motor_error_code))
	motor_error = True

def handle_move_done(motor_id,status,position):
	global move_done
	print("Move Done:id=" + str(motor_id) + ", Status=" + str(status) + ", position=" + str(position))
	move_done = True

def handle_home_done(motor_id,home_pos,pos):
	global home_done
	print("Home Done on Motor:" + str(motor_id) + ", Home Pos=" + str(home_pos) + ", pos=" + str(pos))
	home_done = True
	
def handle_on_input_changed(input_id, is_on):
	print("Input changed on:" + str(input_id) + ", is On =" + str(is_on))

def handle_on_sensor_out_of_bounds(id, limit_type, value):
	print("Sensor Out of Bounds, id=",id," limit type =",limit_type," Value=", value)

def handle_on_liquid_level_tracker_stop(mode, status):
	print("Liquid level tracker stopped mode=", mode, ", Status=", status)

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
		print("Tare Done:")
		print("	ATM=" + str(atm_pressure))
		print("	dp_offset=" + str(Dp_Offset))
		print("	temp1=" + str(Temp_P1))
		print("	temp2=" + str(Temp_P2))
		print("	cal_asp=" + str(cal_asp))
		print("	cal_dsp=" + str(cal_dsp))
		global Target_flow
	else:
		print('*** evt: Tare done--')
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

		print("Calibrate finish:")
		print("	P1 = " + str(Press_P1))
		print("	P2 = " + str(Press_P2))
		print("	dp = " + str(Press_Dp))
		print("	T1 = " + str(Temp_P1))
		print("	T1 = " + str(Temp_P2))
	else:
		print("calibrate fail")
	Calibrate_done = True

def handle_vol_count_finish(total_time_ms, sens_vol):
	global Total_time_ms
	global Sensed_vol
	global Count_volume_done
	Total_time_ms = total_time_ms
	Sensed_vol= sens_vol
	print("Volume Count finish:")
	print("	Total Time = " + str(Total_time_ms))
	print("	Sens Vol = " + str(Sensed_vol))
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
		print("Pipetting Done:")
		print("	total time = " + str(Total_time_ms))
		print("	Alc time = " + str(Alc_time_ms))
		print("	Sampling vol = " + str(Sampling_vol))
		print("	Total Sampling = " + str(Total_sampling))
		print("	Last Flow = " + str(Last_flow))
		print("	P1 Off = " + str(P1_off))
		print("	P2 Off = " + str(P2_off))
		print("	Residual vacuum = " + str(Res_vacuum))
		print("	Selected P2 = " + str(Selected_p2))
		print("	Tau Time = " + str(Tau_time))
		print("	Pressure Peak = " + str(Pressure_peak))
		print("	Average Window = " + str(Avg_window))
		print("	Slope Window = " + str(Slope_window))
		print("	Threshold = " + str(Threshold))
		print("	Sensed volume = " + str(Sensed_vol))
	else:
		print('*** evt: Pipetting done--')
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
			print("Pipetting Error:")
			print("	1 Pipetting Error code\t= " + str(ALC_error_code))
			print("	2 Sampling vol\t\t= " + str(Sampling_vol))
			print("	3 Total Sampling\t= " + str(Total_sampling))
			print("	4 Last Flow\t\t= " + str(Last_flow))
			print("	5 P1 Off\t\t= " + str(P1_off))
			print("	6 P2 Off\t\t= " + str(P2_off))
			print("	7 Residual vacuum\t= " + str(Res_vacuum))
			print("	8 Selected P2\t\t= " + str(Selected_p2))
			print("	9 Tau Time\t\t= " + str(Tau_time))
			print("	10 Pressure Peak\t= " + str(Pressure_peak))
			print("	11 Average Window\t= " + str(Avg_window))
			print("	12 Slope Window\t\t= " + str(Slope_window))
			print("	13 Threshold\t\t= " + str(Threshold))
			print("	14 Sensed volume\t= " + str(Sensed_vol))
		else:
			print('*** evt: Pipetting Error--')

		Alc_time_ms = 'N/A'
		Sampling_vol = 'N/A'

		Pipetting_done = True
		Pipetting_error = True
		p.stop_liquid_tracker()


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
	print("Regulate pressure function aborted by vol limit")
def handle_motor_move_started(motor_id):
	print("Motor Move Started on id " + str(motor_id))

def handle_on_regulate_pressure_limit_reach():
	print("Regulate pressure function volume reached")

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
	print("air transfer detected flow =", flow, ", time=", time_ms)
	phase1_air_tr = True
	
	

def handle_on_clog_detected(flow, time_ms):
	print("clog detected flow =", flow, ", time=", time_ms)

#============== INIT ================================================================================================

p.motor_move_started 				+= handle_motor_move_started
p.motor_move_done 				+= handle_move_done 
p.motor_home_done 				+= handle_home_done
p.motor_error_occured 				+= handle_motor_error_occured
p.on_tare_done 					+= handle_tare_done
p.on_calibrate_finish 				+= handle_calibrate_finish
p.on_count_vol_done 				+= handle_vol_count_finish
p.on_pipetting_done 					+= handle_pipetting_done
p.on_average_done 					+= handle_average_done
p.on_pipetting_error 				+= handle_pipetting_error
p.on_regulate_pressure_limit_reach 		+= handle_on_regulate_pressure_limit_reach
#p.on_average_clog_detect_finish 		+= handle_on_average_clog_detect_finish
p.on_valve_closed 					+= handle_on_valve_closed
#p.on_air_transfer_detected 			+= handle_on_air_transfer_detected
#p.on_clog_detected 					+= handle_on_clog_detected
#p.on_liquid_level_tracker_stop 			+= handle_on_liquid_level_tracker_stop
p.on_input_changed 					+= handle_on_input_changed
p.on_sensor_out_of_bound 			+= handle_on_sensor_out_of_bounds
#p.motor_target_reached +=handle_target_reach
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
	p.home_motor(0,0,1,1,10,50,500, 1000)
	status=1
	while (status & 1):
		status=p.get_motor_status(0)
		#print p.get_motor_pos(0)
		#print p.get_encoder_position(0)

def move_abs_z(abs,velc,acc,wait=1):	
	#clear_motor_fault()
	#clear_estop()
	global move_done
	move_done = False
	pos = p.get_motor_pos(0)['curr_pos']/stem_eng
	upper = pos+2
	lower = pos-2
	
	if abs > chipCalibrationConfig.upperLimit: abs = chipCalibrationConfig.upperLimit
	elif abs < chipCalibrationConfig.lowerLimit: abs = chipCalibrationConfig.lowerLimit

	if lower<abs<upper:
		move_done = True
	p.move_motor_abs(0,abs*stem_eng,velc*stem_eng,acc*stem_eng,10000*stem_eng)
	
	if not move_done and wait==1:
		n=0
		while(move_done==False):
			n+=1
			time.sleep(0.1)
	return True

def move_rel_z(rel,velc,acc,wait=1):	
	#clear_motor_fault()
	#clear_estop()
	target_pos = (p.get_motor_pos(0)['curr_pos'] /stem_eng)  + rel
	if target_pos > 0: target_pos = 0
	elif target_pos < -200: target_pos = -200
	move_abs_z(target_pos,velc,acc,wait)

def tare_pressure():
	abort_flow()
	global Tare_done
	Tare_done = False
	p.tare_pressure()
	while(1):
		time.sleep(0.01)
		if Tare_done:
			break
	if abs(Dp_Offset) > 3:
		return False
	if ATM_pressure < 925:
		return False
	if ATM_pressure > 940:
		return False
	return True

def average_pressure(sample):
	#print "Averaging BEGIN"
	global Average_done
	global AverageP1, Max_p1, Min_p1
	global AverageP2, Max_p2, Min_p2
	Average_done = False
	p.averaging_pressure(sample)
	while(1):
		time.sleep(0.1)
		if Average_done:
			break
	time.sleep(1)
	pressurePack = {
		'p1':{
			'average' 	: AverageP1,
			'max' 		: Max_p1,
			'min'		: Min_p1},
		'p2':{
			'average' 	: AverageP2,
			'max' 		: Max_p2,
			'min'		: Min_p2}}
	print('AverageP1:', AverageP1)
	print('Max P1 	:', Max_p1)
	print('Min P1 	:', Min_p1)
	print('AverageP2:', AverageP2)
	print('Max P2 	:', Max_p2)
	print('Min P2 	:', Min_p2)
	print("Averaging Pressure Done!")
	return pressurePack

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
			print("timeout wait")
			break

def calculate_flow(vol,tip):
	MaxFlowScale_P200 = 0.670
	MinFlowScale_P200 = 0.615
	DecelVolScale_P200 = 0.75

predicted_residual = 0
air_phase1 = False
def start_pipetting(vol,flow,flowmin=0,tip=200,timeout=5000,extravol=1):
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
		"AlcTimeoutMs"       : 5000}

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
		"AlcTimeoutMs"       : 5000}
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
	#p.start_pipetting(1, 0, vol, max_flow, min_flow, decel_vol, predicted, dead_vol,p2high_limit, p2low_limit,start_ave_t1_ms,ave_window_p2t1,start_ave_t2_ms,ave_window_p2t2)
	#set_breach_in()
	#p.set_abort_config(AbortID.PIPBREACHBLOW, False, 1<<InputAbort.BREACH, 1<<InputAbort.BREACH)
	p.start_pipetting(extravol, 0, vol, max_flow, min_flow, decel_vol, predicted, dead_vol,p2high_limit, p2low_limit,start_ave_t2_ms,ave_window_p2t2)
	#print max_flow,min_flow,decel_vol
	if air_phase1:
		move_rel_z(5,20,1000,0)
	
	timeout=15 #override khusus gravimetric
	t2 = 0
	while not Pipetting_done:
		t1 = int(time.time()-start)
		if phase2_fly:
			pos = p.get_motor_pos(0)/stem_eng +3
			p.move_motor_abs(0,pos*stem_eng,100*stem_eng,10000*stem_eng)
			#move_rel_z(10,100,10000,1)
			phase2_fly = False
		if (time.time()-start)>=timeout:
			print("Pipetting Timeout!!\n")
			abort_flow()
			Pipetting_done = True
		if t1 != t2:
			t2 = t1; print("{} timeout at {}".format(int(time.time()-start), timeout))

	
	#p.stop_liquid_tracker()
	
def cek_p2_average():
	global No_liquid
	global air_transfer_by_p2
	No_liquid_by_avp2 = False
	No_liquid_by_res= False
	
	if last_vol < 0: #only aspirate case
		No_liquid = ATM_pressure - P2_t1 <= AirTransfer.d 
		No_res = Res_vacuum > -1.
		
		if No_liquid and not phase1_air_tr and not phase2_air_tr : 
			print('aspirate udara')
			No_liquid_by_avp2 = True
			air_transfer_by_p2 += 1	
		if No_res : 
			print('aspirate udara by res')
			No_liquid_by_res= True
			#air_transfer_by_p2 += 1
		return No_liquid_by_avp2 or No_liquid_by_res
			
			
def minicek():
	start_logger()
	start_flow(-20)
	time.sleep(0.5)
	abort_flow()
	start_flow(20)
	time.sleep(0.5)
	abort_flow()
	aspirate(20,20)
	dispense(20,20)
	ready_to_flow()
	p.set_prop_valve_out(0,0.67)
	time.sleep(2)
	abort_flow()
	ready_to_flow()
	p.set_prop_valve_out(1,0.67)
	time.sleep(2)
	abort_flow()
	stop_logger()


def aspirate(vol,flow,flowmin=5,log=False,timeout=5000,tip=200):
	#p.set_abort_config(7,0,512,0,0)
	start = time.time()
	
	if log:
		start_logger(0,SensorMask.PRESSURE_P1+SensorMask.PRESSURE_P2)
		time.sleep(1)
	start_pipetting(-1*vol, flow,flowmin,tip,timeout)
	print(time.time()-start)
	if log:
		stop_logger()
		time.sleep(1)

def dispense(vol,flow,flowmin=5,log=0,timeout= 5000,tip=200):
	if log == 1:
		start_logger()
		time.sleep(1)
	start_pipetting(vol, flow,flowmin,tip,timeout)

	if log == 1:
		time.sleep(1)
		stop_logger()

def dpc_on():
	#start_logger(0,294)
	'''
	Make sure do DPC On after aspirate
	'''
	global AverageP2
	time.sleep(0.2)
	average_pressure(100)
	p_dpc = AverageP2
	vol_limit = 5
	p.start_regulator_mode(1,p_dpc,2,1,vol_limit)

	print("DPC ON at P2 = {}".format(p_dpc))
	return p_dpc

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
	
	#set_breach_in()
	#p.set_abort_config(AbortID.PIPBREACHBLOW, False, 1<<InputAbort.BREACH, 1<<InputAbort.BREACH)
	p.start_pipetting(0, 0, vol, max_flow, min_flow, decel_vol, predicted, dead_vol, p2high_limit, p2low_limit,start_ave_t1_ms,ave_window_p2t1,start_ave_t2_ms,ave_window_p2t2)

	#timeout=2000
	start = time.time()
	end = 0
	while(1):
		#time.sleep(0.01)
		end = time.time()-start
		if Pipetting_done == True:
			print("bar")
			break
		if end==timeout:
			print("Pipetting Timeout!!\n")
			Pipetting_done = True
			abort_flow()

def aspirate_2(vol,flow,log=0,timeout=2000):
	#p.set_abort_config(7,0,512,0,0)
	if log == 1: start_logger()
	time.sleep(1)
	start_pipetting(-1*vol, flow,flow,200,timeout,0)
	time.sleep(1)
	if log == 1: stop_logger()

def dispense_2(vol,flow,log=0,timeout=2000):
	if log == 1: start_logger()
	time.sleep(1)
	start_pipetting(vol, flow,flow,200,timeout,0)
	time.sleep(1)
	if log == 1: stop_logger()


#============== USER FUNCTION ================================================================================================
def set_sensor_config(idx=0):
	get_sensor_config(idx)
	inp = input("ID,New Value >>> ")
	configID = int(inp.split(',')[0])
	value = float(inp.split(',')[1])
	vals = [p.get_sensor_config(idx)[key] for key in p.get_sensor_config(idx).keys()]
	vals[configID] = value
	p.set_sensor_config(idx,*vals)
	p.save_configuration()
	print('saved')

def get_sensor_config(idx=0):
	readConfig(p.get_sensor_config,idx)

def readConfig(*args):
	args = list(args)
	func = args.pop(0)
	if type(func(*args)) == ordict:
		print("==============================")
		print(" ID\tConfig\t\tValue")
		print("==============================")
		for x, key in enumerate(func(*args)):
			if len(key) < 8: print(f' {x}\t{key}\t\t{func(*args)[key]}')
			else: print(f' {x}\t{key}\t{func(*args)[key]}')		
		print("==============================")
	else:
		print(func(*args))

def aspirate_dpc(vol,flow):
	global AverageP1
	aspirate(vol,flow)
	average_pressure(1000)
	p.start_regulator_mode(0,AverageP1)


def solenoid_test(x=150): #fullV2
	print("== SOLENOID HW TEST BEGIN ==")
	#tambah logger valve vs input pressure vac
	for i in range(0,x):
		p.set_valve(1)
		time.sleep(0.25)
		p.set_drain(1)
		time.sleep(0.25)
		p.select_flow_sensor(1)
		time.sleep(0.25)
		p.set_valve(0)
		time.sleep(0.25)
		p.set_drain(0)
		time.sleep(0.25)
		p.select_flow_sensor(0)
		time.sleep(0.25)
		print_flash( "Loop : "+str(i+1)+"/"+str(x))

	print("-- OK --")
	print("== SOLENOID HW TEST END ==")
	beep(1)

def beep(s=1):
	if s==1:
		for i in range(0,3):
			Beep(1000,1000)

	else:
		for i in range(0,20):
			Beep(5000,200)

def config_set(slot = 0,id=None,val=None,ux=True):
	if id != None or val != None: ux = False
	
	param = ['cal_static_asp',
		'cal_static_dsp',
		'flow_drift_asp',
		'flow_drift_dsp',
		'DpHighThreshold',
		'DpLowThreshold',
		'ExtraOffsetAsp',
		'ExtraOffsetDsp',
		'ExtraScaleAsp',
		'ExtraScaleDsp',
		'SlopeThreshold',
		'vicous_scale',
		'viscous_offset',
		'SensorId']
	if ux:
		for x,i in enumerate(param):
			print(x,i)
		id = int(input("param:\t"))
		val = float(input("value:\t"))
	#baru sampe sini
	data= str(p.get_sensor_config(slot))
	print("===============================================================")

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

	if True:#change
		value[id] = val
		p.set_sensor_config(slot,value[0],value[1],value[2],value[3],value[4],value[5],value[6],value[7],value[8],value[9],value[10],value[11],value[12],value[13])
		p.save_configuration()
		print(" ")
		print(">>>> Config Changed <<<<<<")
		print(" ")

		for i in range(0,len(item)):
			if i==id:
				print(item[i]," = ",value[i], " <<<< ")
			else:
				print(item[i]," = ",value[i])

	return value

def calculate_linear_scale_offset(X,Y): #ganti yg lebih simple?
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
	#p.stop_liquid_tracker()

def test_extra_vol_asp2(flows,volume=100):
	global extra_p1_off_asp
	global extra_vol_asp
	global extra_asp
	#volume = 100
	tare_pressure()
	
	extra_p1_off_asp=[]
	extra_vol_asp=[]
	
	
	print("flow: ", flows)
	for flow in flows:
		
		#print "flow:" + str(flow) + ", End Flow:" + str(end_flow)
		tare_pressure()
		print("Generate flow: ",flow)
		aspirate_2(volume,flow)
		time.sleep(2)
		extra_p1_off_asp.append(P1_off)
		extra_vol_asp.append(Sensed_vol+volume)

	print("finish extra aspirate test")
	extra_asp=calculate_linear_scale_offset(extra_p1_off_asp,extra_vol_asp)
	correl = format_float(corrcoef(extra_p1_off_asp,extra_vol_asp)[0,1])

	print(correl)
	extra_p1_off_asp=[]
	extra_vol_asp=[]

def test_extra_vol_dsp2(flows,volume=100):
	global extra_p1_off_dsp
	global extra_vol_dsp
	global extra_disp
	#volume = 100
	extra_p1_off_dsp = []
	extra_vol_dsp = []
	
	tare_pressure()
	print("flow: ", flows)
	for flow in flows:
		
		tare_pressure()
		print("Generate flow: ",flow)
		dispense_2(volume,flow)
		time.sleep(2)
		extra_p1_off_dsp.append(P1_off)
		extra_vol_dsp.append(Sensed_vol-volume)
		

	print("finish extra dispense test")
	extra_disp=calculate_linear_scale_offset(extra_p1_off_dsp,extra_vol_dsp)
	correl = format_float(corrcoef(extra_p1_off_dsp,extra_vol_dsp)[0,1])

	print(correl)
	print(extra_p1_off_dsp)
	print(extra_vol_dsp)
	extra_p1_off_dsp=[]
	extra_vol_dsp=[]

def extra_vol_test(flows=[15,20,50,100,150],volume=100):
	global pipetting_done_req
	global tare_done_req
	pipetting_done_req = False
	tare_done_req = False
	global extra_asp
	global extra_disp
	#config_set(0,8,0)
	#config_set(0,6,0)
	#config_set(0,9,0)
	#config_set(0,7,0) #tidak perlu karna tidak dipakai
	extra_asp = []
	extra_disp = []
	#ereg_source()
	#set_plug(0)
	abort_flow()
	tare_pressure()
	test_extra_vol_asp2(flows,volume)

	print("Ext_asp scale: ",extra_asp[0], " ","offset",extra_asp[1])
	config_set(0,8,extra_asp[0])
	config_set(0,6,extra_asp[1])
	time.sleep(2)

	test_extra_vol_dsp2(flows,volume)
	config_set(0,9,extra_disp[0])
	config_set(0,7,extra_disp[1])

	print("Extra volume test -- DONE --")
	print("Ext_asp scale: ",extra_asp[0], " ","offset",extra_asp[1])
	print("Ext_disp scale: ",extra_disp[0], " ","offset",extra_disp[1])

	extra_asp=[0,0]
	extra_disp=[0,0]

	status = [False,False]
	asp_c = abs(p.get_sensor_config(0)['ExtraScaleAsp']*-0.5+p.get_sensor_config(0)['ExtraOffsetAsp'])
	dsp_c = p.get_sensor_config(0)['ExtraScaleDsp']*0.5+p.get_sensor_config(0)['ExtraOffsetDsp']

	if asp_c < 2:
		status[0] = True
	if dsp_c <2:
		status[1] = True
	pipetting_done_req = True
	tare_done_req = True
	print("Aspirate:", status[0], '---- Dispense:',status[1])
	return status




def valve_bukatutup(a=100):
	for i in range(a):
		p.set_valve(0)
		time.sleep(0.1)
		p.set_valve(1)
		time.sleep(0.1)

def read_breach(iter):

	while(1):
		ready=input("enter jika siap ambil data tanpa liquid ")
		if ready=='':
			break

	print("lanjut")
	baseline=[]
	for i in range(iter*1000):
		baseline.append(p.read_sensor(8))
		time.sleep(0.01)
	baseline=1.0*sum(baseline)/len(baseline)

	print("baseline = ", baseline)

	while(1):
		ready=input("enter untuk lanjut dengan liquid ")
		if ready=='':
			break
	print("lanjut")
	max=[]
	for i in range(iter*1000):
		max.append(p.read_sensor(8))
		time.sleep(0.01)
	max=1.0*sum(max)/len(max)

	print("max = ", max)

	threshold=((max-baseline)/2)+baseline
	print("threshld: ", threshold)
	p.set_breach_threshold(threshold)
	time.sleep(1)
	p.set_breach_threshold(threshold)
	time.sleep(1)
	p.set_breach_threshold(threshold)

	print("threshold set :", p.get_breach_threshold())


def print_flash(a):

	print(" %s \r" % a, end=' ')
	time.sleep(0.1)
	sys.stdout.flush()

def cek_pid_ereg():
	abort_flow()
	tare_pressure()
	status = True
	vol = [10,20,200,]
	flow = [15,20,150]

	for i in range(0,len(vol)):
		start_logger(0,16+32)
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

	id_ = int(input('ID? vac=0, pres=1, dpc=2 : '))
	print(p.get_regulator_pid(id_))
	print('')
	print('Enter to SKIP')
	print('')

	consP = (input('kP : '))
	consP = origin[id_]['kp'] if consP == '' else consP

	consI = (input('kI : '))
	consI = origin[id_]['ki'] if consI == '' else consI

	consD = (input('kD : '))
	consD = origin[id_]['kd'] if consD == '' else consD

	offset = (input('offset : '))
	offset = origin[id_]['o'] if offset == '' else offset

	thdrain= (input('thres drain : '))
	thdrain= origin[id_]['thres_idrain'] if thdrain == '' else thdrain

	iLim = (input('i limit : '))
	iLim = origin[id_]['i_limit'] if iLim == '' else iLim

	p.set_regulator_pid(id_,consP,consI,consD,offset,thdrain,iLim)
	print(p.get_regulator_pid(id_))
	p.save_configuration()



def default_pid_mini():
	set1 = p.get_regulator_pid(1)
	set0 = p.get_regulator_pid(0)
	p.set_regulator_pid(0,0.01,1e-5,0,0,2,2)
	p.set_regulator_pid(1,0.01,1e-5,0,0,2,2)
	print(p.get_regulator_pid(0))
	print(p.get_regulator_pid(1))



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
	print("cek flow start")
	print('ATM: ',format_float(AverageP2))
	print("set out = ",format_float(max))
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

			open = format_float( p.read_sensor(6))
			open2 = format_float(p.read_sensor(7))

			if i == 1 :
				if open>peak[1]: peak[1] = open
				if open2>peak2[1]:peak2[1] = open2
			else :
				if open<peak[0]: peak[0] = open
				if open2<peak2[0]:peak2[0] = open2

			a = side[i]+' >>'+' output: '+str(format_float(p.get_prop_valve_out(i)))+'\tP1: '+str(open)+'\tP2: '+str(open2)
			if x==(50-1): a = a + '---------\n'
			print(" %s \r" % a, end=' ')
			time.sleep(0.1)
			sys.stdout.flush()

		rate[1] = format_float((peak[1]-idle)/ Target_flow_rel[0]*100)
		rate[0] = format_float((idle - peak[0])/ Target_flow_rel[1]*100)

		if rate[1]> 80: status[1] = True
		if abs (rate[0]) > 80: status[0] = True



		if  0 < peak2[1]-idle2 <= 10: status2[1] = True
		if 0 < idle2-peak2[0] <= 10: status2[0] = True

	print('rateP1', str(rate[0])+'%',str(rate[1])+'%')
	print('P1: ', status, 'P2: ',status2)
	print('All should be True to continue')

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
	max_set = 0.55
	max_out = 0.667

	leaks = False
	stuck = False
	state = False

	stuck = not cek_flow()
	time.sleep(2)
	tare_pressure()
	
	range0 = [p.get_prop_valve_range(0)['min_duty'],p.get_prop_valve_range(0)['max_duty']]
	range1 = [p.get_prop_valve_range(1)['min_duty'],p.get_prop_valve_range(1)['max_duty']]

	print('Vacuum\t(0)range\t:', range0)
	print('Pressure\t(1) range\t:', range1)

	id=[0,1]
	for i in id:
		if leaks or stuck: #check if mini e-reg functioning normally
			print("FAIL")
			break
		set = 0
		inc = rough_tune

		p.set_prop_valve_range(i,0,1)  #initial range from 0 to check leaking
		print("Range Limit 0 - 1")
		
		ready_to_flow()
		time.sleep(3)
		average_pressure(500) #closing state reference
		time.sleep(2)
		
		idle = format_float(AverageP1) #closing state reference

		print('idle', idle)
		print("Tuning start")

		while(1):
			ready_to_flow()
			
			p.set_prop_valve_out(i,set) #set pwm to propprtional valve
			wait_end =  time.time()+3
			while (time.time()< wait_end): #stream 3s for user info
				open = format_float(p.read_sensor(6))
				a = 'id: '+ str(i)+', \tset: '+str(set)+', \tidle: '+str(idle)+', \topen: '+str(open)	
				print_flash(a)
				time.sleep(0.2)
			
			average_pressure(1000)
			open = format_float(AverageP1) #steady value collected
			
			a = 'id: '+ str(i)+', \tset: '+str(set)+', \tidle: '+str(idle)+', \topen: '+str(open)
			
			print_flash(a)
			abort_flow() #shut off

			set += inc  #set for next iteration
			if set >= max_set:
				print("Max set point reach, tuning fail")
				print("Last reading: ", a)
				break

			is_lower = open < idle-tolerance #definisi pressure turun
			is_higher =  open > idle+tolerance #definisi pressure naik
			is_stable = idle-tolerance <= open <=idle+tolerance  #definisi pressure steady


			is_other_leak = (is_lower and i==1) or (is_higher and i==0) #definisi arah pressure kebalikan dari expected
			is_this_leak = (is_lower or is_higher) and set == 0 and not is_other_leak #definisi pressure berubah ke arah expected sebelum dibuka
			is_leak = is_other_leak or is_this_leak #definisi bocor

			is_open_found = (is_lower or is_higher) and set > 0 #definisi open
			# is_open_found = (is_lower or is_higher) and set > 0

			if is_leak : 
				leaks = True
				print("Last reading: ", a)
				if is_other_leak:
					print("current id: ", i, " -other PV is leaking")

				if is_this_leak:
					print("current id: ", i, " -this PV is leaking")
				print("Config not saved")
				abort_flow()
				break


			if is_open_found:
				print("Found opening")
				
				if inc == rough_tune:  #dari rough ke fine tune
					set = set - inc - inc
					inc = fine_tune
					print("Fine Tune")

				elif inc == fine_tune: #dari fine tune ke wrap
					print("Last reading: ", a)
					set = set -inc-inc 					#balikkan nilai set
					p.set_prop_valve_range(i,set,max_out) 	#push value, double cek
					p.set_prop_valve_range(i,set,max_out)
					print("Value set for id = ", i , set)
					readConfig(p.get_prop_valve_range,i)
					time.sleep(1)
					p.save_configuration() #save
					abort_flow()
					status = True
					break
		abort_flow()
	abort_flow()

	beep()
	return status

def set_breach_in():
	a = 0
	for i in range(100):
		b = p.read_sensor(8)
		if b > a:
			a = b
			print(a)
		time.sleep(0.1)

	time.sleep(0.1)
	print("breach: ", a)
	print("threshold: ", p.get_breach_threshold())
	new_th=a+25000
	p.set_breach_threshold(new_th)
	time.sleep(0.1)
	p.set_breach_threshold(new_th)
	time.sleep(0.1)
	print("new_th: ", p.get_breach_threshold())
	time.sleep(0.5)
	p.save_configuration()
	p.save_configuration()
	p.save_configuration()


def set_averaging_col():
	p.set_sensor_averaging_window_size(0,128)
	p.save_configuration()

def wlldxx():
	p.set_abort_threshold(4,100)
	p.set_abort_config(1,0,16,16)
	p.set_abort_config(6,0,16,16)
	move_abs_z(-125,15,1000)
	p.set_abort_config(1,0,0,0)
	p.set_abort_config(6,0,0,0)

def set_estop_abort(thres):
	sensor_mask = InputAbort.ESTOP
	abort_id = AbortID.ESTOP
	thres = p.read_sensor(1) - thres
	p.set_abort_threshold(sensor_mask,thres)
	p.set_abort_config(abort_id,0,1<<sensor_mask,1<<sensor_mask)
	p.set_abort_config(AbortID.MOTORHARDBRAKE,0,1<<sensor_mask,1<<sensor_mask)

def clear_estop():
	p.set_abort_config(AbortID.ESTOP,0,0,0)
	p.set_abort_config(AbortID.MOTORHARDBRAKE,0,0,0)

def clear_abort_config(abort_id=None):
	if abort_id:
		p.set_abort_config(abort_id,0,0,0)
	else:
		for i in range(7): p.set_abort_config(i,0,0,0)

def clear_motor_fault():
	 p.clear_motor_fault(0)
	 p.set_motor_enabled(0,1)
	 global motor_error
	 motor_error = False

def set_current_abort(thres):
	#sensor_mask = InputAbort.CurrentMotorZ
	#abort_id = AbortID.MOTORHARDBRAKE
	print(' set_current_abort no longer available since v2')
	#p.set_abort_threshold(sensor_mask,thres)
	#p.set_abort_config(abort_id,0,1<<sensor_mask,0)

def set_pressure_abort(thres=4):
	sensor_mask = InputAbort.PRESS2
	abort_id = AbortID.MOTORHARDBRAKE
	thres = p.read_sensor(7) + thres
	p.set_abort_threshold(sensor_mask,thres)
	p.set_abort_config(abort_id,0,1<<sensor_mask,0)

def set_collision_abort(thres):
	sensor_mask1 = InputAbort.COLLISION1
	sensor_mask2 = InputAbort.COLLISION2
	abort_id = AbortID.MOTORHARDBRAKE
	current_val = p.read_sensor(1)
	thres1 = current_val - thres
	thres2 = current_val + thres
	print (current_val,thres1,thres2)
	p.set_abort_threshold(sensor_mask1,thres1)
	p.set_abort_threshold(sensor_mask2,thres2)
	p.set_abort_config(abort_id,0,(1<<sensor_mask2)|(1<<sensor_mask1) ,1<<sensor_mask1)


def set_picktip_abort(col=100,curr=0.5):
	abort_id = AbortID.MOTORHARDBRAKE
	threscol = p.read_sensor(1)-col
	threscur = curr
	#print threscol,threscur
	p.set_abort_threshold(InputAbort.TOUCHOFF,threscol)
	#p.set_abort_threshold( InputAbort.CurrentMotorZ,threscur)
	sensor_mask = (1<<InputAbort.TOUCHOFF) 
	p.set_abort_config(abort_id,1,sensor_mask,1<<InputAbort.TOUCHOFF)
	#p.set_abort_config(abort_id,0,1<<sensor_mask,0)

def set_plld(press=3,col=100,cur=1,thres=2000):#resistance val dibesarkan dulu
	set_freq(510)
	abort_id = AbortID.MOTORHARDBRAKE
	abort_id2 = AbortID.VALVECLOSE
	average_pressure(10)
	col = p.read_sensor(1) - col
	press = AverageP2 + press
	thres = p.read_sensor(0) - thres

	p.set_abort_threshold(InputAbort.PRESS2,press)
	p.set_abort_threshold(InputAbort.TOUCHOFF,col)
	#p.set_abort_threshold(InputAbort.CurrentMotorZ,cur)
	p.set_abort_threshold(InputAbort.RESISTANCE,thres)

	pressure = 1<<InputAbort.PRESS2
	collision = 1<<InputAbort.TOUCHOFF
	#current = 1 <<InputAbort.CurrentMotorZ
	wlld = 1 << InputAbort.RESISTANCE

	p.set_abort_config(abort_id,0,pressure+collision+wlld,collision+wlld)

	p.set_abort_config(abort_id2,0,pressure+collision+wlld,collision+wlld)

def set_wlld_abort(thres):
	set_freq(510)
	abort_id = AbortID.MOTORHARDBRAKE
	col = p.read_sensor(1) - 30
	thres = p.read_sensor(0) - thres

	p.set_abort_threshold(InputAbort.TOUCHOFF,col)
	#p.set_abort_threshold(InputAbort.CurrentMotorZ,0.9)
	p.set_abort_threshold(InputAbort.RESISTANCE,thres)

	collision = 1<<InputAbort.TOUCHOFF
	#current = 1 <<InputAbort.CurrentMotorZ
	wlld = 1 << InputAbort.RESISTANCE

	p.set_abort_config(abort_id,0,collision+wlld,collision+wlld)

def format_float(input_data):
	return float("{0:.2f}".format(input_data))

def stream_sensor(limit = 10000):
	print("\n_____________________________________________________________\n", end=' ')
	print("Timer\t|P1\t|P2\t|Col\t|Res\t|PosC\t|PosM\t|Breach")
	print("_____________________________________________________________\n", end=' ')
	#  Sensor id
	#  0 = DLLT 						-> in ADC counts
	#  1 = Collision 					-> in ADC counts
	#  2 = NTC temp 1 					-> in celcius
	#  3 = NTC temp 2 					-> in celcius
	#  4 = Temp on pressure sensor 1 	-> in celcius
	#  5 = temp on pressure sensor 2 	-> in celcius
	#  6 = Pressure on P1 				-> in mBar
	#  7 = Pressure on P2				-> in mBar
	#  8 = Breach capacitance 			-> in Amto Farads

	data_0 = []
	data_1 = []
	data_2 = []
	data_3 = []
	data_4 = []
	data_5 = []
	data_6 = []

	while(limit>0):

		data=["NA"]*7
		data[0]=float("{0:.2f}".format(p.read_sensor(6)))
		data[1]=float("{0:.2f}".format(p.read_sensor(7)))
		data[2]=int(p.read_sensor(1))
		data[3]=int(p.read_sensor(0))
		data[4]=int(p.get_encoder_position(0))
		data[5]=float("{0:.1f}".format(p.get_encoder_position(0)/stem_eng))
		data[6]=p.read_sensor(8)

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
				print(" %s \r" % a)
			else:
				print(" %s \r" % a, end=' ')
				time.sleep(0.1)
				sys.stdout.flush()

		except KeyboardInterrupt:
			#sys.stdout.flush()
			print(" %s \r" % a)
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
			r.append(p.read_sensor(0))

		r_av = int(sum(r)/float(len(r)))
		dev = max(r)-min(r)
		val.append(r_av)
		val.append(dev)

		print(str(i)+' hz\t: '+str(r_av)+'\tdev\t: '+str(dev))

	return val

def get_motor_pos():
	pos = p.get_encoder_position(0)/stem_eng
	pos = format_float(pos)
	return pos

def set_ejector(duty,timeout):
	p.set_ejector(duty,timeout)
def clr_ejector():
	p.clr_ejector()

p20targetpick= -139
p200targetpick= -129 #50,2

def picktip(target=-114,col=50,curr=1.2,saferet=20):
	tolerance_res = [80,200]
	firstmove, secondmove,res_check = False,False,False
	#print 'picktip'
	p.set_AD9833_Frequency(2000)
	time.sleep(0.2)
	resA = 0
	for i in range(6):
		resA+=p.read_sensor(0)
	resA = resA/6
	set_picktip_abort(col,curr)
	move_abs_z(target+1,50,500)
	status1  = get_triggered_input(1)
	if status1 != 8:
		print('collision not triggered')
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
		#print '2nd move done',status2
		if status2 == 1<<7:
			print('current limit triggered')
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
			resB+=p.read_sensor(0)
		resB = resB/6
	res = resA-resB

	if tolerance_res[0] < res < tolerance_res[1]:
		res_check = True
	#if firstmove and secondmove and res_check:
		#print 'Picktip Success'
	p.set_AD9833_Frequency(100)
	return [firstmove,secondmove,res_check]

def eject(travel =9.5):
	boostCurr = 0.5
	travelCurr = 0.4
	holdCurr = 0.2
	pos0 = p.get_encoder_position(0) / stem_eng
	p.activate_ejector(24,10,150,5000)
	#time.sleep(0.1)
	#p.set_encoder_correction_enable(0, False)
	#p.set_fol_error_config(0,1,15)
	p.set_motor_currents(0, 0.6,0.55,0.2)
	move_rel_z(travel,15,3000)
	time.sleep(0.2)
	#release
	p.clear_motor_fault(0)
	p.set_motor_currents(0, boostCurr, travelCurr, holdCurr)
	p.deactivate_ejector()
	move_abs_z(pos0,50,1000)
	p.deactivate_ejector()
	time.sleep(1)
	#p.set_motor_currents(0, boost_curr,travel_curr , hold_curr)
	#p.set_encoder_correction_enable(0, True)
	move_abs_z(pos0,50,1000)
	#p.set_fol_error_config(0,1,4)
	print ("posisi sekarang 2= ", (p.get_encoder_position(0)/stem_eng))

def config_status():
	print('belum')

def start_flow(flow, dur=None):	
	if dur:
		start_flow(flow)
		time.sleep(dur)
		abort_flow()
	else:		
		p.start_regulator_mode(2,flow,1,0,0)

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
	P1start = format_float( p.read_sensor(6))
	P2start = format_float(p.read_sensor(7))

	if P1start < ATM_pressure+limit-10 or P2start < ATM_pressure+limit-10:
		start_status = False
	else:
		start_status = True

	print('Start press: ', P1start,P2start)
	start = time.time()
	end = 0
	while(end<60):
		time.sleep(0.01)
		end = time.time()-start
		P1 = format_float( p.read_sensor(6))
		P2 = format_float(p.read_sensor(7))
		progress = str(int(end/60*100))+'%'
		stat = 'Progress : '+progress+'\t'+str(P1)+'\t'+str(P2)
		print_flash(stat)
		if start_status == False: break


	print("----------------------------------------------------------------")
	leak_rate1 = (P1start- p.read_sensor(6))*60/end
	leak_rate2 = (P2start-p.read_sensor(7))*60/end
	leak_rate = format_float(max(leak_rate1,leak_rate2))
	if leak_rate <5 and start_status == True: status = True
	else: status = False
	print('Leak rate\t: '+str(leak_rate)+' / min -- '+str(status))
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
	P1start = format_float( p.read_sensor(6))
	P2start = format_float(p.read_sensor(7))

	if P1start > ATM_pressure-limit+10 or P2start > ATM_pressure-limit+10:
		start_status = False
	else:
		start_status = True

	print('Start press: ', P1start,P2start)
	start = time.time()
	end = 0

	while(end<60):
		time.sleep(0.01)
		end = time.time()-start
		P1 = format_float( p.read_sensor(6))
		P2 = format_float(p.read_sensor(7))
		progress = str(int(end/60*100))+'%'
		stat = 'Progress : '+progress+'\t'+str(P1)+'\t'+str(P2)
		print_flash(stat)
		if start_status == False: break


	print("----------------------------------------------------------------")
	leak_rate1 = ( p.read_sensor(6)-P1start)*60/end
	leak_rate2 = (p.read_sensor(7)-P2start)*60/end
	leak_rate = format_float(max(leak_rate1,leak_rate2))
	if leak_rate <5 and start_status == True: status = True
	else: status = False
	print('Leak rate\t: '+str(leak_rate)+' / min -- '+str(status))
	release_to_atm()
	time.sleep(3)
	abort_flow()
	pipetting_done_req = True
	tare_done_req = True
	return status,leak_rate
	
def dead_vol_count(dead_mode=0):
	#untuk chip calibration
	lower_th = -1
	upper_th = 1
	dead_vol = {
		'0-Chip':[50,80],
		'1-Stem':[80,200],
		'2-F20':[200,220],
		'3-F200':[400,440],
		'4-F1000':[1200,1300]
		}
	options = sorted(dead_vol.keys())
	
	if dead_mode == 0:
		for i in options: print(i+"\n")
		selected = options[int(input(' Select keys '))]
		ranged = dead_vol[selected]
		print(selected, ranged)
	
	steps = 10
	inputs = list(range(ranged[0],ranged[1]+steps,(ranged[1]-ranged[0])/steps))
	result = None
	for i in inputs:
		#plug
		#mini_source
		#release_to_atm
		#ready_to_flow
		#start_logger
		#aspirate(vol,i)
		#wait_timeout
		#stop_logger
		predicted_deadvol = None
		df = read_csv(file_name)
		predicted_deadvol = df['Pipetting_volume'].tail(2)
		if lower_th < predicted_deadvol < upper_th:
			result = i 
			print(predicted_deadvol, "at ", result) 
			break
		#release_to_atm
	return result

def find_min_col(n=15):
	start = time.time()
	end = 0
	init_val = p.read_sensor(1)

	print("Initial\t: ",init_val)

	min_val = init_val
	while (end<n):
		a = p.read_sensor(1)
		if a < min_val:
			min_val = a
		end = time.time()-start
		print_flash(a)

	print('---------------------------')
	print('Minimum value collision sensing :',min_val)


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

	print("max_curr: ",max_cur)
	return max_cur

def get_motor_pos():
	pos = p.get_encoder_position(0)/stem_eng
	return pos

def set_freq(freq, delay=0.25):
	p.set_AD9833_Frequency(freq)
	time.sleep(delay)

def DLLT_chek(freq=120):
	set_freq(freq)
	start_val = p.read_sensor(0)
	start_pos = get_motor_pos()
	res_diff=[0]
	depth = [0]
	start_logger(MotorMask.PosActual,SensorMask.RESISTANCE)
	for i in range(0,4):
		move_rel_z(-0.5,1,10)
		time.sleep(0.2)
		depth.append(format_float(start_pos-get_motor_pos()))
		res_diff.append(int((start_val-p.read_sensor(0))))
	stop_logger()
	correl = format_float(corrcoef(depth,res_diff)[0,1])
	m = calculate_linear_scale_offset(depth,res_diff)
	m = [format_float(m[0]),format_float(m[1])]
	print(res_diff,depth)
	print('Resistance function to depth : ',m)
	print('Linearity : ', correl)
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
		print("collision detected")
		move_rel_z(3,500,500)
	return sensor,pos

def DLLT_start(reverse=0):
	set_collision_abort(40)
	set_freq(120)
	val1 = p.read_sensor(0)

	move_rel_z(-1,10,1000)
	if get_triggered_input(1) !=0:
		clear_abort_config(1)
		move_rel_z(1,10,500)
	time.sleep(0.5)
	val2 = p.read_sensor(0)
	#print val1,val2
	p.set_dllt_move_profile(40*stem_eng,10000*stem_eng,False)
	p.set_dllt_pid(5,5,10,15)
	threshold = (val2-val1) / 4
	diff = val2-val1

	if threshold > -20:
			#cancel
			threshold = -250
			#print("\n  Geometric LLT Start")
	#else:
		#print("\n  Resistnce LLT Start")
	if reverse:
		threshold = 1000
		print('run reverse=========================')
	p.start_dllt(threshold,0.3,1)
	clear_abort_config(1)

	return True

def DLLT_stop():
	clear_motor_fault()
	clear_abort_config(1)
	p.stop_liquid_tracker()

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

	print("Atm: ", atm)
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

			print('Initial : ', P1start,P2start)
			while(end<dur):
				if not(i*x-50< P1start < i*x+50 and i*x-50< P2start < i*x+50):
					print('Pressure/Vaccum not reach')
					print(P1start,'/',x,'\t',P2start,'/',x)
					start_status = False
					break
				else:
					start_status = True
				time.sleep(0.5)
				end = time.time()-start
				P1 = format_float(( p.read_sensor(6)-atm))
				P2 = format_float((p.read_sensor(7)-atm))
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
			print(' ')
			print('Leak rate : ', leak_rate)
			print('Status : ', status)
			print(' ')



			mode_r = i
			limit_r = x
			start_r = [P1start,P2start]
			start_stat_r = start_status
			end_r = [P1end,P2end]
			rate_r = leak_rate
			sum_r = status

			result[n] = [mode_r,limit_r,start_r,start_stat_r,end_r,rate_r,sum_r]
			n += 1

	print('Leak rate pressure\t: '+str(result[0][5])+' mbar/min at ',str(result[0][2][0])+' mbar')
	print('Leak rate vacuum\t: '+str(result[1][5])+' mbar/min at ',str(result[1][2][0])+' mbar')
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
	print(Sensed_vol)
	return Sensed_vol


'''
cal_static_asp          -1.39488434757e+28
cal_static_dsp          -4.14961787176e+16
flow_drift_asp          1.38064173975e+32
flow_drift_dsp          6.67880642128e-26
DpHighThreshold                 2.54366109014e+27
DpLowThreshold          -1.23682050063e-25
ExtraOffsetAsp          -0.0036393115297
ExtraOffsetDsp          2.72588576296e-34
ExtraScaleAsp           -9.77592335855e+35
ExtraScaleDsp           1.59874143619e-31
SlopeThreshold          3.6536689623e+12
vicous_scale            -4.20316522191e+18
viscous_offset          1.89162179466e+20
SensorId                633956266


'''


def pipettingV2(volume, air_column = 570, max_flow = 150, min_flow = 10, decel_vol= 100, cut_off = 10000, set_tolerance = 0.05, settling_time = 1e6, limitp2 = 50, ext_vol_limit = 2):
	global PipettingV2_done
	PipettingV2_done = False
	p.start_pipettingV2(volume, air_column, max_flow, min_flow, decel_vol, cut_off, set_tolerance, settling_time, limitp2, ext_vol_limit)
	while (PipettingV2_done == False):
		time.sleep(0.1)

def default_limit_p1():
	tare_pressure()
	p.set_regulator_p1_limits(ATM_pressure+473,ATM_pressure-473)
	p.save_configuration()
	print(p.get_regulator_p1_limits())
	
'''
default p1 limit wis
load yaml ini belum
set_mini2() wis
cek_pid_ereg() wis
extra_vol_test() wis
'''
def print_get(funct):
	tab = "\t\t:"
	tablast = "\t:"
	for x,y in enumerate(funct.items()):
		if x==13:
			tablast = tab
		print(x,y[0],tablast,y[1])

def load_chip():
	print("original param")
	print_get(p.get_sensor_config(0))
	print("")
	print("Loading from Chip_data_v2.0.csv for channel# ", inputadd)
	df=read_csv("Chip_data_v2.0.csv")
	df=df[0:31]
	params = df[str(inputadd)].to_list()
	p.set_sensor_config(0,params[0],params[1],params[2],params[3],params[4],params[5],params[6],params[7],params[8],params[9],params[10],params[11],params[12],params[13])
	time.sleep(1)
	p.set_sensor_config(1,params[16],params[17],params[18],params[19],params[20],params[21],params[22],params[23],params[24],params[25],params[26],params[27],params[28],params[29])
	p.save_configuration()
	print("")
	print("new param1")
	print_get(p.get_sensor_config(0))
	print("new param2")
	print_get(p.get_sensor_config(1))
	
def V2_all_ch():
	default_limit_p1()
	load_chip()
	if set_mini2():
		extra_vol_test()
	
def motor_test():
	home_z()
	start_logger(7,0)
	for i in range(3):
		move_rel_z(-50,50,100)
		time.sleep(1)
		move_rel_z(50,50,100)
		time.sleep(1)
		home_z()
	time.sleep(1)
	stop_logger()
	
def default_motor():
	p.set_stealthchop_config(0,0,1,1000)
	p.set_motor_currents(0,0.67,0.6,0.3)
	p.set_encoder_correction_enable(0,1)
	p.save_configuration()

def hi_flow(stat=1):
	p.select_flow_sensor(stat)


################### IMPROVEMENTS ################################ IMPROVEMENTS ################################################## IMPROVEMENTS #################################################
# IMPROVEMENTS ######################### IMPROVEMENTS ################################ IMPROVEMENTS ################################################## IMPROVEMENTS ############################
################### IMPROVEMENTS ################################ IMPROVEMENTS ################################################## IMPROVEMENTS #################################################
# IMPROVEMENTS ######################### IMPROVEMENTS ################################ IMPROVEMENTS ################################################## IMPROVEMENTS ############################
################### IMPROVEMENTS ################################ IMPROVEMENTS ################################################## IMPROVEMENTS #################################################

# PICKTIP
class PicktipConfig:
	firstMoveAcc = 100
	firstMoveVel = 80
	secondMoveAcc = 30
	secondMoveVel = 3
	secondMoveDist = 1.0
	picktipOffset = -0.1
	retractAcc = 100
	retractVel = 100
	retractDist = {20: 60, 200: 70, 1000: 100}
	waitPosOffset = 5
	delayBeforeValidate = 100/1000.0
	colThres = 30
	tipPosTolerance = 2.8
	freq = 1500
	freq_delay = 250/1000.0
	folErrorLimit = 15
	targetReachedWindow = 100
	flow = 150
	validColMin = 500
	validColMax = 3000
	validResMin = 50
	validResMax = 12000
	validSampleNum = 5
	validSamplingDelay = 20/1000.0
	validPress2Limit = {20 : {'min':-6.0, 'max':20.0},
						200: {'min':-6.0, 'max':15.0},
						1000: {'min':-6.0, 'max':8.0}}
	boostCurr = 0.5
	travelCurr = 0.4
	holdCurr = 0.2

def setUp_picktip(targetZ, tip):
	printg(f"Setting Up Picktip for P{tip}..")
	folErrorEnable = p.get_fol_error_config(0)['is_tracking_enabled']
	p.set_fol_error_config(0,folErrorEnable,PicktipConfig.folErrorLimit)
	p.start_regulator_mode(2,PicktipConfig.flow,1,0,0)
	set_freq(PicktipConfig.freq,PicktipConfig.freq_delay)
	tare_pressure()
	init_res = 0
	init_col = 0
	for i in range(PicktipConfig.validSampleNum):
		init_res += sensing.res()
		init_col += sensing.col()
	init_res /= PicktipConfig.validSampleNum
	init_col /= PicktipConfig.validSampleNum
	picking = False
	# FIRST MOVE
	print('firstmove..')
	move_abs_z(targetZ+PicktipConfig.picktipOffset+PicktipConfig.secondMoveDist, PicktipConfig.firstMoveVel, PicktipConfig.firstMoveAcc)
	# SECOND MOVE
	defaultCurr = [p.get_motor_currents(0)[cur] for cur in list(p.get_motor_currents(0).keys())]
	if (init_col - sensing.col()) > PicktipConfig.colThres:
		p.set_motor_currents(0, PicktipConfig.boostCurr, PicktipConfig.travelCurr, PicktipConfig.holdCurr)
		clear_motor_fault()
		print('secondmove..')
		move_abs_z(targetZ+PicktipConfig.picktipOffset, PicktipConfig.secondMoveVel, PicktipConfig.secondMoveAcc)
		picking = True
	# RETRACT MOVE
	clear_motor_fault()
	print('retract..')
	move_rel_z(PicktipConfig.retractDist[tip], PicktipConfig.retractVel, PicktipConfig.retractAcc)
	p.set_motor_currents(0, *defaultCurr)
	# VALIDATE
	if picking:
		press2, col, res = 0,0,0
		p2Valid, colValid, resValid = False, False, False
		for i in range(PicktipConfig.validSampleNum):
			press2 += sensing.p2()
			col += sensing.col()
			res += sensing.res()
			time.sleep(PicktipConfig.validSamplingDelay)
		print('press2 col res :', press2, col, res)
		press2 /= PicktipConfig.validSampleNum;	delta_press = press2 - globals()['ATM_pressure']
		p2min, p2max = PicktipConfig.validPress2Limit[tip]['min'], PicktipConfig.validPress2Limit[tip]['max']
		p2Valid = p2min <= delta_press <= p2max
		col /= PicktipConfig.validSampleNum
		colValid = PicktipConfig.validColMin <= col <= PicktipConfig.validColMax
		res /= PicktipConfig.validSampleNum;# res = init_res - res
		resValid = PicktipConfig.validResMin <= res <= PicktipConfig.validResMax
		abort_flow()
		print("p2: {}, col: {}, res: {}".format(delta_press,col,res))
		print("p2Valid: {}, colValid: {}, resValid: {}".format(p2Valid,colValid,resValid))
		if p2Valid and colValid and resValid:
			printg('Picking Tip Succeed')
			return True
		else: 
			printr('Picking Tip Failed')
			return False
	else: 
		printr('Picking Tip Failed')
		return False

# PIPETTING

class PLLDConfig():
	flow = {20:10, 200:10, 1000:40}
	flow_delay = 250
	stem_vel = 15
	stem_acc = 1000
	colThres = 100
	currentThresh = 1.3
	pressThres = {20:4.5, 200:4.5, 1000:2.0}
	resThres = 500
	freq = 500
	freq_delay = 250/1000.0
	cutOff_freq = 100
	useDynamic = True
	pAvgSample = 1000
	stripGap = 0.4
	#stopDecel = 16384.0
	#jerk = 65535.0
	abortDecel = ((stem_vel*stem_eng)**2)/(2*(stripGap*stem_eng))

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
	thresMultiplier = 0.25 # higher value ~ less sensitive
	dlltMinAspThres = 200
	dlltMinDspThres = 200
	dlltMinThres = -700
	dlltMaxThres = 700

class DLLTConfig(): # ================== THIS IS V2 CONFIG
	sampleSize = 25
	class Res:
		stepSize = 2.5
		bigStep = 10
		kp = {20: 1.2, 200: 0.15, 1000: 0.95}
		ki = {20: 0, 200: 0, 1000: 0}
		kd = {20: 0.126, 200: 0, 1000: 0.095}
		inverted = False
		stem_vel = {20: 10, 200: 10, 1000:10}
		stem_acc = {20: 20, 200: 20, 1000:20}
		colThres = 40
		pidPeriod = 1

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
	upperLimit = 5.0
	lowerLimit = -200.0
	colCompressTolerance = 4.0

def setUp_plld(tip=20, lowSpeed=False, detectMode=0):
	printg(f'Setting Up PLLD for P{tip} | Flow: {PLLDConfig.flow[tip]} | Pthres: {PLLDConfig.pressThres[tip]}')
	p.select_flow_sensor(0)
	p.set_valve_open_response_ms(PipettingConfig.NonPipettingResponseMS)
	p.start_regulator_mode(2,PLLDConfig.flow[tip],1,0,0)
	p.set_AD9833_Frequency(PLLDConfig.freq)
	time.sleep(PLLDConfig.freq_delay)
	print('press2 init', sensing.p2())
	# Find threshold
	p.set_sensor_lpf_cutoff(SensorID.PRESSURE_P1, True, PLLDConfig.cutOff_freq)
	p.set_sensor_lpf_cutoff(SensorID.PRESSURE_P2, True, PLLDConfig.cutOff_freq)
	average_pressure(PLLDConfig.pAvgSample)
	p_ref = globals()['AverageP2']
	p2Max = globals()['Max_p2']
	p2Min = globals()['Min_p2']
	#thread_logger(openui=False,maxTick=PLLDConfig.pAvgSample); df = pd.read_csv(globals()['file_name']); p2Pack = [float(i.split(' ')[1]) if type(i) == str else i for i in df[' Pressure_P2'][:len(df[' Pressure_P2'])-1]]; p_ref = np.average(p2Pack); p2Max = max(p2Pack); p2Min = min(p2Pack)
	pressThres = 0
	if PLLDConfig.useDynamic:
		print('P2 Value (Avg: {}, Max:{}, Min:{})'.format(p_ref, p2Max, p2Min))
		pressThres = ((p2Max - p2Min)/2.0)*PLLDConfig.pressThres[tip]
	else:
		pressThres = PLLDConfig.pressThres[tip]
	p_ref += pressThres
	print('Dynamic:   ',PLLDConfig.useDynamic,'| pressThres: ',pressThres)
	print('pressLimit:', p_ref,'| resLimit:',sensing.res()-PLLDConfig.resThres)
	# Clear All Abort
	clear_estop()
	clear_motor_fault()
	clear_abort_config()
	stopDecel = p.get_motor_deceleration(0)['stop_decel']
	jerk = p.get_motor_deceleration(0)['stop_abort_jerk']
	p.set_motor_deceleration(0, stopDecel, PLLDConfig.abortDecel, jerk)
	# Set Abort PLLD
	p.set_abort_threshold(InputAbort.COLLISION1,sensing.col()-PLLDConfig.colThres)
	p.set_abort_threshold(InputAbort.COLLISION2,sensing.col()+PLLDConfig.colThres)
	p.set_abort_threshold(InputAbort.PRESS2,p_ref)
	p.set_abort_threshold(InputAbort.RESISTANCE,sensing.res()-PLLDConfig.resThres)
	collision1 = 1<<InputAbort.COLLISION1
	collision2 = 1<<InputAbort.COLLISION2
	pressure = 1<<InputAbort.PRESS2
	wlld = 1 << InputAbort.RESISTANCE
	if lowSpeed:
		p.set_abort_config(AbortID.VALVECLOSE,False, pressure+collision1+collision2+wlld, collision1+wlld)
		p.set_abort_config(AbortID.MOTORHARDBRAKE,False, pressure+collision1+collision2+wlld, collision1+wlld)
	else: # normal PLLD
		if detectMode == 0: # V2 PLLD = NORMALBRAKE PRESSURE + HARDBRAKE RESISTANCE
			p.set_abort_config(AbortID.MOTORDECEL,False,collision1+collision2+pressure, collision1)
			p.set_abort_config(AbortID.MOTORHARDBRAKE,False, collision1+collision2+wlld, collision1+wlld)
			p.set_abort_config(AbortID.VALVECLOSE,False, pressure+collision1+collision2+wlld, collision1+wlld)
		elif detectMode == 1: # V2 PLLD = HARDBRAKE PRESSURE
			p.set_abort_config(AbortID.MOTORHARDBRAKE,False,pressure+collision1+collision2, collision1+wlld) #for detectMode
			p.set_abort_config(AbortID.VALVECLOSE,False, pressure+collision1+collision2, collision1+wlld)
		elif detectMode == 2: # V2 PLLD = HARDBRAKE RESISTANCE+PRESSSURE
			p.set_abort_config(AbortID.MOTORHARDBRAKE,False, pressure+collision1+collision2+wlld, collision1+wlld)
			p.set_abort_config(AbortID.VALVECLOSE,False, pressure+collision1+collision2+wlld, collision1+wlld)
	sensorCatcher1 = PostTrigger('s1')
	sensorCatcher1.start()
	printg('PLLD has been set..')
	return round(p_ref,2)

def setUp_wlld():
	printg(f'Setting Up WLLD -> resThres: {WLLDConfig.resThres}')
	p.set_AD9833_Frequency(WLLDConfig.freq)
	time.sleep(WLLDConfig.freq_delay)
	# Clear All Abort
	clear_motor_fault()
	clear_estop()
	clear_abort_config()
	# Set Abort PLLD
	p.set_abort_threshold(InputAbort.COLLISION1,sensing.col()-WLLDConfig.colThres)
	p.set_abort_threshold(InputAbort.COLLISION2,sensing.col()+WLLDConfig.colThres)
	p.set_abort_threshold(InputAbort.RESISTANCE,sensing.res()-WLLDConfig.resThres)
	collision1 = 1<<InputAbort.COLLISION1
	collision2 = 1<<InputAbort.COLLISION2
	wlld = 1 << InputAbort.RESISTANCE
	p.set_abort_config(AbortID.MOTORHARDBRAKE,False, collision1+collision2+wlld, collision1+wlld)
	p.set_abort_config(AbortID.VALVECLOSE,False, collision1+collision2+wlld, collision1+wlld)
	sensorCatcher2 = PostTrigger('s2')
	sensorCatcher2.start()
	printg('WLLD has been set..')
	return sensing.res()-WLLDConfig.resThres

class PostTrigger(threading.Thread):
	proc = 0
	press = None
	res = None
	def __init__(self,name):
		threading.Thread.__init__(self)
		self.name = name
		self.postPress = None
		self.postRes = None
		self.checkStat = False

	def run(self):
		print('Post Press-Res Catcher Started..')
		self.checkingPostValue()
		PostTrigger.press = self.postPress
		PostTrigger.res = self.postRes
		PostTrigger.trigger = str(self.trigger)		
		PostTrigger.proc += 1

	def checkingPostValue(self):
		self.checkStat = True
		PostTrigger.trigger = 'None'
		PostTrigger.press = None
		PostTrigger.res = None
		while self.checkStat:
			if p.get_triggered_inputs(AbortID.MOTORHARDBRAKE) or p.get_triggered_inputs(AbortID.MOTORDECEL):								
				break
		self.postPress = sensing.p2()
		self.postRes = sensing.res()

	def terminate(self):
		self.checkStat = False
	
	@staticmethod
	def terminateAll():
		for i in threading.enumerate():
			try: i.terminate()
			except: pass

def combineDict(dict1, dict2):
	newDict = {}
	for key1 in dict1.keys():
		if key1 not in newDict.keys(): newDict[key1] = dict1[key1]
		for key2 in dict2.keys():
			if key1 != key2:
				if key1 + key2 not in newDict.keys(): 
					newDict[key1 + key2] = str(dict1[key1])+'+'+str(dict2[key2])
	return newDict

def check_triggered_input(abort=None):
	def getInput(abort=None):
		inputPack ={
			1<<0 : 'MOTORFAULT',
			1<<1 : 'ESTOP',
			1<<2 : 'TOUCHOFF',
			1<<3 : 'BREACH',
			1<<4 : 'RESISTANCE',
			1<<5 : 'COLLISION1',
			1<<6 : 'COLLISION2',
			1<<7 : 'NTEMP1',
			1<<8 : 'NTEMP2',
			1<<9 : 'PTEMP1',
			1<<10: 'PTEMP2',
			1<<11: 'PRESSURE1',
			1<<12: 'PRESSURE2'}
		newPack = {}
		newPack = combineDict(inputPack, inputPack)
		if get_triggered_input(abort) in newPack: return newPack[get_triggered_input(abort)]
	if abort or abort == 0:
		triger = getInput(abort)
		return triger
	else:
		abortIds = {
			0 : 'MOTORDECEL',	
			1 : 'MOTORHARDBRAKE',  
			2 : 'ESTOP',
			3 : 'TOUCHOFF', 		
			4 : 'VALVEDRAIN',
			5 : 'VALVECLOSE',	
			6 : 'PIPBREACHBLOW'} 
		for i in abortIds.keys(): print(abortIds[i], 'aborted by', getInput(i)) if getInput(i) else None

def get_triggered_input(ids):
	return p.get_triggered_inputs(ids)

def get_sensor_lpf_cutoff(*ids):
	if ids:
		p.get_sensor_lpf_cutoff(ids[0])
	else:
		sens = ['RESISTANCE','COLLISION','NTC_TEMP1','NTC_TEMP2','TEMP_P1','TEMP_P2','PRESSURE_P1','PRESSURE_P2','BREACH_CAPC']
		for i,s in enumerate(sens):
			print(s,'\t',p.get_sensor_lpf_cutoff(i)['cut_off_hz'])

class ReadSensor():
	def __init__(self): pass
	def p1(self): return round(p.read_sensor(SensorID.PRESSURE_P1),2)
	def p2(self): return round(p.read_sensor(SensorID.PRESSURE_P2),2)
	def res(self): return round(p.read_sensor(SensorID.DLLT_RESISTANCE),1)
	def col(self): return round(p.read_sensor(SensorID.COLLISION),1)
	def ntemp1(self): return p.read_sensor(SensorID.NTC_TEMP1)
	def ntemp2(self): return p.read_sensor(SensorID.NTC_TEMP2)
	def ptemp1(self): return p.read_sensor(SensorID.TEMP_P1)
	def ptemp2(self): return p.read_sensor(SensorID.TEMP_P2)
	def breach(self): return p.read_sensor(SensorID.BREACH_CAPC)
	def noiseCheck(self, sensorMask, sample=1000):
		thread_logger(sensorm=sensorMask,maxTick=1000,openui=False)
		df = pd.read_csv(globals()['file_name'])
		key = globals()['STRING_SENSOR_MASK'][(sensorMask>>1)]
		amps = max(df[key]) - min(df[key])
		return amps, min(df[key]), max(df[key])
	def sampling(self, sensorMask, sample=1000):
		thread_logger(sensorm=sensorMask,maxTick=1000,openui=False)
		df = pd.read_csv(globals()['file_name'])
		key = globals()['STRING_SENSOR_MASK'][(sensorMask>>1)]
		return np.average(df[key])
	def sensorRate(self,dur=0,log=False,maxTick=0):
		print('Press ESC to stop..')
		t0 = time.time()
		p1pack, p2pack, respack, colpack = [],[],[],[];	varpack = [p1pack, p2pack, respack, colpack]
		p1_amp, p2_amp, res_amp, col_amp = 0,0,0,0;	amps = [p1_amp, p2_amp, res_amp, col_amp]
		if log: start_logger(0,51)
		while True:
			if kb.is_pressed('ESC'): break
			t1 = round(time.time()-t0,2)
			p1 = round(sensing.p1(),2)
			p2 = round(sensing.p2(),2)
			res = round(sensing.res(),2)
			col = round(sensing.col(),2)
			senspack = [p1,p2,res,col]
			for i in range(len(varpack)): varpack[i].append(senspack[i])
			for i in range(len(amps)): amps[i] = round(np.max(varpack[i]) - np.min(varpack[i]),2)
			if t1 >= dur:
				if dur: break
			if len(p1pack) >= maxTick:
				if maxTick: break
			print(str(t1)+'s | tick: {} | P1: {} | P2: {} | Res: {} | Col: {}'.format(len(p1pack),*tuple(senspack))+'\r', end=' ')
		if log: stop_logger()
		print('\nStopped at {}s\nAmplitudes..'.format(t1))
		print('aP1: {} | aP2: {} | aRes: {} | aCol: {}'.format(*tuple(amps)))
		print('Average..')
		print('avgP1: {} | avgP2: {} | avgRes: {} | avgCol: {}'.format(*tuple([round(np.average(var),2) for var in varpack])))

sensing = ReadSensor()