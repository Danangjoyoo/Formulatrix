import FloDeck as deck
import pregx as pr
import channelx as c
import time, math
from tabulate import tabulate
import pandas as pd
from pandas import read_csv
import threading, winsound, keyboard as kb, string, numpy as np, colorama as cora, random as rd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


w_eng_value = 4.5454545454
B_zero = 702.4545+9*w_eng_value
A_zero = 264.0000
B = [(B_zero-i*9*w_eng_value) for i in range(0,8)]
A = [(A_zero-i*9*w_eng_value) for i in range(0,8)]

len_length = 0
berat_now = 0
fname = 'Weightscale.txt'
before_asp = 0

P1000_picktip_z = -116
P200_picktip_z = -126
P20_picktip_z = -136
#Zpick   = [-114,-104]

vel_z = 75
acc_z = 130

def move_deck(pos):
	w.move_wdeck_abs(pos)

def setVelAcc_z_mode(mode):
	global vel_z, acc_z; mode = str.lower(mode)
	if mode == 'grav' or mode == 'default':
		vel_z = 75; acc_z = 130
	elif mode == 'plate':
		vel_z = 170; acc_z = 365

def align (rack,well,z=-40,evade=-40,tare=0):
	global vel_z, acc_z
	col_max, col_min = 1550,1450
	well = str.upper(well)
	
	if tare ==1:
		c.p.tare_pressure()
		
	c.set_estop_abort(500)
	deck.set_abort_estop()
	if 500<c.p.read_collision_sensor()<1700:
		if c.p.get_encoder_position(0)/c.stem_eng < evade:
			if c.move_abs_z(evade,vel_z,acc_z):
				print 'matane'
				deck.align_deck(rack,well)
		else:
			deck.align_deck(rack,well)
		c.move_abs_z(z,vel_z,acc_z)
		#c.clear_estop()
		return True
		
	else:
		print "Colision out of range"
		return False


def align_plld (rack,well,target=-40,depth=-85,evade=-20,tare=1,dllt=True,init=False):
	global before_asp
	print 'tare', tare
	if not init:
		flow = c.PLLDConfig.flow
		flow_delay = c.PLLDConfig.flow_delay
		stem_vel = c.PLLDConfig.stem_vel
		stem_acc = c.PLLDConfig.stem_acc
	else:
		flow, flow_delay = 10,250
		stem_vel,stem_acc = 3,100

	if tare ==1:
		c.p.tare_pressure()
	c.set_estop_abort(500)
	deck.set_abort_estop()
	if c.p.get_encoder_position(0)/c.stem_eng < evade:
		c.move_abs_z(evade,100,750)
	deck.align_deck(rack,well,0)
	
	file_len() # for gravimetric
	default_weight = berat_now
	print "default weight", default_weight
	before_asp = default_weight
	time.sleep(0.5)
	print '1 nih'
	c.start_flow(flow,flow_delay/1000)#15
	deck.wait_moves([0,1])
	c.move_abs_z(target,100,750) # manual move
	print('manual')
	c.set_plld(LLD.pressThres,init=init)
	print('auto')
	c.move_abs_z(depth,stem_vel,stem_acc) # max move but will stop when plld triggered"
	
	pos =  c.get_motor_pos()
	sensor = c.get_triggered_input(1)
	print sensor,"dfasdfsadfasdfasdfsdf"
	c.abort_flow()
	c.clear_motor_fault()
	c.clear_abort_config(1)
	c.clear_abort_config(6)
	if sensor == 2 or sensor ==256 or sensor== 258:
		result = True
		if dllt:
			print 'dllt start'
			c.DLLT_start()
	else:
		result = False
		#c.move_rel_z(1,50,750)
	c.clear_estop()
	#LLD.zero = math.ceil(c.p.get_motor_pos(0)/100.0)
	LLD.zero = c.p.get_motor_pos(0)/100.0
	return result

def align_wlld (rack,well,target=-40,depth=-100,evade=-40):
	c.set_estop_abort(500)
	deck.set_abort_estop()
	if c.p.get_encoder_position(0)/c.stem_eng < evade:
		c.move_abs_z(evade,100,750)
	deck.align_deck(rack,well,0)
	c.set_wlld_abort(200)
	deck.wait_moves([0,1])
	c.move_abs_z(target,30,750)
	c.move_abs_z(depth,c.PLLDConfig.stem_vel,c.PLLDConfig.stem_acc)
	pos =  c.get_motor_pos()
	sensor = c.get_triggered_input(1)
	print 'sensor wlld', sensor
	c.clear_motor_fault()
	c.clear_abort_config(1)
	if sensor == 256:
		result = Truec.DLLT_start()
	else:
		result = False
		c.move_rel_z(3,50,750)
		thres_r = 0
	dllt = c.p.read_dllt_sensor()
	z = math.ceil(c.p.get_motor_pos(0)/100); LLD.zero = z
	print '\tDLLT:',dllt,'| Z :',z,'\r'
	c.clear_estop()
	return result

def initialization(homing=True):
	print "System Start ... "
	#w.pump_power(1)
	abort_flow()
	c.clear_abort_config(0)
	c.clear_abort_config(1)
	c.clear_abort_config(2)
	c.clear_abort_config(3)
	c.clear_motor_fault()
	c.clear_estop()
	deck.clear_motor()
	c.enable_z()
	c.home_z()
	#c.move_abs_z(-20,10,100)
	time.sleep(1)
	#w.home_wdeck()
	if homing:
		deck.home_all_motor()
	time.sleep(1)
	pr.default_preg()
	#align(A[0]+100)
	#c.eject()

	print "System Ready\n"

#initialization()

#====================== test function ===================
sensor_OK = False
tubing_OK =False

class DefaultSensorVal:
	P1_ = 930
	P2_ = 930
	Col_ = 1500
	Res_2000 = 1500
	Res_510 = 3000
	Res_210 = 3100
	Res_120 = 3100
	Br =1705981

class ToleranceSensorVal:
	Tol_P = 4
	Tol_Col = 500
	Tol_Res = 100
	Tol_Br = 300000
	Tol_dev_R2000 = 20
	Tol_dev_R510 = 15
	Tol_dev_R120 = 70

def cek_id_triggered(inputval,kelas=DefaultSensorVal):
	name = [a for a in vars(kelas) if not a.startswith('__')]
	val = [vars(kelas)[a] for a in name ]
	x = inputval

def test_start_print(string,t):
	pt = time.strftime('%Y_%m_%d_%H:%M:%S', time.localtime(t))
	print ''
	print '==================================================='
	print '~~~  '+str(string)+'\t\t\t ---START--- '
	print '==================================================='
	print str(pt)+'\n'

def test_done_print(string,status,t1,t2):
	pt = time.strftime('%Y_%m_%d_%H:%M:%S', time.localtime(t2))
	if status:
		print ''
		print '==================================================='
		print '~~~  '+str(string) + '\t\t\t === PASS ==='
		print '==================================================='
		print str(pt)

	else:
		print ''
		print '==================================================='
		print '~~~  '+str(string) + '\t\t\t XXX FAIL XXX'
		print '==================================================='
		print str(pt)

	print 'Elapsed time: ',str(t2-t1)+'\n'


def tubing_leak_check():
	global tubing_OK
	t1 = time.time()
	testname = 'tubing_leak_check'
	test_start_print(testname,t1)

	tubing_OK = pr.preg_chamber_leak_test()


	test_done_print(testname,tubing_OK,t1,time.time())
	pr.default_preg()
	return tubing_OK

def sensor_check():
	global sensor_OK
	#"[P1_avg,P2_avg,Col_avg,Res_avg,Br_avg]"

	t1 = time.time()
	testname = 'sensor_check'
	test_start_print(testname,t1)

	P1_avg = False
	P2_avg = False
	Col_avg = False
	Res_avg = False
	Br_avg = False

	val = c.stream_sensor(200)

	P1_avg = True if  DefaultSensorVal.P1_ -ToleranceSensorVal.Tol_P <= val[0] <= DefaultSensorVal.P1_ + ToleranceSensorVal.Tol_P else False
	P2_avg = True if  DefaultSensorVal.P2_ -ToleranceSensorVal.Tol_P <= val[1] <=  DefaultSensorVal.P2_ + ToleranceSensorVal.Tol_P else False
	Col_avg = True if  DefaultSensorVal.Col_-ToleranceSensorVal.Tol_Col <= val[2] <= DefaultSensorVal.Col_ + ToleranceSensorVal.Tol_Col else False
	Res_avg = True if DefaultSensorVal.Res_210 -  ToleranceSensorVal.Tol_Res  <= val[3] <= DefaultSensorVal.Res_210  + ToleranceSensorVal.Tol_Res else False
	Br_avg = True if DefaultSensorVal.Br -  ToleranceSensorVal.Tol_Br  <= val[4] <=DefaultSensorVal.Br  + ToleranceSensorVal.Tol_Br else False

	print 'P1_avg: ',P1_avg
	print 'P2_avg: ',P2_avg
	print 'Col_avg: ' ,Col_avg
	print 'Res_avg: ',Res_avg
	print 'Br_avg: ',Br_avg

	result = [P1_avg,P2_avg,Col_avg,Res_avg,Br_avg]

	status = True if result[0] and result[1] and result[2] and result[3] and result[4] else False
	sensor_OK = status
	if status:

		print'P1\t|P2\t|Col\t|Res\t|Br'
		print str(val[0])+'\t|'+str(val[1])+'\t|'+str(val[2])+'\t|'+str(val[3])+'\t|'+str(val[4])
	test_done_print(testname,status,t1,time.time())

	return status

def resistance_check():
	t1 = time.time()
	testname = 'resistance_check'
	test_start_print(testname,t1)

	val = c.resistance_check()
	st_2000 = True if DefaultSensorVal.Res_2000 - ToleranceSensorVal.Tol_Res <=val[0] <= DefaultSensorVal.Res_2000 + ToleranceSensorVal.Tol_Res and val[1] < ToleranceSensorVal.Tol_dev_R2000 else False
	st_510 = True if DefaultSensorVal.Res_510 - ToleranceSensorVal.Tol_Res <=val[2] <= DefaultSensorVal.Res_510 + ToleranceSensorVal.Tol_Res and val[3] < ToleranceSensorVal.Tol_dev_R510 else False
	st_120 = True if DefaultSensorVal.Res_120 - ToleranceSensorVal.Tol_Res <=val[4] <= DefaultSensorVal.Res_120 + ToleranceSensorVal.Tol_Res and val[5] < ToleranceSensorVal.Tol_dev_R120 else False

	status = True if st_2000 and st_510 and st_120 else False

	print st_2000,"2k"
	print st_510,"510"
	print st_120,"120"
	test_done_print(testname,status,t1,time.time())
	return status


def picktip(pos='None',target=P200_picktip_z,safe=-10,userinput=0,nextPosOnly=False):
	if not nextPosOnly:
		status = [False]
		maxtry=3
		n = 1
		if pos in deck.wellname:
			while( False in status):
				if n > 1:
					eject()
					pos = deck.wellname[deck.wellname.index(pos)+1]
				align(0,pos,P200_picktip_z+15,P200_picktip_z+15)
				status = c.picktip(target,50,2,10)
				n+=1
				lastpos = pos
				print "POS! :", pos
				try:
					nextpos = deck.wellname[deck.wellname.index(pos)+1]
				except:
					nextpos = deck.wellname[0]
				if n>maxtry: break
				lastpos = pos
		else:
		   #status = c.picktip(target,50,2,10)
		   status = c.setUp_picktip(target, safe)
		   nextpos = 'NONE'
		   lastpos = 'NONE'
		#c.move_abs_z(-40,100,750)
		#nextpos = deck.wellname[deck.wellname.index(pos)+1]
		return [(not (False in status)),nextpos,lastpos]
	else:
		if pos in deck.wellname:
			try:
				nextpos = deck.wellname[deck.wellname.index(pos)+1]
			except:
				nextpos = deck.wellname[0]
			return nextpos

def PLLD(mode = 0,depth=-130):
	if mode ==1: #superslow to find precise surface
		speed = 1
		acc = 10
	else:#normal
		speed = 15
		acc = 500
	check_preg()
	val = c.plld(depth,speed,acc)
	#print 'Done', pos
	print 'PLLD DONE', val
	return val

def ASP(vol):
	c.aspiratexxx(vol,150,10,200,5000)
	
def DISP(vol):
	c.dispensexxx(vol,100,10,200,5000)

def aspirate(vol,tip=1000,log=0,timeout=250000):
	maxflow = 100#special case
	if tip ==  200:
		maxflow = vol*0.67 +16.67
		minflow = vol*0.615 + 7.692
	elif tip == 20:
		maxflow = vol*0.7692 +14.615
		if maxflow<15:maxflow=15
		minflow = vol*0.66 + 0
		if minflow < 15: minflow=15
	elif tip == 1000:
		maxflow = vol
		minflow = maxflow
	#if vol<tip+0.2*tip:
	if tip==20 and vol <=30 or tip ==200 and vol <=250 or tip ==1000 and vol <=1200:
		#c.aspirate(vol,maxflow,minflow,log,timeout,tip)
		pipetting_time = c.aspirate(vol,maxflow,minflow,log,timeout,tip)
	else:
		print 'Vol too large'
	return True, pipetting_time

def dispense(vol,tip=1000,log=0,timeout=250000):
	maxflow = 100#special case
	if tip ==  200:
		maxflow = vol*0.67 +16.67
		minflow = vol*0.615 + 7.692
	elif tip == 20:
		maxflow = vol*0.7692 +14.615
		minflow = vol*0.66 + 0
	elif tip == 1000:
		maxflow = vol/2
		minflow = vol/20 if vol>20 else 20

	pipetting_time = c.dispense(vol,maxflow,minflow,log,timeout,tip)
	#c.dispense(vol,maxflow,minflow,log,timeout,tip)

	return True, pipetting_time
def coba(vol):
	check_preg()
	c.tare_pressure()
	c.home_z()
	move_deck(D2[6])
	PLLD()
	aspirate(200)
	c.move_abs_z(-80,75,1000)

def check_preg():
	if pr.preg_limit==True:
		pr.default_preg()

def set_mini_ereg():

	testname = 'set_mini_ereg'
	t1 = time.time()
	test_start_print(testname,t1)
	check_preg()
	status = c.set_mini2()
	test_done_print(testname,status,t1,time.time())
	return status
def PID_mini_ereg_check():
	check_preg()
	testname = 'PID_mini_ereg_check'
	t1 = time.time()
	test_start_print(testname,t1)
	status = c.cek_pid_ereg()
	if status:
		status = int (raw_input('Grafik bagus? |1: Ya, 0: Tidak|:  '))
		while(status==0):
			print 'Set PID mini'
			c.set_pid_ereg()
			c.cek_pid_ereg()
			status = int (raw_input('Grafik bagus? |1: Ya, 0: Tidak, 2: Menyerah|:  '))
	status = True if status == 1 else False


	test_done_print(testname,status,t1,time.time())
	return status

def calibrate_extra_vol():
	check_preg()
	testname =  'calibrate_extra_vol'
	t1 = time.time()
	test_start_print(testname,t1)
	a= c.extra_vol_test()
	status =a[0] and  a[1]
	test_done_print(testname,status,t1,time.time())
	return status


phase_1_status = False
phase_2_status = False
def phase_1():
	global phase_1_status
	phase_1_status = False
	status1  = sensor_check()
	status2  = resistance_check()
	status3 = tubing_leak_check()
	phase_1_status = status1 and status2 and status3
	print 'Phase 1 done, result: ', phase_1_status


def phase_2():
	global phase_2_status
	check_preg()
	if phase_1_status:
		phase_2_status = False
		if set_mini_ereg():
			check_preg()
			if PID_mini_ereg_check():
				check_preg()
				if calibrate_extra_vol():
					phase_2_status = True

	print 'Phase 2 done, result: ', phase_2_status


def abort_flow():
	c.abort_flow()

def full_stem_leak(full=1):
	check_preg()
	testname = 'full_stem_leak'
	t1 = time.time()
	test_start_print(testname,t1)
	c.move_abs_z(0,100,100)
	if full==1:
		ready = raw_input('PUT CLOGGED TIP IN 0,A12   -- enter to continue')
		if ready =='':
			align(0,'A12')
			picktip()
			align(0,'A12')

	status_1 = c.leak_v20()
	status_2 = status_1

	status = True if status_1 and status_2 else False
	test_done_print(testname,status,t1,time.time())
	return status

def PLLD_response(input=32):
	c.tare_done_req = False
	pr.default_preg()
	testname = 'PLLD_test'
	t1 = time.time()
	test_start_print(testname,t1)
	c.move_abs_z(0,100,100)
	if input==1:
		ready = raw_input('PUT TIP IN B[6] and SBS water at A[7]   -- enter to continue')
		if ready =='':
			align(B[6],0)
			c.picktip()
			align(B[6],0)

	wawik()
	align(1,'A12',-70)
	c.tare_pressure()
	val_1= PLLD(1)
	wawik()

	align(1,'A12',-70)
	c.tare_pressure()
	val_2 = PLLD()
	if val_1[0] == 2 and (val_2[0] == 2 or val_2[0] == 258):

		dist = val_1[1] - val_2[1]
	else:
		dist = 100
	tol =2.5
	print 'dis' , dist
	wawik()
	c.move_abs_z(0,100,100)
	status = True if dist <= tol else False
	test_done_print(testname,status,t1,time.time())
	c.tare_done_req = True
	return status

def wawik(rack=0,source='A1',target=-100,Deck=2,well='B3'):
	z = c.p.get_motor_pos(0)/100.0
	align(Deck,well,-40)
	c.set_collision_abort(30)
	c.move_abs_z(target,20,100)
	c.clear_abort_config(1)
	c.clear_motor_fault()
	c.move_rel_z(3,5,100,0)
	c.start_flow(250)
	time.sleep(1)
	c.abort_flow()
	c.set_collision_abort(30)
	c.move_abs_z(target,20,100)
	c.clear_abort_config(1)
	c.clear_motor_fault()
	c.move_rel_z(3,5,100,0)
	align(rack,source,z+10)

def dllt_linearity():

	name ='dllt_linearity'
	t1 = time.time()
	test_start_print(name,t1)
	wawik()
	align(1,'A12',-70)
	PLLD(1)
	dllt = c.DLLT_chek(120)
	status = True if dllt>0.9 else False

	test_done_print(name,status,t1,time.time())

	wawik()

def menu():
	print 'menu()\t: show functions '
	print 'phase_1()\t: 1st phase MFQC'
	print 'phase_2()\t: 2nd phase MFQC'
	print 'phase_3()\t: 2nd phase MFQC'
	print 'sensor_check()'
	print 'resistance_check()'
	print 'tubing_leak_check()'
	print 'set_mini_ereg()'
	print 'PID_mini_ereg_check()'
	print 'calibrate_extra_vol()'
def eject():
	c.start_flow(50)
	c.eject()
	abort_flow()

def phase_3():
	align(1,'D5')
	c.eject()
	full_stem_leak()
	align(1,'D5')
	c.eject()
	print 'Put P200 tip in 0,A1'
	raw_input('Enter to continue')
	align(0,'A1')
	picktip()
	align(0,'A1')
	print 'Put SBS with water in rack 1, A12'
	raw_input('Enter to continue')
	dllt_linearity()
	PLLD_response()

def phase_4():
	volumes = [5,150]
	rows = ['A12','B12']
	for i in rows:
		for x in volumes:
			wawik()
			align(1,i,-90)
			PLLD()
			c.DLLT_start()
			c.start_logger()
			aspirate(x,200)
			c.stop_logger()
			c.DLLT_stop()
			c.dpc_on()
			c.move_rel_z(5,3,10)
			#.start_logger(0,294)

			align(1,i,-50)
			print 'wait'
			time.sleep(10)
			c.stop_logger()
			align(1,i,-90)
			c.dpc_off()
			c.wlld(-110)
			c.DLLT_start()
			dispense(x,200)
			c.DLLT_stop()
			align(1,i,-50)
			print 'done'
			wawik()
def retract_press(travel=4,flow=19):
	c.start_flow(flow)
	c.move_rel_z(travel,4,100,1)
	abort_flow()
	print "retracted done"

def estop_deck():
	c.set_estop_abort(200)
	deck.set_abort_estop(id)
	c.clear_estop()
	deck.clear_motor()

def dpc_test():
	dispense(200,200)
	dispense(200,200)
	align_plld(1,"B7",-100,-125)
	aspirate(200,200)
	c.start_logger(256+8,2+4+32+256)
	c.dpc_on()
	c.move_rel_z(10,10,100)
	time.sleep(8)
	c.stop_logger()
	c.dpc_off()
#OrderedDict([('kp', 0.004999999888241291), ('ki', 1.0000000116860974e-07), ('kd', 0.0), ('o', 0.0), ('thres_idrain', 0.0), ('i_limit', 0.20000000298023224)])
#OrderedDict([('kp', 0.07999999821186066), ('ki', 0.009999999776482582), ('kd', 0.10000000149011612), ('o', 0.0), ('thres_idrain', 0.0), ('i_limit', 0.0)])
#c.p.set_regulator_pid(2,0.08,1e-2,1e-1,0,0,0)

#=========================MODS START HERE==========================

def file_len():
	global len_length
	
	with open(fname) as f:
		for i, l in enumerate(f):
			pass
	len_length = i + 1      
	return i + 1
	
def last_val():
	global berat_now
	lenght = file_len()
	
	with open(fname, 'r') as f:
		lines = f.read().splitlines()
		val = lines[-1].strip()
		val = float(val)
	berat_now = val
	return val
	
found_nline = False 

def start_wait_nline():
	global found_nline  
	threading.Thread(target=wait_nline, args=()).start()

class avoidInpErr():
	inputStat = False
	thread1 = None
	pauseStat = False
	pauseThread = None
	pauseThreadStat = False
	pauseMessage = ''

	@staticmethod
	def pauseFunct(message):
		i = 0; avoidInpErr.pauseMessage = message
		while avoidInpErr.pauseStat:
			if i == 0:
				print "###################### OPERATION PAUSED! CTRL+SHIFT+P TO UNPAUSE ######################"
			i += 1

	@staticmethod
	def switchPause():
		while avoidInpErr.pauseThreadStat:
			try:
				if kb.is_pressed('CTRL+shift+p'):
					if avoidInpErr.pauseStat:
						avoidInpErr.pauseStat = False
					else:
						avoidInpErr.pauseStat = True
						print ' '
						print avoidInpErr.pauseMessage
						print ' '
			except KeyboardInterrupt:
				avoidInpErr.pauseStat = False
				break
				#raise
	@staticmethod
	def pauseOperation(stat):
		if stat:
			avoidInpErr.pauseThreadStat = True
			avoidInpErr.pauseThread =  threading.Thread(target = avoidInpErr.switchPause)
			avoidInpErr.pauseThread.start()
		else:
			avoidInpErr.pauseThreadStat = False

	@staticmethod
	def warningBeep(wait=None):
		if wait and avoidInpErr.inputStat:
			while avoidInpErr.inputStat:
				time.sleep(wait)
				for i in np.arange(100,1000,200):
					if not avoidInpErr.inputStat:
						break
					winsound.Beep(i,200)					
		else:
			for i in np.arange(100,1000,200):
				winsound.Beep(i,200)
	@staticmethod
	def reminderWarningBeep(t):
		avoidInpErr.thread1 = threading.Thread(target = lambda: avoidInpErr.warningBeep(t))
		avoidInpErr.thread1.start()
	@staticmethod
	def test_temp(val):
		val = float(val)
	@staticmethod
	def test_inputNimbangIncrement1ml(val):
		val.split(",")[2]
	@staticmethod
	def test_inputNimbang1ml(val):
		val.split(",")[3]
	@staticmethod
	def test_inputLiquid(val):
		densities = {"peg":1.147796487,"gly":1.127693491,"met":0.7967092132,"wat":0.99707}
		densities[val]
	@staticmethod
	def test_inputTimbangan(val):
		float(val)
	@staticmethod
	def test_string(val):
		str.lower(val)
	@staticmethod
	def test_number(val):
		float(val)
		int(val)
	@staticmethod
	def test_plateFill(val):
		val.split(',')[4]
	@staticmethod
	def test_rangeVol(val):
		val = val.split(','); val[2]
		[float(i) for i in val]
	@staticmethod
	def reInput(words,test_function=None,warning=False,reminds=None):
		avoidInpErr.inputStat = True
		if warning:
			avoidInpErr.warningBeep()
			if reminds:
				avoidInpErr.reminderWarningBeep(reminds)
		try:			
			inputs = raw_input(words)
			if test_function:
				test_function(inputs)
			avoidInpErr.inputStat = False
			return inputs
		except KeyboardInterrupt:
			avoidInpErr.inputStat = False
			raise    
		except:
			print " "
			print "====== Input Error! Check your input and try again!"
			if test_function:
				return avoidInpErr.reInput(words,test_function)
			else:
				return avoidInpErr.reInput(words)

def wait_nline():
	global found_nline
	found_nline = False
	timeout = 60
	file_len()
	start = len_length
	startStable = time.time()
	i=0
	while True:
		file_len()
		if start == len_length:
			time.sleep(1)
			
		else:
			val = last_val()
			found_nline = True
			print " Found New Val"
			return val, (time.time()-startStable)*1000
			break
		i+=1
		print "i => ", i
		if i==timeout:			
			val = avoidInpErr.reInput("TIMEOUT!!  \n >> input timbangan:  ", avoidInpErr.test_inputTimbangan,warning=True) # avoid error from unintended pressed enter
			val = float(val)
			return val, (time.time()-startStable)*1000
			print "TO - val use manual input"
			break



def zeroing():
	c.home_z()
	deck.home_all_motor()
	
def tare():
	c.tare_pressure()
	
def gravimetric(vol):
	global before_asp
	
	
	print "=================================================="
	print "                 GRAVIMETRIC START"
	print "=================================================="
	
	time.sleep(1)
	
	align(0,'H1')
	picktip()
	align_plld(2,'F12')
	tare()
	
	#file_len()
	#wait_nline()
	#default_weight = berat_now
	#print "default weight", default_weight
	#before_asp = default_weight
	#time.sleep(0.5)
	#
	#print "PLLD Start"
	#PLLD()
	#time.sleep(0.5)
	#c.clear_motor_fault()
	#c.DLLT_start()
	
	
	print "Aspirate Start"
	aspirate(vol)
	
	c.DLLT_stop()
	
	c.move_abs_z(-40,30,100)
	
	wait_nline()
	last_val() #value after asp
	after_asp = berat_now
	print "Weight after ASP", after_asp
			
	ASP_Weight = abs(after_asp-before_asp)
	print "Aspirate weight =", ASP_Weight
	
	#c.move_abs_z(-50,30,100)
	
	align_wlld(2,'F12')
	
	#c.DLLT_start()  
	print "Dispense start"
	dispense(vol)
	c.DLLT_stop()

	c.move_abs_z(-40,30,100)
	
	wait_nline()
	last_val() #value after asp
	after_disp = berat_now
	print "Weight after DISP", after_disp
			
	DISP_Weight = abs(after_disp-after_asp)
	print "Dispense weight =", DISP_Weight
	
	time.sleep(1)
	
	print "Eject Tip"
	align(0,'H2')
	c.move_abs_z(-100,30,100)
	
	eject()
	
	align(1,'F12')
	
	print "=================================================="
	print "                 GRAVIMETRIC DONE"
	print "=================================================="
	
	
	
 
def one_ml_test(vol,tip=1000,log=0):
	pos = 2
	well = 'C5'
	align_plld(pos,well,-80,-110)
	aspirate(vol,tip,log)
	res = c.Res_vacuum
	sen = c.Sensed_vol
	align(pos,well,-40)
	time.sleep(5)
	align_wlld(pos,well,-80,-110)
	dispense(vol,tip,log)
	align(pos,well,-40)
	dispense(50,tip,0)
	return res,sen
	
def nyanya():
	vol = [200,100,50]
	c.start_logger(0,6)
	for i in vol:
		dispense(i,1000)
		time.sleep(0.5)
	
	c.stop_logger()
	
def collect_residual(tip=1000):
	vol = [1e3,800,500,200,100,50,20]*5
	ress = []
	senn = []
	for i in vol:
		res,sen = one_ml_test(i,tip,0)
		ress.append(res)
		senn.append(sen)
		time.sleep(1)
		
	print 'vol\t: ', senn
	print 'res\t: ', ress
	
def vol_calibrate(vol,tip=20):
	newvol = []
	P20_th = 2
	P200_th = 20
	P1000_th = 200

	if tip==20:
		th = P20_th
		locs = ['P20_1','P20_2']
	elif tip == 200:
		th = P200_th
		locs = ['P200_1','P200_2']
		
	elif tip == 1000:
		th = P1000_th
		locs = ['P1000_1','P1000_2']
		
	df = read_csv('CALVAL.csv')
	for i in vol:
		i=float(i)
		if i >th:
			loct = locs[1]
		else:
			loct =locs[0]
		
		scale = df.loc[df['Tip'] == loct, 'Scale Asp'].values[0]
		offset = df.loc[df['Tip'] == loct, 'Offset Asp'].values[0]
		#scale =  float(df.loc[loct][1])
		#offset = float(df.loc[loct][2])
		print scale,offset
		volout = float(i)*scale+offset
		newvol.append(volout)
	return newvol

def volScaling(vols,tip=20,opr='lookup'):
	if str.lower(opr) == 'lookup':
		vol = vols[0]
		df = read_csv('lookup_calval.csv')
		idx, newvols, operation = None, None, None
		list_vol = df['targetVol_p'+str(tip)]
		volAvailability = False
		for i in enumerate(list_vol):
			if i[1] == vol:
				volAvailability = True
				idx = i[0]
				break
			else:
				volAvailability = False
		if volAvailability:
			operation = 'LookUp'
			print('LookUp Table Operation')
			newvol = df['comVol_p'+str(tip)][idx]
			newvols = [newvol]*len(vols)
		else:
			operation = 'Sca-Off'
			print('Scale Offset Operation')
			newvols = vol_calibrate(vols, tip)
	else:
		operation = 'Sca-Off'
		print('Scale Offset Operation')
		newvols = vol_calibrate(vols, tip)
	return newvols, operation


def read_protocol(filename="MAP0.csv"):
	df = read_csv(filename)
	df = df.reindex(sorted(df.columns), axis=1)
	del df['col']
	df.index = df.index + 1
	df1=df.stack().to_frame().reset_index().rename(columns={'level_0': 'Col', 'level_1': 'Row',0:'value'})
	df1 = df1.sort_values('Row').reset_index(drop=True)
	df1['Col'] = df1['Col'].astype(str)
	df1['Target'] = df1['Row'] + df1['Col']
	del df1['Row']
	del df1['Col']
	df1['Volumes'], df1['Source'] = df1['value'].str.split('-', 1).str
	del df1['value']
	volumes = df1['Volumes'].tolist()
	targets = df1['Target'].tolist()
	sources = df1['Source'].tolist()

	return [volumes,targets,sources]
	
backgroundmessage = None
class AsyncWrite(threading.Thread):  
 
	def __init__(self, text, out): 
  
		# calling superclass init 
		threading.Thread.__init__(self)  
		self.text = text 
		self.out = out 
  
	def run(self):   
		f = open(self.out, "a") 
		f.write(self.text) 
		f.close()  
		#time.sleep(2) 
		#print "Finished background file write to"+str(self.out)+'\r',

def back_write(message,filename,warn=True): 
	global backgroundmessage
	background = AsyncWrite(message, filename)
	backgroundmessage = background
	background.start()
	if warn:
		print("Write to csv in background: ", message)

	# till the background thread is done 
def wait_write():
	backgroundmessage.join() 
	
def wraps(data):
	separator = ","
	endline = "\n"
	out = ""
	for i in data:
		out += str(i) + separator
	
	out = out[:-1]+endline
	return out
	
def push_data(some_leading,filename,leadOnly=False):
	if not leadOnly:
		out = [
			some_leading,
			c.Total_time_ms,
			c.Alc_time_ms,
			c.Sampling_vol,
			c.Total_sampling,
			c.Last_flow,
			c.P1_off,
			c.P2_off,
			c.Res_vacuum,
			c.Pipetting_done,
			c.Selected_p2,
			c.Tau_time,
			c.Pressure_peak,
			c.Avg_window,
			c.Slope_window,
			c.Threshold,
			c.Sensed_vol,
			c.loggername
			]
	else:
		out = [some_leading]
	
	back_write(wraps(out),filename)

def manualPicktip(pos='None',target=0,evade=0,defaultStat=True):
	if pos in deck.wellname:
		try:
			nextpos = deck.wellname[deck.wellname.index(pos)+1]
		except:
			nextpos = deck.wellname[0]
		#align(0,pos,target+30)
		#time.sleep(0.5)
		align(0,pos,target,evade)
		time.sleep(0.1)
		#c.move_abs_z(target,100,100)
		#time.sleep(0.5)
		align(0,pos,evade)
		return defaultStat,nextpos,pos



def nimbang_1ml(*args):
	proceed = True
	if args:
		if 'v' in args:
			print '\n\t\t=========== MULTI VOLUME MODE ============='
			nimbang_increment_1ml('v')
			proceed = False
		elif 'i' in args:
			print '\n\t\t=========== MULTI VOLUME MODE ============='
			nimbang_increment_1ml()
			proceed = False

	if proceed:
		deck.setTravelMode('grav')
		setVelAcc_z_mode('grav')
		inputs = avoidInpErr.reInput("input please..: vol,tip,iter,pickpos ",avoidInpErr.test_inputNimbang1ml)
		inputs = inputs.split(",")
		vol = float(inputs[0])
		tip = int(inputs[1])
		iter = int(inputs[2])
		pickpos = inputs[3]
		deck.setZeroDeckMode(tip)

		liquid = avoidInpErr.reInput("input liquid type..: peg,gly,met,wat  ",avoidInpErr.test_inputLiquid)
		densities = {
		"peg":1.147796487,
		"gly":1.127693491,
		"met":0.7967092132,
	    "wat":0.99429}    # "wat":0.99707 at 25 C  # "wat":0.99429
		density = densities[liquid]

		print "   ====== !! CAUTION !! =====   "
		print "Don't set zeroing on gravimetric! Make sure the weight is postive!"
		print "This is used to measure the initial and final weight"
		co = avoidInpErr.reInput("Have you setup the gravimetric? y/n ",warning=True); co = str.lower(co)
		while True:
			if co == 'y':
				break
			else:
				co = avoidInpErr.reInput("Have you setup the gravimetric? y/n "); co = str.lower(co)

		
		# posisi timbangan
		scale_pos = [2,'F12']
		
		# z picktip
		pick_targets = {
			20	:-133.8,
			200	:-124.5,
			1000:-129.5
			}
			
		# z saat pindah labware biar ga nabrak timbangan	
		evades = {
			20	:3,
			200	:3,
			1000:3
			}
			
		# aspirate lowest pos	
		targets = {
			20	:-123,
			200	:-114,
			1000:-67
			}
			
		# pos setelah aspirate, nunggu ditimbang	
		safes ={
			20	:-108,
			200	: -98,
			1000: 3
			}
		# ga dipake
		aboves = {
			20	: 0,
			200	: 0,
			1000:0
			}		
		
		pick_target = pick_targets[tip]
		evade 		= evades[tip]
		target 		= targets[tip]
		safe 		= safes[tip]
		above 		= aboves[tip]
		jet 		= 1+target

		vols = [vol]*iter
		#volume = vol_calibrate(vols,tip)
		volume,operation = volScaling(vols, tip,'scale')

		initWeight, finalWeight = 0,0
		string_pushData = ""

		next_pickpos = pickpos
		filename = 'grav\Gravimetric vol_'+str(vol)+ '_' + time.strftime('%Y%m%d%H%M%S', time.localtime(time.time())) + '.csv'
		dates = time.strftime('%Y/%m/%d %H:%M:%S', time.localtime(time.time()))
		#push_data("Liquid,Tip,Type,CommandedVol,Weight,Density,CalcVol,Total_time_ms,Alc_time_ms,Sampling_vol,Total_sampling,Last_flow,P1_off,P2_off,Res_vacuum,Pipetting_done,Selected_p2,Tau_time,Pressure_peak,Avg_window,Slope_window,Threshold,Sensed_vol,Log Files",filename)
		push_data("Dates,Temp,Liquid,Tip,Type,Operation,CommandedVol,Weight,Density,CalcVol,Stable_Time_ms,Pip_Time_ms,Half_Cycle_Time_ms,Full_Cycle_time_ms,Init_Weight,Final_Weight,WeightLoss,WeightLoss_Ratio,Total_time_ms,Alc_time_ms,Sampling_vol,Total_sampling,Last_flow,P1_off,P2_off,Res_vacuum,Pipetting_done,Selected_p2,Tau_time,Pressure_peak,Avg_window,Slope_window,Threshold,Sensed_vol,Log Files",filename)
		for x in range(iter):
			saved_cycleTime = [time.time()]
			dates = time.strftime('%Y/%m/%d %H:%M:%S', time.localtime(time.time()))
			
			#string_pushData = ""
			align(0,next_pickpos,evade,evade)
			if not tip == 1000:
				picktipstat = picktip(next_pickpos,pick_targets[tip])
			else:
				picktipstat = manualPicktip(next_pickpos,pick_target,evade)
			
			pickpos = next_pickpos
			next_pickpos = picktipstat[1]
			ejectpos = picktipstat[2]
			
			print " "
			print "=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-="
			print "Start of iteration No.",x+1
			print " "
			print pickpos, next_pickpos
			if picktipstat[0]:
				temp = avoidInpErr.reInput("Input Temperature: ", avoidInpErr.test_temp,warning=True,reminds=2)

				### Set abort Move to above weight scale
				c.set_estop_abort(500)
				c.move_abs_z(evade,50,100)
				align(scale_pos[0],scale_pos[1],safe,evade)
				
				### Tare weight
				weight0, stableTime = wait_nline()
				if x == 0:
					initWeight = weight0

				### aspirate and move up
				#align_plld(scale_pos[0],scale_pos[1],safe,target,safe)
				align(scale_pos[0],scale_pos[1],target,target,safe)
				c.start_logger(0,6+4096)
				#aspirate(volume[x],tip)
				_, pipetting_time = aspirate(volume[x],tip)
				c.stop_logger()
				c.dpc_on()
				c.move_rel_z(3,5,10)#slow move up to avoid hanging drop
				align(scale_pos[0],scale_pos[1],safe,safe)
				
				###weighing
				weight1, stableTime = wait_nline()
				weight_asp = abs(weight0-weight1)
				calcvol = weight_asp/density
				saved_cycleTime.append(time.time())
				Half_Cycle_Time_ms = (saved_cycleTime[1] - saved_cycleTime[0])*1000

				print "Weight - vol:\t",weight_asp, calcvol
				print "Pip time", pipetting_time
				#push_data(liquid+",P"+str(tip)+",asp,"+str(vol)+","+str(weight_asp)+","+str(density)+","+str(calcvol),filename)
				string_pushData += dates+","+str(temp)+","+liquid+",P"+str(tip)+",asp,"+operation+","+str(vol)+","+str(weight_asp)+","+str(density)+","+str(calcvol)+","+str(stableTime)+","+str(pipetting_time)+","+str(Half_Cycle_Time_ms)
				
				print " "
				print "=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-="
				print "Mid of Iteration No.",x+1
				print "=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-="
				print " "
	            
				### Dispense and move up
				#align(scale_pos[0],scale_pos[1],target,target)
				align_wlld (scale_pos[0],scale_pos[1],target+15,target,safe)
	            #align(2,'F12',124.5)
				c.dpc_off()
				time.sleep(2)
				c.start_logger(0,6+4096)
				#dispense(volume[x],tip)
				_, pipetting_time = dispense(volume[x],tip)
				c.stop_logger()
				retract_press(10,45)
				align(scale_pos[0],scale_pos[1],safe,safe)
				
				### weighing
				weight2, stableTime = wait_nline()
				weight_dsp = abs(weight2-weight1)
				calcvol = weight_dsp/density
				print "Weight - vol:\t",weight_dsp, calcvol
				print "Pip time", pipetting_time
				#push_data(liquid+",P"+str(tip)+",dsp,"+str(vol)+","+str(weight_dsp)+","+str(density)+","+str(calcvol),filename)

				align(scale_pos[0],scale_pos[1],evade,evade)
				### eject
				align(0,ejectpos,pick_targets[tip]+20,evade)
				#align(1,'A1',-133)
				eject()
				time.sleep(1)
				eject()

				saved_cycleTime.append(time.time())
				Half_Cycle_Time_ms = (saved_cycleTime[2] - saved_cycleTime[1])*1000

				Full_Cycle_time_ms = (saved_cycleTime[2] - saved_cycleTime[0])*1000
				string_pushData += ','+str(Full_Cycle_time_ms)+'|'

				if x == iter-1:
					align(0,ejectpos,-10)
					finalWeight = weight2
					string_pushData += dates+","+str(temp)+","+liquid+",P"+str(tip)+",dsp,"+operation+","+str(vol)+","+str(weight_dsp)+","+str(density)+","+str(calcvol)+","+str(stableTime)+","+str(pipetting_time)+","+str(Half_Cycle_Time_ms)+','+str(Full_Cycle_time_ms)
				else:
					string_pushData += dates+","+str(temp)+","+liquid+",P"+str(tip)+",dsp,"+operation+","+str(vol)+","+str(weight_dsp)+","+str(density)+","+str(calcvol)+","+str(stableTime)+","+str(pipetting_time)+","+str(Half_Cycle_Time_ms)+','+str(Full_Cycle_time_ms)+';'

				print 'Cycle Time >>', [saved_cycleTime[1]-saved_cycleTime[0], saved_cycleTime[2]-saved_cycleTime[1], saved_cycleTime[2]-saved_cycleTime[0]]

			print " "
			print "End of iteration No.",x+1
			print "=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-="
			print " "
	    
		weightLoss = initWeight - finalWeight
		weightLoss_Ratio = weightLoss/initWeight
		"""try:
			weightLoss_Ratio = round((weightLoss/initWeight),3)
		except:
			weightLoss_Ratio = '-'"""
		saved_pushData = string_pushData.split(';')
		print 'saved Pushdata', saved_pushData
		for savedData in saved_pushData:
			asp_data = savedData.split('|')[0]
			asp_data += ","+str(initWeight)+","+str(finalWeight)+","+str(weightLoss)+","+str(weightLoss_Ratio)
			push_data(asp_data,filename)
			dsp_data = savedData.split('|')[1]
			dsp_data += ","+str(initWeight)+","+str(finalWeight)+","+str(weightLoss)+","+str(weightLoss_Ratio)
			push_data(dsp_data,filename)

		avoidInpErr.warningBeep()
		print "Loop done, data stored at: ", filename


def nimbang_increment_1ml(*inputs1):
	deck.setTravelMode('grav')
	setVelAcc_z_mode('grav')
	manualvol = False
	if not inputs1:
		inputs1 = avoidInpErr.reInput("input Vol Range : startVol, endVol, resolution >> ",avoidInpErr.test_arangeVol)
		inputs1 = inputs1.split(",")
	else:
		if str.lower(inputs1[0]) == 'v' or str.lower(inputs1[0]) == 'vol':
			manualvol = True
			inputs1 = avoidInpErr.reInput('Desired Vols: ')
	inputs2 = avoidInpErr.reInput("input please : tip, iter_per_tip, PickPos >> ",avoidInpErr.test_inputNimbangIncrement1ml)
	inputs2 = inputs2.split(",")
	liquid = avoidInpErr.reInput("input liquid type : peg,gly,met,wat >> ",avoidInpErr.test_inputLiquid)
	splitStat = raw_input("Split aspirate with dispense? Y/N  ")
	splitStat = str.lower(splitStat)
	if splitStat == 'y':
		splitStat = True
	else:
		splitStat = False

	if not manualvol:
		startVol = float(inputs1[0])
		endVol = float(inputs1[1])
		resolution = float(inputs1[2])
		list_vol = np.arange(startVol, endVol, resolution)
	else:
		list_vol = [float(vol) for vol in inputs1.split(',')]

	tip = inputs2[0]
	deck.setZeroDeckMode(tip)
	iter_per_tip = inputs2[1]
	initPickPos = inputs2[2]

	print " "
	print "!! CAUTION !!"
	print "====weighing properties===="
	print "List Volume :",list_vol
	print "Total Increment Pipetting:", len(list_vol)
	print "Tip required: ", int(iter_per_tip)*int((len(list_vol)))
	print "tip:",tip,"| iter per tip:",iter_per_tip,"| Initial Pickpos:",initPickPos
	print "Split Files:", splitStat
	print "==========================="
	print "[NOTES] ALWAYS REFILL YOUR SELECTED PICKPOS ON CADDY EVERYTIME THE VOLUME IS CHANGING!"
	#print "Total Increment Pipetting:", len(list_vol)
	avoidInpErr.reInput("Is that clear? Enter to continue", warning=True,reminds=2)
	print "Pipetting Started.."
	print " "

	filename, filename1, filename2 = None, None, None
	if splitStat:
		#asp
		filename1 = 'grav\Gravimetric vol_'+'_asp_'+str(list_vol[0])+'_to_'+str(list_vol[-1])+ '_' + time.strftime('%Y%m%d%H%M%S', time.localtime(time.time())) + '.csv'
		push_data("Dates,Temp,Liquid,Tip,Type,Operation,CommandedVol,Weight,Density,CalcVol,Stable_Time_ms,Pip_Time_ms,Half_Cycle_Time_ms,Full_Cycle_time_ms,Init_Weight,Final_Weight,WeightLoss,WeightLoss_Ratio,Total_time_ms,Alc_time_ms,Sampling_vol,Total_sampling,Last_flow,P1_off,P2_off,Res_vacuum,Pipetting_done,Selected_p2,Tau_time,Pressure_peak,Avg_window,Slope_window,Threshold,Sensed_vol,Log Files",filename1)
		#dsp
		filename2 = 'grav\Gravimetric vol_'+'_dsp_'+str(list_vol[0])+'_to_'+str(list_vol[-1])+ '_' + time.strftime('%Y%m%d%H%M%S', time.localtime(time.time())) + '.csv'
		push_data("Dates,Temp,Liquid,Tip,Type,Operation,CommandedVol,Weight,Density,CalcVol,Stable_Time_ms,Pip_Time_ms,Half_Cycle_Time_ms,Full_Cycle_time_ms,Init_Weight,Final_Weight,WeightLoss,WeightLoss_Ratio,Total_time_ms,Alc_time_ms,Sampling_vol,Total_sampling,Last_flow,P1_off,P2_off,Res_vacuum,Pipetting_done,Selected_p2,Tau_time,Pressure_peak,Avg_window,Slope_window,Threshold,Sensed_vol,Log Files",filename2)
	else:
		filename = 'grav\Gravimetric vol_'+str(list_vol[0])+'_to_'+str(list_vol[-1])+ '_' + time.strftime('%Y%m%d%H%M%S', time.localtime(time.time())) + '.csv'
		push_data("Dates,Temp,Liquid,Tip,Type,Operation,CommandedVol,Weight,Density,CalcVol,Stable_Time_ms,Pip_Time_ms,Half_Cycle_Time_ms,Full_Cycle_time_ms,Init_Weight,Final_Weight,WeightLoss,WeightLoss_Ratio,Total_time_ms,Alc_time_ms,Sampling_vol,Total_sampling,Last_flow,P1_off,P2_off,Res_vacuum,Pipetting_done,Selected_p2,Tau_time,Pressure_peak,Avg_window,Slope_window,Threshold,Sensed_vol,Log Files",filename)

	dates = None

	for i in enumerate(list_vol):
		vol = float(i[1])
		tip = int(tip)
		iter = int(iter_per_tip)
		if i[0] == 0:
			pickpos = initPickPos
		else:
			pickpos = next_pickpos
		densities = {
		"peg":1.147796487,
		"gly":1.127693491,
		"met":0.7967092132,
	    "wat":0.99429}    # "wat":0.99707 at 25 C  # "wat":0.99429
		density = densities[liquid]
		
		# posisi timbangan
		scale_pos = [2,'F12']
		
		# z picktip
		pick_targets = {
			20	:-133.8,
			200	:-124.5,
			1000:-123
			}
			
		# z saat pindah labware biar ga nabrak timbangan	
		evades = {
			20	:3,
			200	:3,
			1000:3
			}
			
		# aspirate lowest pos	
		targets = {
			20	:-123,
			200	:-114,
			1000:-64
			}
			
		# pos setelah aspirate, nunggu ditimbang	
		safes ={
			20	:-108,
			200	: -98,
			1000: 3
			}
		# ga dipake
		aboves = {
			20	: 0,
			200	: 0,
			1000:0
			}		
		
		pick_target = pick_targets[tip]
		evade 		= evades[tip]
		target 		= targets[tip]
		safe 		= safes[tip]
		above 		= aboves[tip]
		jet 			= 1+target
		
		vols = [vol]*iter
		#volume = vol_calibrate(vols,tip)
		volume,operation = volScaling(vols,tip,'scale')
		
		next_pickpos = pickpos

		initWeight, finalWeight = 0,0
		string_pushData = ""
		string_aspPushData = ""
		string_dspPushData = ""

		for x in range(iter):
			saved_cycleTime = [time.time()]
			dates = time.strftime('%Y/%m/%d %H:%M:%S', time.localtime(time.time()))

			align(0,next_pickpos,evade,evade)
			if not tip == 1000:
				picktipstat = picktip(next_pickpos,pick_targets[tip])
			else:
				picktipstat = manualPicktip(next_pickpos,pick_target,evade)
			
			pickpos = next_pickpos
			next_pickpos = picktipstat[1]
			ejectpos = picktipstat[2]
			
			print " "
			print "=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-="
			print "Start of iteration No.",x+1,"of volume",i[1],"uL | vol no.",i[0]+1,"of",len(list_vol)
			print " "
	        
			print pickpos, next_pickpos
			if picktipstat[0]:
				temp = avoidInpErr.reInput("Input Temperature: ", avoidInpErr.test_temp,warning=True,reminds=2)

				### Set abort Move to above weight scale
				c.set_estop_abort(500)
				c.move_abs_z(evade,50,100)
				align(scale_pos[0],scale_pos[1],safe,evade)
				
				### Tare weight
				weight0, stableTime = wait_nline()
				if x == 0:
					initWeight = weight0
				
				### aspirate and move up
				#align_plld(scale_pos[0],scale_pos[1],safe,target,safe)
				align(scale_pos[0],scale_pos[1],target,target,safe)
				c.start_logger(0,6+4096)
				#aspirate(volume[x],tip)
				_, pipetting_time = aspirate(volume[x],tip)
				c.stop_logger()
				c.dpc_on()
				c.move_rel_z(3,7,10)#slow move up to avoid hanging drop
				align(scale_pos[0],scale_pos[1],safe,safe)
				
				###weighing
				weight1,stableTime = wait_nline()
				weight_asp = abs(weight0-weight1)
				calcvol = weight_asp/density
				saved_cycleTime.append(time.time())
				Half_Cycle_Time_ms = (saved_cycleTime[1] - saved_cycleTime[0])*1000
				print "Weight - vol:\t",weight_asp, calcvol
				print "Pip time", pipetting_time
				
				if splitStat:
					string_aspPushData += dates+","+str(temp)+","+liquid+",P"+str(tip)+",asp,"+operation+","+str(vol)+","+str(weight_asp)+","+str(density)+","+str(calcvol)+","+str(stableTime)+","+str(pipetting_time)+","+str(Half_Cycle_Time_ms)
				else:	
					string_pushData += dates+","+str(temp)+","+liquid+",P"+str(tip)+",asp,"+operation+","+str(vol)+","+str(weight_asp)+","+str(density)+","+str(calcvol)+","+str(stableTime)+","+str(pipetting_time)+","+str(Half_Cycle_Time_ms)
				
				print " "
				print "=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-="
				print "Mid of Iteration No.",x+1,"of volume",i[1],"uL | vol no.",i[0]+1,"of",len(list_vol)
				print "=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-="
				print " "
	            
				### Dispense and move up
				#align(scale_pos[0],scale_pos[1],target,target)
				if tip == 1000:
					align(scale_pos[0], scale_pos[1],target+10,target,safe)
				else:
					align_wlld (scale_pos[0],scale_pos[1],target+10,target,safe)
	            #align(2,'F12',124.5)
				c.dpc_off()
				time.sleep(2)
				c.start_logger(0,6+4096)
				#dispense(volume[x],tip)
				_, pipetting_time = dispense(volume[x],tip)
				c.stop_logger()
				retract_press(11,55)
				align(scale_pos[0],scale_pos[1],safe,safe)
				
				### weighing
				weight2,stableTime = wait_nline()
				weight_dsp = abs(weight2-weight1)
				calcvol = weight_dsp/density
				saved_cycleTime.append(time.time())
				Half_Cycle_Time_ms = (saved_cycleTime[2] - saved_cycleTime[1])*1000
				print "Weight - vol:\t",weight_dsp, calcvol
				print "Pip time", pipetting_time
				align(scale_pos[0],scale_pos[1],evade,evade)
				### eject
				align(0,ejectpos,pick_targets[tip]+20,evade)
				#align(1,'A1',-133)
				eject()
				time.sleep(0.1)
				eject()

				saved_cycleTime.append(time.time())
				Half_Cycle_Time_ms = (saved_cycleTime[2] - saved_cycleTime[1])*1000
				Full_Cycle_time_ms = (saved_cycleTime[2] - saved_cycleTime[0])*1000
				if splitStat:
					if x == iter-1:
						string_aspPushData += ','+str(Full_Cycle_time_ms)
					else:
						string_aspPushData += ','+str(Full_Cycle_time_ms)+'|'
				else:
					string_pushData += ','+str(Full_Cycle_time_ms)+'|'

				if x == iter-1:
					finalWeight = weight2
					if splitStat:
						string_dspPushData += dates+","+str(temp)+","+liquid+",P"+str(tip)+",dsp,"+operation+","+str(vol)+","+str(weight_dsp)+","+str(density)+","+str(calcvol)+","+str(stableTime)+","+str(pipetting_time)+","+str(Half_Cycle_Time_ms)+','+str(Full_Cycle_time_ms)
					else:	
						string_pushData += dates+","+str(temp)+","+liquid+",P"+str(tip)+",dsp,"+operation+","+str(vol)+","+str(weight_dsp)+","+str(density)+","+str(calcvol)+","+str(stableTime)+","+str(pipetting_time)+","+str(Half_Cycle_Time_ms)+','+str(Full_Cycle_time_ms)
				else:
					if splitStat:
						string_dspPushData += dates+","+str(temp)+","+liquid+",P"+str(tip)+",dsp,"+operation+","+str(vol)+","+str(weight_dsp)+","+str(density)+","+str(calcvol)+","+str(stableTime)+","+str(pipetting_time)+","+str(Half_Cycle_Time_ms)+','+str(Full_Cycle_time_ms)+'|'
					else:	
						string_pushData += dates+","+str(temp)+","+liquid+",P"+str(tip)+",dsp,"+operation+","+str(vol)+","+str(weight_dsp)+","+str(density)+","+str(calcvol)+","+str(stableTime)+","+str(pipetting_time)+","+str(Half_Cycle_Time_ms)+','+str(Full_Cycle_time_ms)+';'
			print " "
			print "End of iteration No.",x+1,"of volume",i[1],"uL | vol no.",i[0]+1,"of",len(list_vol)
			print "=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-="
			print " "

		weightLoss = initWeight - finalWeight
		weightLoss_Ratio = (weightLoss/initWeight)
		"""try:
			weightLoss_Ratio = round((weightLoss/initWeight)*100,3)
		except:
			weightLoss_Ratio = '-'"""
		if splitStat:
			asp_data = string_aspPushData.split('|')
			for data in asp_data:
				data += ","+str(initWeight)+","+str(finalWeight)+","+str(weightLoss)+","+str(weightLoss_Ratio)
				print data
				push_data(data, filename1)
			dsp_data = string_dspPushData.split('|')
			for data in dsp_data:
				data += ","+str(initWeight)+","+str(finalWeight)+","+str(weightLoss)+","+str(weightLoss_Ratio)
				push_data(data, filename2)
		else:
			saved_pushData = string_pushData.split(';')
			for savedData in saved_pushData:
					asp_data = savedData.split('|')[0]
					asp_data += ","+str(initWeight)+","+str(finalWeight)+","+str(weightLoss)+","+str(weightLoss_Ratio)+'%'
					push_data(asp_data,filename)
					dsp_data = savedData.split('|')[1]
					dsp_data += ","+str(initWeight)+","+str(finalWeight)+","+str(weightLoss)+","+str(weightLoss_Ratio)+'%'
					push_data(dsp_data,filename)
		if i[0]+1 != len(list_vol):		
			print " "
			print "[CHANGING PIPETTING VOLUME..]"
			print "DON'T FORGET TO REFILL YOUR SELECTED PICKPOS, ignore if it's already refilled"
			print " "
		else:
			print " "

	align(0,pickpos,safe)
	if splitStat:
		print "Loop done, data stored at: ", filename1,'and',filename2
	else:
		print "Loop done, data stored at: ", filename

def autoposAsp(vol,row='E'): #Referensi dari tabel Working Dye
	row = str.upper(row)
	if vol <= 2: 		#WD 4
		pos = row+'12'
	elif 2 < vol <= 8: 	#WD 3
		pos = row+'10'
	elif 8 < vol <= 40: #WD 2
		pos = row+'7'
	else: 				#WD 1
		pos = row+'2'
	return pos

def speedMode(mode='grav'):
	if mode == 'plate':
		deck.setTravelMode('plate')
		setVelAcc_z_mode('plate')
		print 'Pipetting Speed: Plate (Fast)'
	elif mode == 'grav' or mode == 'default':
		deck.setTravelMode('grav')
		setVelAcc_z_mode('grav')
		print 'Pipetting Speed: Gravimetric (Slow)'

def plate_maps(realPos=False):
	maps = []
	for idx_rows,rows in [i for i in enumerate(string.ascii_uppercase) if i[0] <= 7]:
		maps.append([])
		for cols in range(12):
			if realPos:
				maps[idx_rows].append(rows+str(cols+1))
			else:
				maps[idx_rows].append(' ')
	return maps

def plate_Marking(maps, pos, val,showMap=False):
	for i in enumerate(plate_maps(realPos=True)):
		for ii in enumerate(i[1]):
			if pos == ii[1]:
				#print 'marked at ',pos, ii[0], len(i[1])
				maps[i[0]][ii[0]] = val
	if showMap:
		for i in maps:
			print i
	return maps

def plate_showMap(rawMaps):
	maps=[]; marks = 0
	for i in enumerate(rawMaps): # to avoid overriding the original matrix
		maps.append([])
		maps[i[0]].append(string.ascii_uppercase[i[0]])
		for ii in i[1]:
			maps[i[0]].append(ii)
			try: len(ii)
			except: marks += 1
	keyMap = [i+1 for i in range(12)]; keyMap.insert(0, '+')
	dfMap = pd.DataFrame(maps, columns=keyMap)
	dfMap = dfMap.set_index(dfMap['+']); dfMap.pop('+')
	printy(tabulate(dfMap, headers='keys',tablefmt='psql'))
	return rawMaps, marks

def plate_fill(*inputs):
	operation, simulation = False, False
	list_vol, aspPos, dspPos, complete_vols = [], [], [], []
	tip, iter_per_tip, pickpos = None, None, None
	tipMap, aspMap, dspMap = plate_maps(),plate_maps(),plate_maps()
	if inputs:
		if inputs[0] == 's':
			printg("\t\t*** SIMULATION MODE ***\t\t")
			simulation = True
			inputs = None
		else:
			print(inputs)
			operation = True
			list_vol 		= inputs[0]
			tip 			= inputs[1]
			iter_per_tip 	= inputs[2]
			pickpos 		= inputs[3]
			aspPos_state	= inputs[6]
			simulation 		= inputs[7]
			complete_vols 	= [i for i in list_vol for ii in range(iter_per_tip)]
			print complete_vols

			if aspPos_state == 'a' or aspPos_state == 'auto':
				aspPos_state = 'auto'
				aspPos = [autoposAsp(i) for i in complete_vols]
			elif aspPos_state == 'n' or aspPos_state == 'normal':
				aspPos_state = 'normal'
				for i in range(len(complete_vols)):
					if i == 0:
						aspPos.append(inputs[4])
					else:
						aspPos.append(picktip(aspPos[i-1], nextPosOnly=True))
			else:
				aspPos = [inputs[4]]*len(complete_vols)
			
			for i in range(len(complete_vols)):
				if i == 0:
					dspPos.append(inputs[5])
				else:
					dspPos.append(picktip(dspPos[i-1], nextPosOnly=True))

			if not simulation:
				operation = True

	if not inputs:
		if not simulation:
			inputs = raw_input("Pipetting Mode: Increment/Copy/CustomVol/Simulation (i/c/v/s) >> ")
		else:
			inputs = raw_input("Pipetting Mode: Increment/Copy/CustomVol/Simulation (i/v/s) >> ")
		if str.lower(inputs) == 'i':
			printb("   =================== increment Filling Mode Activated ===================")
			inputs = avoidInpErr.reInput('StartVol, EndVol, range >> ',avoidInpErr.test_rangeVol); inputs = inputs.split(',')
			list_vol =  np.arange(float(inputs[0]),float(inputs[1]),float(inputs[2]))
			inputs = str.upper(avoidInpErr.reInput('Tip, Iter/tip, Pickpos, AspPos, DspPos >> ', avoidInpErr.test_plateFill)); inputs = inputs.split(',')
			aspPos_state = str.lower(raw_input('Asp Pos Mode (auto/normal/lock) >> '))
			if not simulation:
				plate_fill(list_vol,int(inputs[0]), int(inputs[1]), inputs[2], inputs[3], inputs[4],aspPos_state,False)
			else:
				plate_fill(list_vol,int(inputs[0]), int(inputs[1]), inputs[2], inputs[3], inputs[4],aspPos_state,True)
		elif str.lower(inputs) == 'v':
			printb("   =================== Custom Vol Mode Activated ===================")
			inputs = avoidInpErr.reInput('Desired Vol >> '); inputs = inputs.split(',')
			list_vol =  [float(i) for i in inputs]
			inputs = str.upper(avoidInpErr.reInput('Tip, Iter/tip, Pickpos, AspPos, DspPos >> ', avoidInpErr.test_plateFill)); inputs = inputs.split(',')
			aspPos_state = str.lower(raw_input('Asp Pos Mode (auto/normal/lock) >> '))
			if not simulation:
				plate_fill(list_vol,int(inputs[0]), int(inputs[1]), inputs[2], inputs[3], inputs[4],aspPos_state, False)
			else:
				plate_fill(list_vol,int(inputs[0]), int(inputs[1]), inputs[2], inputs[3], inputs[4],aspPos_state,True)
		elif str.lower(inputs) == 'c':
			if simulation:
				printr("**Simulation isn't available for Plate Copy\n**Please reinput operation type..")
				plate_fill()
			else:
				printb("   =================== Plate Copy Mode Activated ===================")
				inputs = str.lower(raw_input("Insert Pickpos, tip >> ")); inputs = inputs.split(',')
				plate_copy(inputs[0],int(inputs[1]))
		elif str.lower(inputs) == 's':
			printg("\t\t*** SIMULATION MODE ***\t\t")
			plate_fill('s')
		else:
			printr("Insert Only 1 mode! i/c/v/s")
			plate_fill()

	if operation:
		sim_pickpos = pickpos
		for x,i in enumerate(complete_vols):
			tipMap = plate_Marking(tipMap,sim_pickpos,i)
			sim_pickpos = picktip(sim_pickpos, nextPosOnly=True)
			aspMap = plate_Marking(aspMap, aspPos[x],i)
			dspMap = plate_Marking(dspMap, dspPos[x],i)
		printb("\n\n*** ---------------------------- Plate Pipetting Preview ---------------------------- ***")
		print "\t--TIP MAP--"
		plate_showMap(tipMap)
		print "\n\t--ASPIRATE MAP-- | Mode: ", aspPos_state
		plate_showMap(aspMap)
		print "\n\t--DISPENSE MAP--"
		plate_showMap(dspMap)
		print "Volumes\t\t:", list_vol
		print "Tip\t\t:", tip
		print "Iter/tip\t:", iter_per_tip
		print "Aspirate Mode\t:", aspPos_state
		print "AspPos:", inputs[4], '| DspPos:', inputs[5]
		print 'Pickpos', pickpos
		volume, operation = volScaling(complete_vols,tip,'scale'); print 'Volulme Calibration\t:',operation
		deck.setZeroDeckMode(tip)

		if not simulation:
			printr('Enter to continue... ');raw_input()
			speedMode('plate')
			starttime=time.time()
			# z picktip
			pick_targets 	= {20	:-134, 	200		:-125, 	1000	:-127}	
			# z saat pindah labware biar ga nabrak timbangan	
			evades 			= {20	:3,		200		:3,		1000	:3}	
			# aspirate lowest pos	
			targets 		= {20 	:-130, 	200 	:-119, 	1000	:-70}
			# dsp lowest pos
			postTargets 	= {20	:-127,	200		:-116,	1000	:-68}
			# pos setelah aspirate, nunggu ditimbang	
			safes 			= {20	:-80,	200		: -60,	1000	: 3}
			# ga dipake
			aboves 			= {20	: 0,	200		: 0,	1000	:0}
			ejectZ 			= {20 	: -125,	200 	: -110,	1000 	: -90}

			pick_target = pick_targets[tip]
			asp_target = targets[tip]
			dsp_target = postTargets[tip]
			evade 		= evades[tip]
			target 		= targets[tip]
			safe 		= safes[tip]
			above 		= aboves[tip]
			jet 		= 1+target
			eject_z		= ejectZ[tip]

			print volume
			target = dspPos
			source = aspPos

			next_pickpos = pickpos
			for x,i in enumerate(complete_vols):
				if tip == 1000:
					picktipstat = manualPicktip(next_pickpos, pick_target)
				else:
					picktipstat = picktip(next_pickpos,pick_target)
				pickpos = next_pickpos
				next_pickpos = picktipstat[1]
				ejectpos = picktipstat[2]
				print pickpos, next_pickpos
				if picktipstat[0]:
					# aspirate phase
					c.move_abs_z(safe,100,300)
					align_plld(1,source[x],asp_target+15,asp_target,safe)
					aspirate(volume[x],tip)
					c.dpc_on()
					c.move_abs_z(safe,100,300)

					#dispense phase
					align(2,target[x],dsp_target,dsp_target)
					#align_wlld(2,target[x],dsp_target+15,dsp_target,-95)
					c.dpc_off()
					dispense(volume[x],tip)
					retract_press(9,41)

					#eject phase
					align(0,pickpos,pick_target+9,pick_target+65)
					c.enable_z()
					eject()
					eject()
			align(0,pickpos,1); speedMode('plate')
			elapsedtime = (time.time()-starttime)
			print "\t--TIP MAP--";_,marks=plate_showMap(tipMap);print "\n\t--ASPIRATE MAP-- | Mode: ", aspPos_state;plate_showMap(aspMap);print "\n\t--DISPENSE MAP--";plate_showMap(dspMap)
			printb('!!! OPERATION SUMMARY !!!')
			print 'Elapsed Time\t:', elapsedtime
			print 'Tip used\t:', marks
			print 'Calibration Type\t:', operation

def plate_copy(pickpos='A1',tip=200,protocolname='MAP0.csv'):
    starttime=time.time()
    safe_h_dsp = -100
    safe_h_asp = -100
    lld_asp = -125  
    lld_dsp = -127
    pick_targets 	= {20	:-134, 	200		:-125, 	1000	:-127}
    targetpick = pick_targets[tip]
    protocol = read_protocol(protocolname)
    volume = vol_calibrate(protocol[0],tip)

    print volume
    target =protocol[1]
    source = protocol[2]
    
    next_pickpos = pickpos
    for x,i in enumerate(source):
        #align(0,pickpos)
        picktipstat = picktip(next_pickpos,targetpick)
        pickpos = next_pickpos
        next_pickpos = picktipstat[1]
        ejectpos = picktipstat[2]
        print pickpos, next_pickpos
        if picktipstat[0]:
           # align(1,source[x],-100,-40,1)
            #PLLD()()
            align_plld(1,source[x],safe_h_asp,lld_asp,-40,1)
            aspirate(volume[x],tip)
            c.dpc_on()
            align_wlld(2,target[x],safe_h_dsp,lld_dsp,-95)
            c.dpc_off()
            dispense(volume[x],tip)
            retract_press()
            align(0,ejectpos,targetpick+9,targetpick+65)

            c.enable_z()
            eject()
            time.sleep(1)
            eject()
    elapsedtime = (time.time()-starttime)
    print "Timeit = ", elapsedtime

def nimbang_low(vol,tip,log=1):
	target = -110#ganjel spon hitam
	safe = -80
	above = -20
	jet = 1+target
	
	#c.move_abs_z(above,50,100)
	#c.move_abs_z(target,50,100)
	#time.sleep(1)
	
	c.move_abs_z(safe,50,100)
	tare = wait_nline()
	c.move_abs_z(target,50,100)
	aspirate(vol,tip,log)
	sensed =c.Sensed_vol
	c.move_abs_z(above,100,100)
	print tare
	weight = tare-wait_nline()
	#c.move_abs_z(above,50,100)
	#if raw_input(' enter = dispense ')=='':
	time.sleep(3)
	if True:
		c.move_abs_z(jet,50,100)
		if vol<50: 
			dispense(vol+10,tip,log)
		else:
			dispense(vol+0.01*vol,tip,log)
		#dispense(100,1000)
		c.move_abs_z(above,50,100)
	return weight,sensed

def zz():
	vol = [1030,202,24,8.7]
	weight,sensed= [],[]
	for i in vol:
		actual,detected = nimbang_1ml(i,0)
		weight.append(actual)
		sensed.append(detected)
		for i,x in enumerate(weight):
			print weight[i]," - \t", sensed[i]
		time.sleep(1)
def yy():
	vol = [3,2,1.5,1]
	weight,sensed= [],[]
	for i in vol:
		actual,detected = nimbang_low(i,20,0)
		weight.append(actual)
		sensed.append(detected)
		for i,x in enumerate(weight):
			print weight[i]," - \t", sensed[i]
		time.sleep(1)
		
def zz():
	vol = [1030,202,24,8.7]
	weight,sensed= [],[]
	for i in vol:
		actual,detected = nimbang_low(i,0)
		weight.append(actual)
		sensed.append(detected)
		for i,x in enumerate(weight):
			print weight[i]," - \t", sensed[i]
		time.sleep(1)

# PLOTTER
class Plotter():
	getData = False
	lastLen = 0
	init_t = 0
	filename = None
	t,travel,vel,acc,col,res,p1,p2 = [], [], [], [], [], [], [], []
	show_travel = True
	show_vel = True
	show_acc = True
	show_col = True
	show_res = True
	show_p1 = True
	show_p2 = True

	@staticmethod
	def plot_logging(start=True,thread=False):
		if start:
			n = 0
			Plotter.getData = True
			filename = 'Level\plot_sensor_{}.csv'.format(int(time.time()))
			pd.DataFrame([[0,0,0,0,0,0,0,0]],columns=['t','travel','vel','acc','col','res','p1','p2']).to_csv(filename, index=False)
			Plotter.filename = filename
			# movement
			init_t = time.time()
			Plotter.init_t = init_t
			current_t = time.time() - init_t
			before_t = 0
			init_travel = abs(c.p.get_encoder_position(0))
			before_travel = 0
			current_vel = 0
			before_vel = 0
			current_acc = 0
			before_acc = 0
			#other sensor
			col, res, p1, p2 = 0,0,0,0
			if thread:
				back_write(wraps(['t,travel,vel,acc,col,res,p1,p2']),filename)
				time.sleep(0.1)
				while Plotter.getData:
					# movement
					current_t = round(time.time() - init_t,2)					
					current_travel = abs(c.p.get_encoder_position(0))-init_travel
					current_vel = (current_travel-before_travel)/(current_t-before_t)
					current_acc = (current_vel - before_vel)/(current_t-before_t)
					before_t = current_t
					before_travel = current_travel
					before_vel = current_vel
					before_acc = current_acc
					# other sensor
					col = c.p.read_collision_sensor()
					res = c.p.read_dllt_sensor()
					p1 = c.p.read_pressure_sensor(0)
					p2 = c.p.read_pressure_sensor(1)
					n += 1
					back_write(wraps(['{},{},{},{},{},{},{},{}'.format(
						current_t, current_travel, current_vel, current_acc, col, res, p1, p2)]),filename,warn=False)
			else:
				thread1 = threading.Thread(target=Plotter.plot_logging,args=(1,1))
				thread1.start()
		else:
			Plotter.getData = False

	#==================== REALTIME PLOTTER ======================
	plotStat = False
	init_t = time.time()
	init_travel = 0
	avgTime = []
	x = []
	limit = 30
	init = True
	current_t = 0
	before_t = 0
	init_travel = 0
	before_travel = 0
	current_vel = 0
	before_vel = 0
	current_acc = 0
	before_acc = 0
	varPack = {
		'travel': [[], 'travel'	, False],
		'vel'	: [[], 'vel'	, False],
		'acc'	: [[], 'acc'	, False],
		'col'	: [[], 'col'	, False],
		'res'	: [[], 'res'	, False],
		'p1'	: [[], 'p1'		, False],
		'p2'	: [[], 'p2'		, False] }

	@staticmethod
	def reset_realtime():
		Plotter.plotStat = False
		Plotter.init_t = time.time()
		Plotter.init_travel = 0
		Plotter.avgTime = []
		Plotter.x = []
		Plotter.limit = 20
		Plotter.init = True
		Plotter.varPack = {
	        'travel': [[], 'travel'	, False],
	        'vel'	: [[], 'vel'	, False],
	        'acc'	: [[], 'acc'	, False],
	        'col'	: [[], 'col'	, False],
	        'res'	: [[], 'res'	, False],
	        'p1'	: [[], 'p1'		, False],
	        'p2'	: [[], 'p2'		, False],
	    }

	@staticmethod
	def plot_realtime(**hide):
		if hide:
			Plotter.reset_realtime()
			container, label, showStat = 0, 1, 2
			if 'limit' in hide: Plotter.limit = hide['limit']
			for var in Plotter.varPack:
				if Plotter.varPack[var][label] in hide:
					Plotter.varPack[var][showStat] = hide[Plotter.varPack[var][label]]
			ani = FuncAnimation(plt.gcf(), Plotter.autoUpdate, interval=15)
			plt.show()
		else:
			print "Input sensor that you want to plot! (Ex: p2=True, p1= True"

	@staticmethod
	def autoUpdate(i):
		t1 = time.time()
		# Initialization =======================
		container, label, showStat = 0, 1, 2
		if Plotter.init:
			Plotter.init_t = time.time()
			Plotter.current_t = time.time() - Plotter.init_t
			Plotter.before_t = 0
			Plotter.init_travel = abs(c.p.get_encoder_position(0))
			Plotter.before_travel = 0
			Plotter.current_vel = 0
			Plotter.before_vel = 0
			Plotter.current_acc = 0
			Plotter.before_acc = 0
			Plotter.init = False
			time.sleep(0.1)
		# set limit
		if len(Plotter.x) >= Plotter.limit:
			Plotter.x.pop(0)
			for var in Plotter.varPack: Plotter.varPack[var][container].pop(0)
		# movement
		Plotter.current_t = round(time.time() - Plotter.init_t, 2)					
		Plotter.current_travel = abs(c.p.get_encoder_position(0))-Plotter.init_travel
		Plotter.current_vel = (Plotter.current_travel-Plotter.before_travel)/(Plotter.current_t-Plotter.before_t)
		Plotter.current_acc = (Plotter.current_vel - Plotter.before_vel)/(Plotter.current_t-Plotter.before_t)
		Plotter.before_t = Plotter.current_t
		Plotter.before_travel = Plotter.current_travel
		Plotter.before_vel = Plotter.current_vel
		Plotter.before_acc = Plotter.current_acc
		# other sensor
		col = c.p.read_collision_sensor()
		res = c.p.read_dllt_sensor()
		p1 = c.p.read_pressure_sensor(0)
		p2 = c.p.read_pressure_sensor(1)
		# ADD DATA
		Plotter.x.append(Plotter.current_t)
		Plotter.varPack['travel'][container].append(Plotter.current_travel)
		Plotter.varPack['vel'	][container].append(Plotter.current_vel)
		Plotter.varPack['acc'	][container].append(Plotter.current_acc)
		Plotter.varPack['col'	][container].append(col)
		Plotter.varPack['res'	][container].append(res)
		Plotter.varPack['p1'	][container].append(p1)
		Plotter.varPack['p2'	][container].append(p2)

		# start to plot
		plt.cla()
		for var in Plotter.varPack:
			if Plotter.varPack[var][showStat]:
				plt.plot(Plotter.x, Plotter.varPack[var][container], linewidth=1, label=Plotter.varPack[var][label])
		plt.legend(loc='upper left')
        
        # end of plotting =======================
        #print("Elapsed:", round(time.time() - t1, 4), "ms")

spdPlotter = False
def speedPlotter(start=True,thread=False):
	global spdPlotter
	if start:
		spdPlotter = True
		filename = 'Level\plot_speed_{}.csv'.format(int(time.time()))
		t1 = time.time()
		t = time.time() - t1
		n = 0
		before_t = 0
		desum = abs(c.p.get_encoder_position(0))
		before_travel = 0
		if thread:
			back_write(wraps(['t,travel,speed,res']),filename)
			while spdPlotter:
				t = round(time.time() - t1,2)
				travel = abs(c.p.get_encoder_position(0))-desum
				speed = (travel-before_travel)/(t-before_t)
				before_travel = travel
				before_t = t
				n += 1
				back_write(wraps(['{},{},{},{}'.format(t,travel,speed,c.p.read_dllt_sensor())]),filename,warn=False)
		else:
			thread1 = threading.Thread(target=speedPlotter,args=(1,1))
			thread1.start()
	else:
		spdPlotter = False

def preReadingPlotter(readCount=5,decrement=-1,customDelay=None):
	curDelay = c.PrereadingConfig.readDelay
	if customDelay: # put in sec unit
		c.PrereadingConfig.readDelay = customDelay
	align(1,'D7',-50)
	mainLLD.findSurface(-100,'wet')
	speedPlotter(1)
	mainLLT.preReading()
	for i in range(readCount-1):
		mainLLT.preReading(decrement)
	time.sleep(0.05)
	speedPlotter(0)
	c.PrereadingConfig.readDelay = curDelay
	print '\nPreReading Plotter Done!'

# LLD/LLT Script
class mainLLD():
	class Operation():
		def __init__(self,types):
			self.types = types
			self.zero = 0
			self.LLT_freq = 510
			self.p1 = 0
			self.p2 = 0
			self.res = 0 
			self.surfaceFound = False
			self.useDynamic = True
			self.pressThres = c.PLLDConfig.pressThres
			self.pressLimit = None
			self.resThres = c.PLLDConfig.resThres
			self.resLimit = None
			self.press_trig = False
			self.res_trig = False
			self.trigtime_p = 0
			self.trigtime_r = 0
			self.preRead_freq = 120
			self.preReading_idealSpeed = 0
			self.readDelay = 200/1000.0
			self.r1_res = 0
			self.r2_res = 0
			self.r3_res = 0
			self.r4_res = 0
			self.r5_res = 0
			self.r6_res = 0
			self.expectedSatZ = {20: -110, 200: -100, 1000: 70}
			self.satRes = 0
			self.satZ = 0
			self.satZlimit = 0
			self.saturated = False
			self.t_operation = 0
			self.TriggeredFirst = None

		def reset(self):
			self.surfaceFound = False
			self.press_trig = False
			self.pressLimit = None
			self.res_trig = False
			self.resLimit = None
			self.saturated = False

		@staticmethod
		def set_value(z,p1,p2,r):
			LLD.zero = z
			LLD.p1 = p1
			LLD.p2 = p2
			LLD.res = r

		@staticmethod
		def get_value(text=False):
			if not text:
				return round(LLD.zero,3), round(LLD.p1,3), round(LLD.p2,3), LLD.res
			else:
				return 'Z: {}\tP1: {}\tP2: {}\tR: {}'.format(round(LLD.zero,3), round(LLD.p1,3), round(LLD.p2,3), LLD.res)

	@staticmethod
	def goZero(manual=False,flow=3,dllt=True,tip=200):
		c.clear_estop()
		c.abort_flow(); retract_press(3,150); c.start_flow(flow)
		if not tip == 1000:
			z = -70
		else:
			z = -10
			LLD.zero = -20
		x,y = 0,0
		p1,p2,r = 0,0,0
		cre,n = 1,0
		z_anchor = LLD.zero
		sf_press, sf_res = False, False
		p1_init = c.p.read_pressure_sensor(0)
		p2_init = c.p.read_pressure_sensor(1)
		r_init = c.p.read_dllt_sensor()
		printr('Inital Value\t: p1 = {}\tp2 = {}\tr = {}'.format(p1_init,p2_init,r_init))
		printr('LLD value\t: p1 = {}\tp2 = {}\tr = {}'.format(LLD.p1,LLD.p2,LLD.res))
		if manual:
			printy('Manual Tuning GoZERO : \nuse ctrl+up/down to control Z pos (+shift to speed up)\npress space when done..')
			while True:
				if kb.is_pressed('space'):
					break
				if kb.is_pressed('down+ctrl'):
					z -= 3 if kb.is_pressed('shift') else 1
				elif kb.is_pressed('up+ctrl'):
					z += 3 if kb.is_pressed('shift') else 1
				p1 = c.p.read_pressure_sensor(0)
				p2 = c.p.read_pressure_sensor(1)
				if dllt:
					r = c.p.read_dllt_sensor()
				c.p.move_motor_abs(0,z*100,100*100,100*100)
				if c.p.read_collision_sensor() < 1000:
					c.clear_motor_fault()
					c.clear_estop()
				print 'z: '+str(z)+'| P1 = '+str(p1)+' | P2 = '+str(p2)+' | Diff: '+str(p1-p2)+' | dllt: '+str(r)+'\r',
			LLD.set_value(z,p1,p2+1,r)
			print 'LLD Set >>', LLD.get_value(True)
			printg('Manual GoZERO Finished')
			print 'z: '+str(z)+'| P1 = '+str(p1)+' | P2 = '+str(p2)+' | Diff: '+str(p1-p2)+' | dllt: '+str(r)
			c.abort_flow()
			retract_press(10,100)
			c.clear_motor_fault()
			mainLLD.goZero(manual=False)
		else:
			printy('Auto Tuning GoZERO')
			if LLD.res > r_init:
				r_init = LLD.res
			if abs(p2_init-LLD.p2) > 2:
				c.abort_flow(); retract_press(10,150); c.start_flow(flow)
			while True:
				p1 = c.p.read_pressure_sensor(0)
				p2 = c.p.read_pressure_sensor(1)
				r = c.p.read_dllt_sensor()
				if p2 < LLD.p2+5:
					if p2_init < p2:
						if r < r_init-100:
							z += cre
							n += 1; print n
						else:
							z -= cre
					else:
						z -= cre
				else:
					c.abort_flow(); retract_press(3,150); c.start_flow(flow)
				if LLD.zero+10 < z:
					cre = 3
				elif LLD.zero+5 < z <= LLD.zero +10:
					cre = 0.5
				elif z < LLD.zero + 3:
					cre = 0.1
				if n >= 25 and r > r_init-100 and p2_init < p2 < LLD.p2+5:
					break
				c.p.move_motor_abs(0,z*100,100*100,100*100)
				if c.p.read_collision_sensor() < 1000:
					c.clear_motor_fault()
					c.clear_estop()
					z += 5
				print 'z: '+str(z)+'| P1 = '+str(p1)+' | P2 = '+str(p2)+' | Diff: '+str(p1-p2)+' | dllt: '+str(r)+'\r',
			LLD.set_value(z,p1,p2+1,r)
			if z > z_anchor+10:
				printr('\nZero Surface too far from estimation, Entering Addition Phase...')
				mainLLD.goZero()
			else:
				printg('\n Zero Surface Found! Auto Tuning GoZERO Finished')
				print 'LLD Set >>', LLD.get_value(True)
				c.abort_flow()
				c.clear_motor_fault()
		c.set_estop_abort(500)

	@staticmethod
	def testGoZero(x):
		filename = 'Level/LLDgoZeroCheck_'+ time.strftime('%Y%m%d%H%M%S', time.localtime(time.time())) + '.csv'
		back_write(wraps(['n','Z','P1','P2','Resistance','Total Time']),filename)
		for i in range(x):
			print(i)
			t1 = time.time()
			mainLLD.goZero()
			total = time.time() - t1
			z,p1,p2,r = LLD.get_value()
			back_write(wraps([str(i+1),str(z),str(p1),str(p2),str(r),str(total)]),filename)

	@staticmethod
	def varCheck(x):
		c.start_flow(1)
		p1_rec, p2_rec, r_rec = [], [], []
		p1_tAvg,p2_tAvg,r_tAvg = [], [], []
		p1_maxDev,p2_maxDev,r_maxDev = 0,0,0
		filename = 'Level/LLDvariableCheck_'+ time.strftime('%Y%m%d%H%M%S', time.localtime(time.time())) + '.csv'
		back_write(wraps(['P1','P2','Resistance']), filename)
		for i in range(x):
			p1 = c.p.read_pressure_sensor(0); p1_rec.append(p1)
			p2 = c.p.read_pressure_sensor(1); p2_rec.append(p2)
			r = c.p.read_dllt_sensor(); r_rec.append(r)
			back_write(wraps([p1,p2,r]),filename,False)
		p1_avg = np.average(p1_rec)
		p2_avg = np.average(p2_rec)
		r_avg = np.average(r_rec)
		for i in range(x):
			p1_t = abs(p1_avg - p1_rec[i]); p1_tAvg.append(p1_t/p1_avg)
			p2_t = abs(p2_avg - p2_rec[i]); p2_tAvg.append(p2_t/p2_avg)
			r_t = abs(r_avg - r_rec[i]); r_tAvg.append(r_t/r_avg)
			if p1_t > p1_maxDev: p1_maxDev = p1_t 
			if p2_t > p2_maxDev: p2_maxDev = p2_t
			if r_t > r_maxDev: r_maxDev = r_t
		p1_stability = np.average(p1_tAvg)
		p2_stability = np.average(p2_tAvg)
		r_stability = np.average(r_tAvg)
		printb('Mean\t\t: P1: {}\tP2: {}\tRes: {}'.format(p1_avg, p2_avg, r_avg))
		printb('Instability\t: P1: {}\tP2: {}\tRes: {}'.format(p1_stability, p2_stability, r_stability))
		printb('Max Deviation\t: P1: {}\tP2: {}\tRes: {}'.format(p1_maxDev,p2_maxDev,r_maxDev))
		c.abort_flow()

	@staticmethod
	def checkResSatur(tip):
		z = LLD.zero
		tipLength = {20:1,200:1,1000:1}
		maxz = tipLength[tip]
		zpack,respack = [], []
		while z <= maxZ:
			res = c.p.read_dllt_sensor()
			zpack.append(z); respack.append(res)
			z -= 0.5
			c.p.move_motor_abs(0,z*100,100*100,100*100)

	@staticmethod
	def findSurface(depth=-80,lld='dry',lowSpeed=False):
		print('FindSurface Started.. lld: {} | HighAccuracy: {}'.format(lld, lowSpeed))
		if lowSpeed:
			flow, flow_delay = 15,250
			stem_vel,stem_acc = 2,10
		else:
			flow = c.PLLDConfig.flow
			flow_delay = c.PLLDConfig.flow_delay
			stem_vel = c.PLLDConfig.stem_vel
			stem_acc = c.PLLDConfig.stem_acc
		depth -= c.chipCalibrationConfig.colCompressTolerance
		if str.lower(lld) == 'dry':
			c.p.set_stop_decel(0,c.PLLDConfig.decel,0)
			Dry.pressLimit = c.setUp_plld(lowSpeed=lowSpeed)
		elif str.lower(lld) == 'wet':
			Wet.resLimit = c.setUp_wlld()
		init_res = c.p.read_dllt_sensor()
		print 'move', c.p.get_motor_pos(0)
		c.move_abs_z(depth,stem_vel,stem_acc) # max move but will stop when plld triggered"
		if str.lower(lld) == 'dry':
			if c.get_triggered_input(c.AbortID.NormalAbortZ) == 1 << c.InputAbort.PressureSensor2:
				Dry.press_trig = True
				if c.get_triggered_input(c.AbortID.HardZ) == 1 << c.InputAbort.LiquidLevelSensor:
					Dry.res_trig = True
		elif str.lower(lld) == 'wet':
			if c.get_triggered_input(c.AbortID.HardZ) == 1 << c.InputAbort.LiquidLevelSensor:
				Wet.res_trig = True
		print 'done move',  c.p.get_motor_pos(0)
		# after the motor stopped, set every process done
		c.abort_flow()
		Average_done = True
		Tare_done = True
		Calibrate_done = True
		Count_volume_done = True
		Pipetting_done = True
		# clear all abort
		pos =  c.get_motor_pos()
		c.clear_motor_fault()
		c.clear_abort_config(c.AbortID.NormalAbortZ)
		c.clear_abort_config(c.AbortID.HardZ)
		c.clear_abort_config(c.AbortID.ValveClose)
		zero = c.p.get_motor_pos(0)/100.0
		print 'Checking surfaceFound..'
		print 'pressureCheck:\t',Dry.pressThres, c.p.read_pressure_sensor(1)
		print 'resCheck:\t',init_res- c.PLLDConfig.resThres, c.p.read_dllt_sensor()
		if str.lower(lld) == 'dry':
			if Dry.pressThres < c.p.read_pressure_sensor(1):
				LLD.surfaceFound = True
				Dry.surfaceFound = True
				printy('Surface found at Dry')
		elif str.lower(lld) == 'wet':
			if Wet.resLimit > c.p.read_dllt_sensor():
				LLD.surfaceFound = True
				Wet.surfaceFound = True
				printb('Surface found at Wet')
		return zero
lld = mainLLD()

LLD = mainLLD.Operation('LLD')
LLD.zero = -90
LLD.res = 3100
LLD.p2 = 936
Dry = mainLLD.Operation('DRY')
Wet = mainLLD.Operation('WET')
Wet.useDynamic = False

class mainLLT():
	r1 = 0
	r2asp = 0
	r2dsp = 0
	r2diff = 0
	threshold = None
	lltMode = None

	@staticmethod
	def run(operation='asp'):
		LLD.reset()
		mainLLT.findThreshold(operation=operation)
		if str.lower(operation) == 'asp':
			if mainLLT.r2asp > mainLLT.r1:
				printg('**Geometric LLT Mode**')
				mainLLT.threshold = 0.0
				mainLLT.Geo.init(operation)
				mainLLT.Geo.start()
			elif abs(mainLLT.r2asp - mainLLT.r1) < c.PrereadingConfig.dlltMinAspThres:
				printg('**Geometric LLT Mode**')
				mainLLT.Geo.init(operation)
				mainLLT.Geo.start()
			else:
				printg('**Resistance LLT Mode**')
				mainLLT.Res.init(operation)
				mainLLT.Res.start()
		elif str.lower(operation) == 'dsp':
			if not mainLLT.r2dsp or not mainLLT.r2asp: mainLLT.r2diff = mainLLT.r2dsp - mainLLT.r2asp
			if mainLLT.r2 > mainLLT.r1:
				printg('**Geometric LLT Mode**')
				mainLLT.threshold = 0.0 # to avoid different resistance preread mode n operation
				mainLLT.Geo.init(operation)
				mainLLT.Geo.start()
			elif c.PrereadingConfig.dlltMinDspThres < abs(mainLLT.r2 - mainLLT.r1) and (c.PrereadingConfig.dlltMinThres<mainLLT.r2diff<c.PrereadingConfig.dlltMaxThres):
				printg('**Resistance LLT Mode**')
				mainLLT.Res.init(operation)
				mainLLT.Res.start()
			else:
				printg('**Geometric LLT Mode**')
				mainLLT.Geo.init(operation)
				mainLLT.Geo.start()

	@staticmethod
	def terminate():
		if mainLLT.lltMode:
			if mainLLT.lltMode == 'geo':
				mainLLT.Geo.stop()
			elif mainLLT.lltMode == 'res':
				mainLLT.Res.stop()
			print 'LLT Terminated'
		else:
			print 'LLT Unterminated'

	@staticmethod
	def check():
		printg('DLLT limit:');print c.p.get_dllt_limit()
		printg('DLLT Move Profile:'); print c.p.get_dllt_move_profile()
		printg('DLLT pid:'); print c.p.get_dllt_pid()
		printg('Tracking Limit:'); print c.p.get_tracking_limit()
		printg('Tracking Config:'); print c.p.get_motor_tracking_config()
		printg('Tracking Status:'); print c.p.get_motor_tracking_status()

	@staticmethod
	def findSaturation(z,tip):
		print 'Find Saturation Parameters...'
		tipLength = {
					20:30,
					200:40,
					1000:80}
		maxZ = z-tipLength[tip]
		zpack, respack, decreasePack = [0],[0],[0]
		saturated = False
		n = 0
		while (z >= maxZ and not saturated):
			z -= 0.5
			c.move_abs_z(z,10,1000)
			pos = c.p.get_motor_pos(0)/100.0; zpack.append(pos)
			res = c.p.read_dllt_sensor(); respack.append(res)
			decRate = res-respack[-2]; decreasePack.append(decRate)
			if n > 5:
				if decreasePack[-1] < decreasePack[-2]:
					saturated = True
					break
			n += 1
		if saturated: print 'Resistance Saturated!'
		else: print 'Resistance is not Saturated!'	
		return zpack[-1], respack[-1], maxZ, saturated

	@staticmethod
	def preReading(move=0):
		if c.p.get_AD9833_Frequency() != c.PrereadingConfig.freq:
			c.set_freq(c.PrereadingConfig.freq, c.PrereadingConfig.freq_delay)
		c.move_rel_z(move,c.PrereadingConfig.stem_vel, c.PrereadingConfig.stem_acc)
		time.sleep(c.PrereadingConfig.readDelay)
		res = c.p.read_dllt_sensor()
		z = c.p.get_motor_pos(0)/100.0
		return res, z

	@staticmethod
	def findThreshold(operation='asp'):
		print 'Finding LLT Threshold..'
		if LLD.surfaceFound:
			align(1,'D7',LLD.zero)
		else:
			align(1,'D7',-10)
			c.move_abs_z(-30,100,200)
			LLD.zero = mainLLD.findSurface(-100)
		mainLLT.r1,_ = mainLLT.preReading()
		r2,_ = mainLLT.preReading(-c.PrereadingConfig.stepDown)
		mainLLT.threshold = (r2 - mainLLT.r1)*c.PrereadingConfig.thresMultiplier
		if   str.lower(operation) == 'asp': mainLLT.r2asp = r2
		elif str.lower(operation) == 'dsp': mainLLT.r2dsp = r2
		print 'r1: {} | r2: {} | Thres: {}'.format(mainLLT.r1, r2, mainLLT.threshold)

	class Geo():
		@staticmethod
		def init(operation='asp'):
			mainLLT.lltMode = 'geo'
			mainLLT.Geo.stop()
			if not mainLLT.threshold: mainLLT.findThreshold(operation=operation)
			print 'Geometric LLT initialized..'

		@staticmethod
		def start():
			print 'Geometric LLT started..'
			c.set_collision_abort(c.DLLTConfig.Geo.colThres)
			c.p.set_tracking_limit(True, c.chipCalibrationConfig.upperLimit*c.stem_eng, c.chipCalibrationConfig.lowerLimit*c.stem_eng)
			c.p.set_motor_tracking_config(
				c.DLLTConfig.Geo.trackFactor,
				mainLLT.threshold,
				c.DLLTConfig.Geo.stem_vel,
				c.DLLTConfig.Geo.stem_acc,
				c.DLLTConfig.Geo.inverted,
				c.DLLTConfig.Geo.startVolThres,
				1)
			c.p.set_motor_tracking_running(True)

		@staticmethod
		def stop():
			print 'Geometric LLT Stopped..'
			c.p.set_motor_tracking_running(False)
			if c.get_triggered_input(c.AbortID.NormalAbortZ) or c.get_triggered_input(c.AbortID.HardZ):
				print 'Motion Config Cleared..'
				c.clear_abort_config(c.AbortID.EstopOut)
				c.clear_abort_config(c.AbortID.NormalAbortZ)
				c.clear_abort_config(c.AbortID.HardZ)
				c.clear_motor()
				c.clear_motor_fault()

	class Res():
		@staticmethod
		def init(operation='asp'):
			mainLLT.lltMode = 'res'
			if not mainLLT.threshold: mainLLT.findThreshold(operation=operation)
			mainLLT.Res.stop()
			c.p.set_dllt_pid(c.DLLTConfig.Res.kp, c.DLLTConfig.Res.ki, c.DLLTConfig.Res.kd, c.DLLTConfig.Res.samplingTime)
			c.p.set_dllt_move_profile(c.DLLTConfig.Res.stem_vel*c.stem_eng, c.DLLTConfig.Res.stem_acc*c.stem_eng, c.DLLTConfig.Res.inverted)
			print 'Resistance LLT initialized..'

		@staticmethod
		def start():
			print 'Resistance LLT Started..'
			c.set_collision_abort(c.DLLTConfig.Res.colThres)
			#c.p.set_dllt_limit(True, c.PrereadingConfig.dlltMinThres, c.PrereadingConfig.dlltMaxThres)
			c.p.start_dllt(mainLLT.threshold, c.DLLTConfig.Res.stepSize, c.DLLTConfig.Res.bigStep)

		@staticmethod
		def stop():
			print 'Resistance LLT Stopped..'
			c.p.stop_dllt()
			if c.get_triggered_input(c.AbortID.NormalAbortZ) or c.get_triggered_input(c.AbortID.HardZ):
				print 'Motion Config Cleared..'
				c.clear_abort_config(c.AbortID.EstopOut)
				c.clear_abort_config(c.AbortID.NormalAbortZ)
				c.clear_abort_config(c.AbortID.HardZ)
				c.clear_motor()
				c.clear_motor_fault()
llt = mainLLT()

class PvR(): # Pressure vs Resistance First Triggered
	lastTestObj = None
	lastTrigtime_p = None
	lastTrigtime_r = None
	trigStart = True
	triggering = False
	trigDone = False

	@staticmethod
	def triggeringThread(sensor,obj,p2_init,res_init,t0,rules=False):
		while PvR.trigStart:
			if not rules:
				if sensor == 'press' or sensor == 'p':
					sensor = 'p'
					rules = c.p.read_pressure_sensor(1) > obj.pressLimit
					if rules: PvR.lastTrigtime_p = round(time.time()-t0,5)
				elif sensor == 'res' or sensor == 'dllt' or sensor == 'r':
					sensor = 'r'					
					rules = c.p.read_dllt_sensor() < res_init - obj.resThres
					if rules: PvR.lastTrigtime_r = round(time.time()-t0,5)
			while PvR.triggering:
				print 'Checking trigger stat...\t\t\t\t\t\t'+'\r',
				if rules:
					if sensor == 'p':
						if not obj.press_trig:
							obj.press_trig = True
							obj.pressLimit = p2_init + obj.pressThres
						printy('Pressure Triggered at', obj.types, 'Operation\n')
						obj.trigtime_p = PvR.lastTrigtime_p
					elif sensor == 'r':
						if not obj.res_trig:
							obj.res_trig = True
							obj.resLimit = res_init - obj.resThres
						printy('Resistance Triggered at', obj.types, 'Operation\n')
						obj.trigtime_r = PvR.lastTrigtime_r
					PvR.trigStart = False
					PvR.trigDone = True
					break

	@staticmethod
	def preRun(obj,p2_init,res_init): # put this function before the setup abort functions declared
		PvR.lastTestObj = obj
		t0 = time.time()
		PvR.lastTrigtime_p = None
		PvR.lastTrigtime_r = None
		PvR.trigStart = True
		PvR.triggering = False
		PvR.trigDone = False
		PvR.rules = False
		check_trigger1 = threading.Thread(target=PvR.triggeringThread,args=('p',obj,p2_init,res_init,t0))
		check_trigger1.start()
		check_trigger2 = threading.Thread(target=PvR.triggeringThread,args=('r',obj,p2_init,res_init,t0))
		check_trigger2.start()

	@staticmethod
	def postRun(): # put this function after event that needs abort function is done
		time.sleep(1)
		PvR.triggering = True
		print 'Waiting Press v Res of {} to be done..'.format(PvR.lastTestObj.types)
		while not PvR.trigDone:
			time.sleep(0.1)
		PvR.triggering = False
		print 'Press V Res Finished, Winner:', PvR.getLastWinner()

	@staticmethod
	def getLastWinner():
		if PvR.lastTestObj:
			if PvR.lastTestObj.trigtime_p and PvR.lastTestObj.trigtime_r:
				if PvR.lastTestObj.trigtime_p < PvR.lastTestObj.trigtime_r:
					return 'Press Sensor', PvR.lastTrigtime_r - PvR.lastTrigtime_p
				elif PvR.lastTestObj.trigtime_p > PvR.lastTestObj.trigtime_r:
					return 'Res Sensor', PvR.lastTrigtime_p - PvR.lastTrigtime_r
			else:
				if not PvR.lastTestObj.trigtime_r and not PvR.lastTestObj.trigtime_p:
					return 'No Winner', None
				elif not PvR.lastTestObj.trigtime_r and PvR.lastTestObj.trigtime_p:
					return 'Press Sensor', PvR.lastTestObj.trigtime_p
				elif PvR.lastTestObj.trigtime_r and not PvR.lastTestObj.trigtime_p:
					return 'Res Sensor', PvR.lastTestObj.trigtime_r
		else:
			print 'No PvR have ran'

def tip_reciprocate():
	printy('!!! PUT THE WATER BUCKET ON RACK 1-D7 !!!')
	inputs1 = avoidInpErr.reInput('Tip, Iter, Pickpos >> ')
	tip = int(inputs1.split(',')[0])
	iters = int(inputs1.split(',')[1])
	pickpos = inputs1.split(',')[2]

	# z picktip
	pick_targets 	= {20	:-134, 	200		:-125, 	1000	:-127}	
	# z saat pindah labware biar ga nabrak timbangan	
	evades 			= {20	:3,		200		:3,		1000	:3}	
	# aspirate lowest pos	
	targets 		= {20 	:-95, 	200 	:-84, 	1000	:-50}
	safes 			= {20	:-55,	200		:-35,	1000	:3}

	deck.setZeroDeckMode(tip)
	next_pickpos = pickpos
	pick_target = pick_targets[tip]
	evade = evades[tip]
	target = targets[tip]
	safe = safes[tip]
	source = 'D7'
	zeros = 0
	n = 0

	filename = 'Level\LLD_P'+str(tip)+ '_' + time.strftime('%Y%m%d%H%M%S', time.localtime(time.time())) + '.csv'
	back_write(wraps([
		'X'+','+'n'			+','+
		'Date'				+','+
		'Tip'				+','+
		'Zero Surface'		+','+
		'p1_init'			+','+
		'AtmPress(p2_init)' +','+
		'Initial Res'		+','+
		'Veloc'				+','+
		'Accel'				+','+
		'Flow'				+','+
		'Type'				+','+
		'UseDynamic'		+','+
		'Press Threshold'	+','+
		'Press Limit'		+','+
		'Res Threshold'		+','+
		'Res Limit'			+','+
		'Press Trig'		+','+
		'Res Trig'			+','+
		'LLT Res Freq'		+','+
		'ZeroRes'			+','+
		'dRes(init-zero)'	+','+
		'Depth'				+','+
		'P1'				+','+
		'P2'				+','+
		'dP1(init-zero)'	+','+
		'dP2(init-zero)'	+','+
		'Pre Read Freq'		+','+
		'R1'				+','+
		'R2'				+','+
		'R3'				+','+
		'R4'				+','+
		'R5'				+','+
		'R6 at ExpectedSatZ'+','+
		'ExpectedSatZ'		+','+
		'Saturated Res'		+','+
		'Saturated Z'		+','+
		'FindSatZLimit'		+','+
		'Saturated'			+','+
		'Opr Time ms'		+','+
		'FullCycle ms']),filename)
	c.move_abs_z(-10,200,500)

	for x in range(iters):
		t_tot1 = time.time()
		c.tare_pressure(); atm_press = c.ATM_pressure
		dates = time.strftime('%Y/%m/%d %H:%M:%S', time.localtime(time.time()))
		if tip == 1000:
			picktipstat = manualPicktip(next_pickpos, pick_target)
		else:
			picktipstat = picktip(next_pickpos,pick_target,safe)
		pickpos 		= next_pickpos
		next_pickpos 	= picktipstat[1]
		ejectpos		= picktipstat[2]
		if picktipstat[0]:
			next_pickpos
			p1_init = c.p.read_pressure_sensor(0)
			res_init = c.p.read_dllt_sensor()
			printg('Finding Zero Surface...')
			print 'initRes:',res_init,'| p1_init:',p1_init,'| p2_init:',atm_press
			align(1,source,target+15,safe)
			zeros = mainLLD.findSurface(target,lld='dry',lowSpeed=True)
			if c.p.read_dllt_sensor() < res_init - Dry.resThres:
				LLD.res_trig = True
			if LLD.res_trig:
				printr('Resistance triggered! Pressure Zero Surface Fail, Trying GoZERO...')
				mainLLD.goZero()
				zeros = LLD.zero
				LLD.surfaceFound = True
			printg('Zero Surface Found! Cleaning up the tip...')
			Dry.reset()
			Wet.reset()
			if LLD.surfaceFound:
				wawik(1,source,target-10)
				#################### DRY DRY DRY DRY DRY #####################################

				# Dry Phase
				printb('DRY PHASE..')
				t1 = time.time()
				Dry.zero = mainLLD.findSurface(target,lld='dry')
				Dry.t_operation = time.time()-t1
				Dry.p1, Dry.p2 = c.p.read_pressure_sensor(0),c.p.read_pressure_sensor(1)
				Dry.res = c.p.read_dllt_sensor()
				time.sleep(c.PrereadingConfig.readDelay)

				# PreReading Phase
				#R1 = 0mm
				Dry.r1_res,_ = mainLLT.preReading()
				printg('Level 1..', Dry.r1_res,_)

				#R2 = -1mm				
				Dry.r2_res,_ = mainLLT.preReading(-c.PrereadingConfig.stepDown)
				printg('Level 2..',Dry.r2_res,_)

				#R3 = -2mm
				Dry.r3_res,_ = mainLLT.preReading(-c.PrereadingConfig.stepDown)
				printg('Level 3..',Dry.r3_res,_)

				#R4 = -3mm
				Dry.r4_res,_ = mainLLT.preReading(-c.PrereadingConfig.stepDown)
				printg('Level 4..',Dry.r4_res,_)

				#R5 = -4mm
				Dry.r5_res,_ = mainLLT.preReading(-c.PrereadingConfig.stepDown)
				printg('Level 5..',Dry.r5_res,_)

				#R6 = -110
				Dry.r6_res,_ = mainLLT.preReading(Dry.expectedSatZ[tip]-(c.p.get_motor_pos(0)/100.0))
				printg('Level 6..',Dry.r6_res,_)

				#Saturated Res & Z
				Dry.satZ, Dry.satRes, Dry.satZlimit, Dry.saturated = mainLLT.findSaturation(Dry.zero, tip)
				printg('SaturatedRes:',Dry.satRes,'at z:',Dry.satZ)

				##################### WET WET WET WET WET ########################3

				printb('WET PHASE..')
				# Wet phase
				t3 = time.time()
				align(1,source,target+30)
				Wet.zero = mainLLD.findSurface(target,lld='wet')
				Wet.t_operation = time.time()-t3

				#Checking wlld triggers
				Wet.p1, Wet.p2 = c.p.read_pressure_sensor(0), c.p.read_pressure_sensor(1)
				Wet.res = c.p.read_dllt_sensor()
				c.DLLT_stop()
				time.sleep(c.PrereadingConfig.readDelay)

				# PreReading Phase
				#R1 = 0mm
				Wet.r1_res,_ = mainLLT.preReading()
				printg('Level 1..', Wet.r1_res,_)

				#R2 = -1mm				
				Wet.r2_res,_ = mainLLT.preReading(-c.PrereadingConfig.stepDown)
				printg('Level 2..',Wet.r2_res,_)

				#R3 = -2mm
				Wet.r3_res,_ = mainLLT.preReading(-c.PrereadingConfig.stepDown)
				printg('Level 3..',Wet.r3_res)

				#R4 = -3mm
				Wet.r4_res,_ = mainLLT.preReading(-c.PrereadingConfig.stepDown)
				printg('Level 4..',Wet.r4_res,_)

				#R5 = -4mm
				Wet.r5_res,_ = mainLLT.preReading(-c.PrereadingConfig.stepDown)
				printg('Level 5..',Wet.r5_res,_)

				#R6 = -110
				Wet.r6_res,_ = mainLLT.preReading(Wet.expectedSatZ[tip]-(c.p.get_motor_pos(0)/100.0))
				printg('Level 6..',Wet.r6_res,_)

				#Saturated Res & Z
				Wet.satZ, Wet.satRes, Wet.satZlimit, Wet.saturated = mainLLT.findSaturation(Wet.zero, tip)
				printg('SaturatedRes:',Wet.satRes,'at z:',Wet.satZ)

				c.move_abs_z(target+30,100,300,0)
				t_tot = time.time() - t_tot1

				# DRY DATA PUSH
				n += 1
				wrapper = '{}'
				for i in range(43-1): wrapper += ',{}' 
				back_write(wraps([wrapper.format(
					x, n,
					dates,
					'P'+str(tip),
					zeros,
					p1_init,
					atm_press,
					res_init,
					c.PLLDConfig.stem_vel,
					c.PLLDConfig.stem_acc,
					c.PLLDConfig.flow,
					Dry.types,
					Dry.useDynamic,
					Dry.pressThres,
					Dry.pressLimit,
					Dry.resThres,
					Dry.resLimit,
					Dry.press_trig,
					Dry.res_trig,
					Dry.LLT_freq,
					Dry.res,
					res_init - Dry.res,
					zeros - Dry.zero,
					Dry.p1,
					Dry.p2,
					Dry.p1 - p1_init,
					Dry.p2 - atm_press,
					Dry.preRead_freq,
					Dry.r1_res,
					Dry.r2_res,
					Dry.r3_res,
					Dry.r4_res,
					Dry.r5_res,
					Dry.r6_res,
					Dry.expectedSatZ[tip],
					Dry.satRes,
					Dry.satZ,
					Dry.satZlimit,
					Dry.saturated,
					Dry.t_operation,
					t_tot
					)]),filename)
				
				# WET DATA PUSH
				n += 1
				wrapper = '{}'
				for i in range(43-1): wrapper += ',{}' 
				back_write(wraps([wrapper.format(
					x, n,
					dates,
					'P'+str(tip),
					zeros,
					p1_init,
					atm_press,
					res_init,
					c.PLLDConfig.stem_vel,
					c.PLLDConfig.stem_acc,
					c.PLLDConfig.flow,
					Wet.types,
					Wet.useDynamic,
					Wet.pressThres,
					Wet.pressLimit,
					Wet.resThres,
					Wet.resLimit,
					Wet.press_trig,
					Wet.res_trig,
					Wet.LLT_freq,
					Wet.res,
					res_init - Wet.res,
					zeros - Wet.zero,
					Wet.p1,
					Wet.p2,
					Wet.p1 - p1_init,
					Wet.p2 - atm_press,
					Wet.preRead_freq,
					Wet.r1_res,
					Wet.r2_res,
					Wet.r3_res,
					Wet.r4_res,
					Wet.r5_res,
					Wet.r6_res,
					Wet.expectedSatZ[tip],
					Wet.satRes,
					Wet.satZ,
					Wet.satZlimit,
					Wet.saturated,
					Wet.t_operation,
					t_tot
					)]),filename)

			printg('Eject Phase..')
			# Eject phase
			align(0,ejectpos,pick_target+10,pick_target+85)
			eject()
			eject()
	align(0, next_pickpos, pick_target+50)



# ALWAYS RE-SETUP EVERY TIME CHANNEL IS CHANGED
def hi_mode(chipNumber):
	pr.pregv.set_drain_enable(0,1)
	pr.pregv.set_drain_out(0,1)
	time.sleep(1) # delay 1 second to make sure selenoid valve is fully open/close. This is code operation without overshoot on valve voltage input.
	pr.pregv.set_drain_out(0,0.83)
	c.config_set(0,8.333560349)
	c.config_set(1,8.708193195)
	
def low_mode(chipNumber):
	pr.pregv.set_drain_enable(0,0)
	c.config_set(0,0.7802958402)
	c.config_set(1,0.8206705656)

def PID_mini_ereg_check():
    check_preg()
    testname = 'PID_mini_ereg_check'
    t1 = time.time()
    test_start_print(testname,t1)
    status = c.cek_pid_ereg()
    if status:
        try:
            status = int (raw_input('Grafik bagus? |1: Ya, 0: Tidak|:  '))
        except ValueError:
            print 'invalid input'
        while(status==0):
            print 'Set PID mini'
            c.set_pid_ereg()
            c.cek_pid_ereg()
            status = raw_input('Grafik bagus? |1: Ya, 0: Tidak, 2: Menyerah|:  ')
            status = int(status)
    status = True if status == 1 else False
    test_done_print(testname,status,t1,time.time())
    return status

def asdi_check(vol, tip=1000, log=0): # check both aspirate and dspense
	print '\n\t\t***ASPIRATE***'
	aspirate(vol, tip, log)
	time.sleep(1)
	print '\n\t\t***DISPENSE***'
	dispense(vol, tip, log)


# VISUALIZATION
cora.init()
def printr(*args):
	text = ''
	for t,i in enumerate(args): text += str(i)+' ' if t+1 <= len(args) else str(i)
	print cora.Fore.RED+cora.Style.BRIGHT+text+cora.Style.RESET_ALL

def printb(*args):
	text = ''
	for t,i in enumerate(args): text += str(i)+' ' if t+1 <= len(args) else str(i)
	print cora.Fore.CYAN+cora.Style.BRIGHT+text+cora.Style.RESET_ALL

def printg(*args):
	text = ''
	for t,i in enumerate(args): text += str(i)+' ' if t+1 <= len(args) else str(i)
	print cora.Fore.GREEN+cora.Style.BRIGHT+text+cora.Style.RESET_ALL

def printy(*args):
	text = ''
	for t,i in enumerate(args): text += str(i)+' ' if t+1 <= len(args) else str(i)
	print cora.Fore.YELLOW+cora.Style.BRIGHT+text+cora.Style.RESET_ALL
