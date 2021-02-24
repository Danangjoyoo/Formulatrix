### Script Version : v2021.2.24.1614158113
from misc import *
import FloDeck_stageV2_212 as deck
import pregx as pr
import channelx_stageV2_212 as c
import time, math, sys
from tabulate import tabulate
import pandas as pd
from pandas import read_csv
import threading, winsound, os, sys, signal
import keyboard as kb, string, numpy as np, colorama as cora, random as rd
import matplotlib.pyplot as plt

w_eng_value = 4.5454545454
B_zero = 702.4545+9*w_eng_value
A_zero = 264.0000
B = [(B_zero-i*9*w_eng_value) for i in range(0,8)]
A = [(A_zero-i*9*w_eng_value) for i in range(0,8)]

len_length = 0
berat_now = 0
fname = 'Weightscale.txt'
before_asp = 0

P200_picktip_z = -126
P20_picktip_z = -136
#Zpick   = [-114,-104]

pick_targets    = {20: -199, 200: -191, 1000: -143.5}
asp_targets     = {20: -170, 200: -160, 1000: -110}
dsp_targets     = {20: -120, 200: -130, 1000: -80}
safes           = {20: -95, 200: -85, 1000: -20}
evades          = {20: -20, 200: -30, 1000: 0}


def move_deck(pos):
    w.move_wdeck_abs(pos)

def align (rack,well,z=-40,evade=-40,tare=0):
    global vel_z, acc_z
    if tare ==1:
        c.p.tare_pressure()
    c.set_estop_abort(300)
    c.set_collision_abort(100)
    deck.set_abort_estop()
    if c.get_motor_pos() < evade:
        if c.move_abs_z(evade,vel_z,acc_z):
            print('matane')
            deck.align_deck(rack,well)
    else:
        deck.align_deck(rack,well)
    c.move_abs_z(z,vel_z,acc_z)
    c.clear_estop()
    return True

def align_plld (rack,well,target=-40,depth=-85,evade=-20,tare=1):
    global before_asp
    if tare ==1:
        c.p.tare_pressure()
    c.set_estop_abort(300)
    deck.set_abort_estop()
    if c.p.get_encoder_position(0)/c.stem_eng < evade:
        c.move_abs_z(evade,100,750)
    deck.align_deck(rack,well,0)
    
    file_len()
    #wait_nline()
    default_weight = berat_now
    print("default weight", default_weight)
    before_asp = default_weight
    time.sleep(0.5)
     
    
    c.start_flow(200)#15
    deck.wait_moves([0,1])
    c.move_abs_z(target,100,750)
    c.set_plld()
    c.move_abs_z(depth,15,500)
    
    pos =  c.get_motor_pos()
    sensor = c.get_triggered_input(1)
    print(sensor,"dfasdfsadfasdfasdfsdf")
    c.abort_flow()
    c.clear_motor_fault()
    c.clear_abort_config(1)
    c.clear_abort_config(6)
    if sensor == 2 or sensor ==256 or sensor== 258:
        result = True
        c.DLLT_start()

    else:
        result = False
        c.move_rel_z(1,50,750)
    c.clear_estop()

    return result

def align_wlld (rack,well,target=-40,depth=-100,evade=-40):
    c.set_estop_abort(300)
    deck.set_abort_estop()
    if c.p.get_encoder_position(0)/c.stem_eng < evade:
        c.move_abs_z(evade,vel_z,acc_z)
    deck.align_deck(rack,well,0)
    c.set_wlld_abort(200)
    deck.wait_moves([0,1])
    c.move_abs_z(target,vel_z,acc_z)
    c.move_abs_z(depth,15,500)
    pos =  c.get_motor_pos()
    sensor = c.get_triggered_input(1)
    print('sensor wlld', sensor)
    c.clear_motor_fault()
    c.clear_abort_config(1)
    if sensor == 256:
        result = True
        c.DLLT_start()
    else:
        result = False
        c.move_rel_z(3,50,750)
    c.clear_estop()
    return result

def initialization():
    print("System Start ... ")
    parkingBeep(True)
    #w.pump_power(1)
    abort_flow()
    tare()
    c.clear_abort_config() #abort all
    c.clear_motor_fault()
    c.clear_estop()
    deck.clear_motor()
    c.enable_z()
    c.home_z()
    c.move_abs_z(-20,10,100)
    time.sleep(2)
    #w.home_wdeck()
    deck.home_all_motor()
    time.sleep(2)
    pr.default_preg()
    speedMode('m')
    parkingBeep(False)
    #time.sleep(2)
    #aspirate(200)
    #time.sleep(2)
    #dispense(200)
    #align(A[0]+100)
    #c.eject()

    print("System Ready\n")

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
    print('')
    print('===================================================')
    print('~~~  '+str(string)+'\t\t\t ---START--- ')
    print('===================================================')
    print(str(pt)+'\n')

def test_done_print(string,status,t1,t2):
    pt = time.strftime('%Y_%m_%d_%H:%M:%S', time.localtime(t2))
    if status:
        print('')
        print('===================================================')
        print('~~~  '+str(string) + '\t\t\t === PASS ===')
        print('===================================================')
        print(str(pt))

    else:
        print('')
        print('===================================================')
        print('~~~  '+str(string) + '\t\t\t XXX FAIL XXX')
        print('===================================================')
        print(str(pt))

    print('Elapsed time: ',str(t2-t1)+'\n')


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

    print('P1_avg: ',P1_avg)
    print('P2_avg: ',P2_avg)
    print('Col_avg: ' ,Col_avg)
    print('Res_avg: ',Res_avg)
    print('Br_avg: ',Br_avg)

    result = [P1_avg,P2_avg,Col_avg,Res_avg,Br_avg]

    status = True if result[0] and result[1] and result[2] and result[3] and result[4] else False
    sensor_OK = status
    if status:

        print('P1\t|P2\t|Col\t|Res\t|Br')
        print(str(val[0])+'\t|'+str(val[1])+'\t|'+str(val[2])+'\t|'+str(val[3])+'\t|'+str(val[4]))
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

    print(st_2000,"2k")
    print(st_510,"510")
    print(st_120,"120")
    test_done_print(testname,status,t1,time.time())
    return status


def picktip(pos='None',target=None,safe=None,tip=None,nextPosOnly=False):
    deck.setZeroDeckMode(tip)
    if not target: target = globals()['pick_targets'][tip]
    if not safe: safe = globals()['safes'][tip]
    if not nextPosOnly:
        status, nextpos, lastpos = False, None, None
        maxtry=3
        n = 1
        if pos in deck.wellname:
            while(not status):
                if n > 1:
                    #eject()
                    pos = deck.wellname[deck.wellname.index(pos)+1]            
                align(0,pos,target+15,safe)                
                status = c.setUp_picktip(target,tip)
                n += 1
                lastpos = pos
                print("POS! :", pos)
                try: nextpos = deck.wellname[deck.wellname.index(pos)+1]
                except: nextpos = deck.wellname[0]
                if n>maxtry: break
                lastpos = pos
        else:
           status = c.setUp_picktip(target, tip)
           nextpos = 'NONE'
           lastpos = 'NONE'
        return [status,nextpos,lastpos]
    else:
        if pos in deck.wellname:
            try: nextpos = deck.wellname[deck.wellname.index(pos)+1]
            except: nextpos = deck.wellname[0]
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
    print('PLLD DONE', val)
    return val

def ASP(vol):
    c.aspiratexxx(vol,150,10,200,5000)
    
def DISP(vol):
    c.dispensexxx(vol,100,10,200,5000)

def aspirate(vol,tip=200,log=False):
    maxflow = 100#special case
    minflow = 5
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
    if vol<1200:
        c.aspirate(vol,maxflow,minflow,log,tip)
    else:
        print('Vol too large')
    return True

def dispense(vol,tip=200,log=0,bubble_detect=0):
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
    if bubble_detect:
        vol = vol*1.5
        c.p.set_air_transfer_detect_params(1,thres,1000,250,1)
    c.dispense(vol,maxflow,minflow,log,tip)

    return True
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
        status = int (input('Grafik bagus? |1: Ya, 0: Tidak|:  '))
        while(status==0):
            print('Set PID mini')
            c.set_pid_ereg()
            c.cek_pid_ereg()
            status = int (input('Grafik bagus? |1: Ya, 0: Tidak, 2: Menyerah|:  '))
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
    print('Phase 1 done, result: ', phase_1_status)


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

    print('Phase 2 done, result: ', phase_2_status)


def abort_flow():
    c.abort_flow()

def full_stem_leak(full=1):
    check_preg()
    testname = 'full_stem_leak'
    t1 = time.time()
    test_start_print(testname,t1)
    c.move_abs_z(0,100,100)
    if full==1:
        ready = input('PUT CLOGGED TIP IN 0,A12   -- enter to continue')
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
        ready = input('PUT TIP IN B[6] and SBS water at A[7]   -- enter to continue')
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
    print('dis' , dist)
    wawik()
    c.move_abs_z(0,100,100)
    status = True if dist <= tol else False
    test_done_print(testname,status,t1,time.time())
    c.tare_done_req = True
    return status

def wawik(rack=0,source='A1',target=-100,Deck=2,well='B3'):
    z = c.get_motor_pos()
    c.move_abs_z(0,100,100)
    align(Deck,well,-100)
    c.set_collision_abort(23)
    c.move_abs_z(target-50,20,100)
    c.clear_abort_config(1)
    c.clear_motor_fault()
    c.move_rel_z(3,5,100,0)
    c.start_flow(150)
    time.sleep(1)
    c.abort_flow()
    c.set_collision_abort(23)
    c.move_abs_z(target-50,20,100)
    c.clear_abort_config(1)
    c.clear_motor_fault()
    c.move_rel_z(3,5,100,0)
    c.move_abs_z(0,100,100)
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
    print('menu()\t: show functions ')
    print('phase_1()\t: 1st phase MFQC')
    print('phase_2()\t: 2nd phase MFQC')
    print('phase_3()\t: 2nd phase MFQC')
    print('sensor_check()')
    print('resistance_check()')
    print('tubing_leak_check()')
    print('set_mini_ereg()')
    print('PID_mini_ereg_check()')
    print('calibrate_extra_vol()')

def eject(**kargs):
    if kargs:
        if 'tip' in kargs and 'ejectpos' in kargs:
            if kargs['tip'] == 1000 and kargs['ejectpos'] in deck.wellname:
                align(0,kargs['ejectpos'],-120)
            else: align(1,'D2',-120)
        else: align(1,'D2',-120)
    else: align(1,'D2',-120)
    c.start_flow(50)
    c.eject()
    abort_flow()

def phase_3():
    align(1,'D5')
    c.eject()
    full_stem_leak()
    align(1,'D5')
    c.eject()
    print('Put P200 tip in 0,A1')
    input('Enter to continue')
    align(0,'A1')
    picktip()
    align(0,'A1')
    print('Put SBS with water in rack 1, A12')
    input('Enter to continue')
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
            print('wait')
            time.sleep(10)
            c.stop_logger()
            align(1,i,-90)
            c.dpc_off()
            c.wlld(-110)
            c.DLLT_start()
            dispense(x,200)
            c.DLLT_stop()
            align(1,i,-50)
            print('done')
            wawik()
def retract_press(travel=3):
    c.start_flow(50)
    c.move_rel_z(travel,1,100,1)
    abort_flow()
    
def bubble_retract(vol,travel=3):
    c.p.set_air_transfer_detect_params(1,20,1000,250,1)
    c.move_rel_z(travel,1,100,0)
    dispense(vol,200)
    c.p.set_air_transfer_detect_params(0,2,1000,250,1)
    
def loop_bubble_det(vol,tip,loop=1):
    n = 0
    extra_dispense = {20:10,200:20}
    for i in range(loop):
        c.phase1_air_tr = False
        c.wlld(-10)
        c.p.set_air_transfer_detect_params(0,0,0,0,0)
        aspirate(vol,tip)
        print(1)
        c.p.set_air_transfer_detect_params(1,20,1000,250,1)
        print(2)
        c.dispense(vol+extra_dispense[tip],0.6*vol,10)
        print(3)
        c.move_rel_z(5,4,50)
        c.move_abs_z(-100,100,100)
        print(4)
        if c.phase1_air_tr:
            n += 1
        time.sleep(2)
        print("Succses,Loop ", n,i+1,"/",loop)
        #this works 20210127

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
    
def wait_nline():
    global found_nline
    found_nline = False
    timeout = 20
    file_len()
    start = len_length
    i=0
    while True:
        file_len()
        if start == len_length:
            time.sleep(1)
            
        else:
            val = last_val()
            found_nline = True
            return val
            break
        i+=1
        if i==timeout:
            val = last_val()
            return val
            print("TO - val use previous")
            break

    print(" Found New Val")
    

def zeroing():
    c.home_z()
    deck.home_all_motor()
    
def tare():
    c.tare_pressure()
    
def gravimetric(vol):
    global before_asp
    print("==================================================")
    print("                 GRAVIMETRIC START")
    print("==================================================")
    
    time.sleep(1)
    
    align(0,'A12')
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
    
    
    print("Aspirate Start")
    aspirate(vol)
    
    c.DLLT_stop()
    
    c.move_abs_z(-40,30,100)
    
    wait_nline()
    last_val() #value after asp
    after_asp = berat_now
    print("Weight after ASP", after_asp)
            
    ASP_Weight = abs(after_asp-before_asp)
    print("Aspirate weight =", ASP_Weight)
    
    #c.move_abs_z(-50,30,100)
    
    align_wlld(2,'F12')
    
    #c.DLLT_start()  
    print("Dispense start")
    dispense(vol)
    c.DLLT_stop()

    c.move_abs_z(-40,30,100)
    
    wait_nline()
    last_val() #value after asp
    after_disp = berat_now
    print("Weight after DISP", after_disp)
            
    DISP_Weight = abs(after_disp-after_asp)
    print("Dispense weight =", DISP_Weight)
    
    time.sleep(1)
    
    print("Eject Tip")
    align(0,'A1')
    c.move_abs_z(-100,30,100)
    
    eject()
    
    align(1,'F12')
    
    print("==================================================")
    print("                 GRAVIMETRIC DONE")
    print("==================================================")

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
        
    print('vol\t: ', senn)
    print('res\t: ', ress)
    
def nimbang_1ml(vol,log=1):
    target = -86
    safe = -60
    above = 0
    jet = 1+target
    
    #c.move_abs_z(above,50,100)
    c.move_abs_z(safe,50,100)
    tare = wait_nline()
    c.move_abs_z(target,50,100)
    time.sleep(0.5)
    aspirate(vol,1000,log)
    sensed =c.Sensed_vol
    c.move_abs_z(above,100,100)
    print(tare)
    weight = tare-wait_nline()
    #if raw_input(' enter = dispense ')=='':
    time.sleep(3)
    if True: #why
        c.move_abs_z(jet,50,100)
        if vol<50: 
            dispense(vol+10,1000,log)
        else:
            dispense(vol+0.01*vol,1000,log)
        dispense(vol/2,1000,0)#blow
        #dispense(100,1000)
        c.move_abs_z(above,50,100)
    return weight,sensed
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
    print(tare)
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
            print(weight[i]," - \t", sensed[i])
        time.sleep(1)
def yy():
    vol = [3,2,1.5,1]
    weight,sensed= [],[]
    for i in vol:
        actual,detected = nimbang_low(i,20,0)
        weight.append(actual)
        sensed.append(detected)
        for i,x in enumerate(weight):
            print(weight[i]," - \t", sensed[i])
        time.sleep(1)      
def zz():
    vol = [1030,202,24,8.7]
    weight,sensed= [],[]
    for i in vol:
        actual,detected = nimbang_low(i,0)
        weight.append(actual)
        sensed.append(detected)
        for i,x in enumerate(weight):
            print(weight[i]," - \t", sensed[i])
        time.sleep(1)
    
        
def hi_mode():
    pr.pregv.set_drain_enable(0,1)
    pr.pregv.set_drain_out(0,1)
    time.sleep(1) # delay 1 second to make sure selenoid valve is fully open/close. This is code operation without overshoot on valve voltage input.
    pr.pregv.set_drain_out(0,0.83)
    c.config_set(0,9.12831301571)
    c.config_set(1,9.01990355963)
    #ExtraOffsetAsp', 0.1636429876089096
    #ExtraOffsetDsp', -0.03153923526406288
    #ExtraScaleAsp', 0.11045452207326889
    #ExtraScaleDsp', 0.1395275592803955
    
def low_mode():
    pr.pregv.set_drain_enable(0,0)
    c.config_set(0,0.626109444712)
    c.config_set(1,0.651305043306)

'''
OrderedDict([('cal_static_asp', 0.6261094212532043), ('cal_static_dsp', 0.651305
0198554993), ('flow_drift_asp', 3.343819116707891e-05), ('flow_drift_dsp', -2.76
43198336591013e-05), ('DpHighThreshold', 1.0), ('DpLowThreshold', 0.5), ('ExtraO
ffsetAsp', 0.1636429876089096), ('ExtraOffsetDsp', -0.03153923526406288), ('Extr
aScaleAsp', 0.11045452207326889), ('ExtraScaleDsp', 0.1395275592803955), ('Slope
Threshold', 0.0010000000474974513), ('vicous_scale', 0.0027199999894946814), ('v
iscous_offset', 0.17599999904632568), ('SensorId', 105L)])
        
'''

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


def yoyo(): #temporary for debugging dpc
    c.plld(-130)
    c.move_rel_z(-1,30,30)
    c.start_logger()
    aspirate(15,20)
    c.dpc_on()
    c.move_rel_z(10,75,750)
    time.sleep(5)
    #c.dpc_off
    c.stop_logger()
    #dispense(25,20)

    
    

################### IMPROVEMENTS ################################ IMPROVEMENTS ################################################## IMPROVEMENTS #################################################
# IMPROVEMENTS ######################### IMPROVEMENTS ################################ IMPROVEMENTS ################################################## IMPROVEMENTS ############################
################### IMPROVEMENTS ################################ IMPROVEMENTS ################################################## IMPROVEMENTS #################################################
# IMPROVEMENTS ######################### IMPROVEMENTS ################################ IMPROVEMENTS ################################################## IMPROVEMENTS ############################
################### IMPROVEMENTS ################################ IMPROVEMENTS ################################################## IMPROVEMENTS #################################################

# DECKS
A1,A2,A3,A4,A5,A6,A7,A8,A9,A10,A11,A12 = [A for A in deck.wellname[0:12]]
B1,B2,B3,B4,B5,B6,B7,B8,B9,B10,B11,B12 = [B for B in deck.wellname[12:24]]
C1,C2,C3,C4,C5,C6,C7,C8,C9,C10,C11,C12 = [C for C in deck.wellname[24:36]]
D1,D2,D3,D4,D5,D6,D7,D8,D9,D10,D11,D12 = [D for D in deck.wellname[36:48]]
E1,E2,E3,E4,E5,E6,E7,E8,E9,E10,E11,E12 = [E for E in deck.wellname[48:60]]
F1,F2,F3,F4,F5,F6,F7,F8,F9,F10,F11,F12 = [F for F in deck.wellname[60:72]]
G1,G2,G3,G4,G5,G6,G7,G8,G9,G10,G11,G12 = [G for G in deck.wellname[72:84]]
H1,H2,H3,H4,H5,H6,H7,H8,H9,H10,H11,H12 = [H for H in deck.wellname[84:96]]

stageSpd = 'slow'
def speedMode(mode=None):
    if mode == 's' or mode == 'default' or mode == 'slow' or mode == 0:
        globals()['stageSpd'] = 'slow'
        deck.setTravelMode('s')
        setVelAcc_z_mode('s')
        print('Motor Speed: Slow')
    elif mode == 'm' or mode == 'medium' or mode == 1:
        globals()['stageSpd'] = 'medium'
        deck.setTravelMode('m')
        setVelAcc_z_mode('m')        
        print('Motor Speed: Medium')
    elif mode == 'f' or mode == 'fast' or mode == 2:
        globals()['stageSpd'] = 'fast'
        deck.setTravelMode('f')
        setVelAcc_z_mode('f')
        print('Motor Speed: Fast')
    else:        
        if globals()['stageSpd'] == 'slow': speedMode('m')
        elif globals()['stageSpd'] == 'medium': speedMode('f')
        elif globals()['stageSpd'] == 'fast': speedMode('s')

vel_z = 75
acc_z = 500

# CHANNEL
def setVelAcc_z_mode(mode):
    global vel_z, acc_z; mode = str.lower(mode)
    if mode == 's' or mode == 'default':
        vel_z = 75; acc_z = 500
    elif mode == 'm':
        vel_z = 100; acc_z = 500
    elif mode == 'f':
        vel_z = 150; acc_z = 1000
speedMode('m')

def manualStem():
    c.clear_motor_fault()
    c.clear_estop()
    col_init = c.sensing.col()
    r_init = c.sensing.res()
    x, y = deck.current_pos()
    z = c.get_motor_pos()
    printr('Inital Value\t: x,y,z = {}\tcol = {}\tres = {}'.format((x,y,z), col_init, r_init))
    printy('Use alt+up/down to control Z pos')
    printy('Use capslock+up/down/left/right to control deck pos')
    printy('+CTRL to speed up ======= press ESC to terminate..')
    while True:
        if kb.is_pressed('ESC'): break
        if kb.is_pressed('down+alt'): z -= 3 if kb.is_pressed('CTRL') else 0.5
        elif kb.is_pressed('up+alt'): z += 3 if kb.is_pressed('CTRL') else 0.5
        if kb.is_pressed('up+capslock'): y -= 3 if kb.is_pressed('CTRL') else 0.5
        elif kb.is_pressed('down+capslock'): y += 3 if kb.is_pressed('CTRL') else 0.5
        if kb.is_pressed('right+capslock'): x -= 3 if kb.is_pressed('CTRL') else 0.5
        elif kb.is_pressed('left+capslock'): x += 3 if kb.is_pressed('CTRL') else 0.5
        col = round(c.sensing.col(),1)
        r = round(c.sensing.res(),1)
        c.p.move_motor_abs(0,z*5.0,100*5.0,100*5.0,10000*5.0)
        deck.d.move_motor_abs(0,x*4.54545454,50*4.54545454,100*4.54545454,20*4.54545454)
        deck.d.move_motor_abs(1,y*4.54545454,50*4.54545454,100*4.54545454,20*4.54545454)
        if c.p.read_sensor(c.SensorID.COLLISION) < 1000:
            c.clear_motor_fault()
            c.clear_estop()
        print('\rz: '+str(round(c.get_motor_pos(),2))+'| Col = '+str(col)+' | Res = '+str(r)+' | Deck: '+str(deck.current_pos())+'\r', end=' ')
    printg('\nManual Stem Terminated')
    c.abort_flow()
    c.clear_motor_fault()

# PLATE READER
class Plate():
    @staticmethod
    def autoposAsp(vol,row='E'): #Referensi dari tabel Working Dye
        row = str.upper(row)
        if vol <= 2:        #WD 4
            pos = row+'12'
        elif 2 < vol <= 8:  #WD 3
            pos = row+'10'
        elif 8 < vol <= 40: #WD 2
            pos = row+'7'
        else:               #WD 1
            pos = row+'2'
        return pos

    @staticmethod
    def maps(realPos=False):
        maps = []
        for idx_rows,rows in enumerate([char for char in string.ascii_uppercase[:8]]):
            maps.append([])
            for cols in range(12):
                if realPos: maps[idx_rows].append(rows+str(cols+1))
                else: maps[idx_rows].append(' ')
        return maps

    @staticmethod
    def mapMarking(maps, pos, val,showMap=False):
        for i in enumerate(Plate.maps(realPos=True)):
            for ii in enumerate(i[1]):
                if pos == ii[1]: maps[i[0]][ii[0]] = val
        if showMap:
            for i in maps: print(i)
        return maps

    @staticmethod
    def showMap(rawMaps):
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

    @staticmethod
    def fill(*inputs):
        operation, simulation = False, False
        list_vol, aspPos, dspPos, complete_vols = [], [], [], []
        tip, iter_per_vol, pickpos = None, None, None
        tipMap, aspMap, dspMap = Plate.maps(),Plate.maps(),Plate.maps()
        if inputs:
            if inputs[0] == 's':
                printg("\t\t*** SIMULATION MODE ***\t\t")
                simulation = True
                inputs = None
            else:
                print(inputs)
                operation = True
                list_vol        = inputs[0]
                tip             = inputs[1]
                iter_per_vol    = inputs[2]
                pickpos         = inputs[3]
                aspPos_state    = inputs[6]
                simulation      = inputs[7]
                complete_vols   = [i for i in list_vol for ii in range(iter_per_vol)]
                print(complete_vols)

                if aspPos_state == 'a' or aspPos_state == 'auto':
                    aspPos_state = 'auto'
                    aspPos = [Plate.autoposAsp(i) for i in complete_vols]
                elif aspPos_state == 'n' or aspPos_state == 'normal':
                    aspPos_state = 'normal'
                    for i in range(len(complete_vols)):
                        if i == 0:
                            aspPos.append(inputs[4])
                        else:
                            aspPos.append(picktip(aspPos[i-1], tip=tip, nextPosOnly=True))
                else:
                    aspPos = [inputs[4]]*len(complete_vols)
                
                for i in range(len(complete_vols)):
                    if i == 0:
                        dspPos.append(inputs[5])
                    else:
                        dspPos.append(picktip(dspPos[i-1], tip=tip, nextPosOnly=True))

                if not simulation:
                    operation = True

        if not inputs:
            if not simulation:
                inputs = input("Pipetting Mode: Increment/Copy/CustomVol/Simulation (i/c/v/s) >> ")
            else:
                inputs = input("Pipetting Mode: Increment/Copy/CustomVol/Simulation (i/v/s) >> ")
            if str.lower(inputs) == 'i':
                printb("   =================== increment Filling Mode Activated ===================")
                inputs = avoidInpErr.reInput('StartVol, EndVol, range >> ',avoidInpErr.test_rangeVol); inputs = inputs.split(',')
                list_vol =  np.arange(float(inputs[0]),float(inputs[1]),float(inputs[2]))
                inputs = str.upper(avoidInpErr.reInput('Tip, Iter/tip, Pickpos, AspPos, DspPos >> ', avoidInpErr.test_plateFill)); inputs = inputs.split(',')
                aspPos_state = str.lower(input('Asp Pos Mode (auto/normal/lock) >> '))
                if not simulation:
                    Plate.fill(list_vol,int(inputs[0]), int(inputs[1]), inputs[2], inputs[3], inputs[4],aspPos_state,False)
                else:
                    Plate.fill(list_vol,int(inputs[0]), int(inputs[1]), inputs[2], inputs[3], inputs[4],aspPos_state,True)
            elif str.lower(inputs) == 'v':
                printb("   =================== Custom Vol Mode Activated ===================")
                inputs = avoidInpErr.reInput('Desired Vol >> '); inputs = inputs.split(',')
                list_vol =  [float(i) for i in inputs]
                inputs = str.upper(avoidInpErr.reInput('Tip, Iter/vol, Pickpos, AspPos, DspPos >> ', avoidInpErr.test_plateFill)); inputs = inputs.split(',')
                aspPos_state = str.lower(input('Asp Pos Mode (auto/normal/lock) >> '))
                if not simulation:
                    Plate.fill(list_vol,int(inputs[0]), int(inputs[1]), inputs[2], inputs[3], inputs[4],aspPos_state, False)
                else:
                    Plate.fill(list_vol,int(inputs[0]), int(inputs[1]), inputs[2], inputs[3], inputs[4],aspPos_state,True)
            elif str.lower(inputs) == 'c':
                if simulation:
                    printr("**Simulation isn't available for Plate Copy\n**Please reinput operation type..")
                    Plate.fill()
                else:
                    printb("   =================== Plate Copy Mode Activated ===================")
                    inputs = str.lower(input("Insert Pickpos, tip >> ")); inputs = inputs.split(',')
                    Plate.plate_copy(inputs[0],int(inputs[1]))
            elif str.lower(inputs) == 's':
                #printg("\t\t*** SIMULATION MODE ***\t\t")
                Plate.fill('s')
            else:
                printr("Insert Only 1 mode! i/c/v/s")
                Plate.fill()

        if operation:
            sim_pickpos = pickpos
            for x,i in enumerate(complete_vols):
                tipMap = Plate.mapMarking(tipMap,sim_pickpos,i)
                sim_pickpos = picktip(sim_pickpos, tip=tip, nextPosOnly=True)
                aspMap = Plate.mapMarking(aspMap, aspPos[x],i)
                dspMap = Plate.mapMarking(dspMap, dspPos[x],i)
            printb("\n\n*** ---------------------------- Plate Pipetting Preview ---------------------------- ***")
            print("\t--TIP MAP--")
            Plate.showMap(tipMap)
            print("\n\t--ASPIRATE MAP-- | Mode: ", aspPos_state)
            Plate.showMap(aspMap)
            print("\n\t--DISPENSE MAP--")
            Plate.showMap(dspMap)
            print("Volumes\t\t:", list_vol)
            print("Tip\t\t:", tip)
            print("Iter/vol\t:", iter_per_vol)
            print("Aspirate Mode\t:", aspPos_state)
            print("AspPos:", inputs[4], '| DspPos:', inputs[5])
            print('Pickpos', pickpos)
            volume, operation = Plate.volScaling(complete_vols,tip,'scale'); print('Volulme Calibration\t:',operation)
            deck.setZeroDeckMode(tip)

            if not simulation:
                printr('Enter to continue... ');input()
                speedMode('plate')
                starttime   = time.time()
                pick_target = globals()['pick_targets'][tip]
                asp_target  = globals()['asp_targets'][tip]
                dsp_target  = globals()['dsp_target'][tip]
                evade       = evades[tip]
                target      = globals()['asp_target'][tip]
                safe        = globals()['safes'][tip]

                print(volume)
                target = dspPos
                source = aspPos

                next_pickpos = pickpos
                for x,i in enumerate(complete_vols):
                    picktipstat = picktip(next_pickpos, tip=tip)
                    pickpos = next_pickpos
                    next_pickpos = picktipstat[1]
                    ejectpos = picktipstat[2]
                    print(pickpos, next_pickpos)
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
                print("\t--TIP MAP--");_,marks=Plate.showMap(tipMap);print("\n\t--ASPIRATE MAP-- | Mode: ", aspPos_state);Plate.showMap(aspMap);print("\n\t--DISPENSE MAP--");Plate.showMap(dspMap)
                printb('!!! OPERATION SUMMARY !!!')
                print('Elapsed Time\t:', elapsedtime)
                print('Tip used\t:', marks)
                print('Calibration Type\t:', operation)

    @staticmethod
    def volCalibrate(vol,tip=20):
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
            volout = float(i)*scale+offset
            newvol.append(volout)
        return newvol

    @staticmethod
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
                operation = 'sca-off'
                print('Scale Offset Operation')
                newvols = Plate.volCalibrate(vols, tip)
        elif str.lower(opr) == 'sca-off' or str.lower(opr) == 'scale' or str.lower(opr) == 'scaoff' or str.lower(opr) == 's':
            operation = 'Sca-Off'
            print('Scale Offset Operation')
            newvols = Plate.volCalibrate(vols, tip)
        return newvols, operation

    @staticmethod
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

    @staticmethod
    def plate_copy(pickpos='A1',tip=200,protocolname='MAP0.csv'):
        starttime=time.time()
        safe_h_dsp = -100
        safe_h_asp = -100
        lld_asp = -125  
        lld_dsp = -127
        pick_targets    = {20   :-134,  200     :-125,  1000    :-127}
        targetpick = pick_targets[tip]
        protocol = read_protocol(protocolname)
        volume = vol_calibrate(protocol[0],tip)
        print(volume)
        target = protocol[1]
        source = protocol[2]
        next_pickpos = pickpos
        for x,i in enumerate(source):
            #align(0,pickpos)
            picktipstat = picktip(next_pickpos,targetpick)
            pickpos = next_pickpos
            next_pickpos = picktipstat[1]
            ejectpos = picktipstat[2]
            print(pickpos, next_pickpos)
            if picktipstat[0]:
                #align(1,source[x],-100,-40,1)
                #PLLD()
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
        print("Timeit = ", elapsedtime)

plate = Plate

plotter = Plotter(c.p)
cplotter = CPlotter(c.p)

def aa(counter=False, dur=1):
    if not counter:
        aa(2)
        printy("First Start Flow 10uL/s in 3 seconds")
        c.start_flow(10)
        aa(2)
        printy("Flow Aborted")
        c.abort_flow()
        aa(5)
        printy("Aspirate 50")
        aspirate(50)
        aa(3)
        printy("Dispense 50")
        dispense(50)
        printy("Second Start Flow 10uL/s in 3 seconds")
        c.start_flow(10)
        aa(5)
        printy("Flow Aborted")
        c.abort_flow()
    else:
        for i in range(counter):
            print('waiting..',i)
            time.sleep(dur)

# LLD/LLT Script
class mainLLD():
    class Operation():
        def __init__(self,types):
            self.types = types
            self.zero = 0
            self.lld_freq = c.PLLDConfig.freq
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
            self.NormalZ_trig = None
            self.HardZ_trig = None
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
            self.expectedSatZ = {20: -4, 200: -5, 1000: -6}
            self.satRes = 0
            self.satZ = 0
            self.satZlimit = 0
            self.saturated = False
            self.t_operation = 0
            self.TriggeredFirst = None
            self.lowSpeed_flow = 15

        def reset(self):
            print(self.types,'has been reset..')
            self.surfaceFound = False
            self.press_trig = False
            self.pressLimit = None
            self.res_trig = False
            self.NormalZ_trig = None
            self.HardZ_trig = None
            self.resLimit = None
            self.saturated = False

    @staticmethod
    def findSurface(depth=-180,lld='dry',tip=20,lowSpeed=False,detectMode=1):
        LLD.reset()
        print(('FindSurface Started.. lld: {} | lowSpeed: {} | depth: {}'.format(lld, lowSpeed, depth)))
        # MAIN FINDSURFACE====================        
        c.clear_estop()
        c.clear_motor_fault()
        c.clear_abort_config()
        anchorFlow = c.PLLDConfig.flow[tip]
        if lowSpeed:
            c.PLLDConfig.flow[tip] = LLD.lowSpeed_flow
            stem_vel = 2
            stem_acc = 5
        else:
            stem_vel = c.PLLDConfig.stem_vel
            stem_acc = c.PLLDConfig.stem_acc
        # Algorithms Start Here
        depth -= c.chipCalibrationConfig.colCompressTolerance
        if str.lower(lld) == 'dry':
            Dry.reset()
            Dry.pressLimit = c.setUp_plld(tip=tip, lowSpeed=lowSpeed, detectMode=detectMode)
        elif str.lower(lld) == 'wet':
            Wet.reset()
            Wet.resLimit = c.setUp_wlld()
        init_res = c.sensing.res()
        # ADD-ON FINDSURFACE====================
        print('move', c.get_motor_pos())
        proc = c.PostTrigger.proc #for sensor read catcher
        c.move_abs_z(depth,stem_vel,stem_acc) # max move but will stop when plld triggered"
        while int(round(c.get_motor_pos(),0)) != int(round(depth,0)): 
            if proc != c.PostTrigger.proc: break
        if str.lower(lld) == 'dry':
            if 'RESISTANCE' in c.PostTrigger.trigger:
                Dry.res_trig = True                
            elif 'PRESSURE2' in c.PostTrigger.trigger:
                Dry.press_trig = True
            Dry.HardZ_trig = c.PostTrigger.trigger
            LLD.HardZ_trig = c.PostTrigger.trigger
        elif str.lower(lld) == 'wet':
            if 'RESISTANCE' in c.PostTrigger.trigger:
                Wet.res_trig = True
            Wet.HardZ_trig = c.PostTrigger.trigger
            LLD.HardZ_trig = Wet.HardZ_trig
        printr('Trigger check-> HardZ: {}'.format(LLD.HardZ_trig))
        print('done move',  c.get_motor_pos())
        # MAIN FINDSURFACE====================
        # after the motor stopped, set every process done
        c.abort_flow()
        c.Average_done = True
        c.Tare_done = True
        c.Calibrate_done = True
        c.Count_volume_done = True
        c.Pipetting_done = True
        # clear all abort
        print('press-res trig:',Dry.press_trig, Dry.res_trig)
        pos =  c.get_motor_pos()
        c.clear_motor_fault()
        c.clear_abort_config(c.AbortID.MOTORHARDBRAKE)
        c.clear_abort_config(c.AbortID.VALVECLOSE)
        zero = c.get_motor_pos()
        # ADD-ON FINDSURFACE====================
        print('Checking surfaceFound..')
        print('pressureCheck..\t limit: {}\t | postpress: {}'.format(Dry.pressLimit, c.PostTrigger.press))
        print('resCheck..\t limit: {}\t | postRes: {}'.format(init_res - c.PLLDConfig.resThres, c.PostTrigger.res))
        if str.lower(lld) == 'dry':
            if Dry.press_trig:
                LLD.surfaceFound = True
                Dry.surfaceFound = True
                printy('Surface found at Dry (PLLD)')
            else:
                printy("Pressure Limit isn't reached at Dry (PLLD failed)")
            if Dry.res_trig:
                LLD.surfaceFound = True
                Dry.surfaceFound = True
                printy('Resistance Triggered at Dry (PLLD)')
        elif str.lower(lld) == 'wet':
            if Wet.res_trig:
                LLD.surfaceFound = True
                Wet.surfaceFound = True
                printb('Surface found at Wet (WLLD)')
            else:
                printy("Resistance Limit isn't reached at Wet (WLLD failed)")
        if lowSpeed: c.PLLDConfig.flow[tip] = anchorFlow
        c.PostTrigger.terminateAll()
        return zero

    # LLD TEST / TIP RECIPROCATING
    class Test():
        runStat = True

        @staticmethod
        def stopTest():
            printr('STOPPING LLD TEST... PLEASE WAIT UNTILL THE LAST PROCESS IS DONE!\t\t\t')
            mainLLD.test.runStat = False

        @staticmethod
        def baseline(*args):
            mainLLD.test.runStat = True
            tip, iters, pickpos = None, None, None
            if not args:
                printy('!!! PUT THE WATER BUCKET ON RACK 1-D7 !!!')
                inputs1 = avoidInpErr.reInput('Tip, Iter, Pickpos >> ')
                tip = int(inputs1.split(',')[0])
                iters = int(inputs1.split(',')[1])
                pickpos = inputs1.split(',')[2]
            else:
                tip = args[0]
                iters = args[1]
                pickpos = args[2]

            deck.setZeroDeckMode(tip)
            speedMode('f')
            next_pickpos = pickpos
            pick_target = globals()['pick_targets'][tip]
            evade = globals()['evades'][tip]
            target = globals()['asp_targets'][tip]
            safe = globals()['safes'][tip]
            source = 'D10'
            zeros = 0
            n = 0

            filename = 'Level\LLD_P'+str(tip)+ '_' + time.strftime('%Y%m%d%H%M%S', time.localtime(time.time())) + '.csv'
            back_write(wraps([
                'X'+','+'n'         +','+
                'Date'              +','+
                'Tip'               +','+
                'Zero Surface'      +','+
                'p1_init'           +','+
                'AtmPress(p2_init)' +','+
                'Initial Res'       +','+
                'Veloc'             +','+
                'Accel'             +','+
                'Flow'              +','+
                'Type'              +','+
                'UseDynamic'        +','+
                'Press Threshold'   +','+
                'Press Limit'       +','+
                'Res Threshold'     +','+
                'Res Limit'         +','+
                'Press Trig'        +','+
                'Res Trig'          +','+
                'NormalZ Trigger'   +','+
                'HardZ Trigger'     +','+
                'LLD Freq'          +','+
                'Triggered Res'     +','+
                'dRes(init-trig)'   +','+
                'Depth'             +','+
                'Triggered P1'      +','+
                'Triggered P2'      +','+
                'dP1(init-trig)'    +','+
                'dP2(init-trig)'    +','+
                'Pre Read Freq'     +','+
                'R1'                +','+
                'R2'                +','+
                'R3'                +','+
                'R4'                +','+
                'R5'                +','+
                'R6 at ExpectedSatZ'+','+
                'ExpectedSatZ'      +','+
                'Saturated Res'     +','+
                'Saturated Z'       +','+
                'Saturated Depth'   +','+
                'FindSatZLimit'     +','+
                'Saturated'         +','+
                'Opr Time ms'       +','+
                'FullCycle ms']),filename)
            c.move_abs_z(-10,200,500)

            for x in range(iters):
                if mainLLD.test.runStat: 
                    LLD.reset()
                    t_tot1 = time.time()
                    c.tare_pressure(); atm_press = c.ATM_pressure
                    dates = time.strftime('%Y/%m/%d %H:%M:%S', time.localtime(time.time()))
                    picktipstat = picktip(next_pickpos, tip=tip)
                    pickpos         = next_pickpos
                    next_pickpos    = picktipstat[1]
                    ejectpos        = picktipstat[2]
                    if picktipstat[0]:
                        p1_init = c.sensing.p1()
                        res_init = c.sensing.res()
                        printg('Finding Zero Surface...')
                        print('initRes:',res_init,'| p1_init:',p1_init,'| p2_init:',atm_press)
                        align(1,source,target+15,safe)
                        zeros = mainLLD.findSurface(target,lld='dry',lowSpeed=True,tip=tip)
                        if tip != 1000:
                            if c.sensing.res() < res_init - Dry.resThres:
                                LLD.res_trig = True
                            if LLD.res_trig:
                                printr('Resistance triggered! Pressure Zero Surface Fail, Trying GoZERO...')
                                LLD.surfaceFound = False
                            else:
                                printg('Zero Surface Found! Cleaning up the tip...')
                        Dry.reset()
                        Wet.reset()
                        if LLD.surfaceFound:
                            wawik(1,source,target-10)
                            #################### DRY DRY DRY DRY DRY #####################################

                            # Dry Phase
                            printy('DRY PHASE..')
                            time.sleep(1) #wait the water to stable
                            t1 = time.time()
                            Dry.zero = mainLLD.findSurface(target,lld='dry',tip=tip)
                            Dry.t_operation = time.time()-t1
                            Dry.p1, Dry.p2 = c.sensing.p1(),c.PostTrigger.press
                            Dry.res = c.PostTrigger.res
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
                            Dry.r6_res,_ = mainLLT.preReading(Dry.expectedSatZ[tip])
                            printg('Level 6..',Dry.r6_res,_)

                            #Saturated Res & Z
                            Dry.satZ, Dry.satRes, Dry.satZlimit, Dry.saturated = mainLLT.findSaturation(Dry.zero, tip)
                            printg('SaturatedRes:',Dry.satRes,'at z:',Dry.satZ)

                            ##################### WET WET WET WET WET ########################

                            printb('WET PHASE..')
                            # Wet phase
                            t3 = time.time()
                            align(1,source,target+30, target+30)
                            Wet.zero = mainLLD.findSurface(target,lld='wet',tip=tip)
                            Wet.t_operation = time.time()-t3

                            #Checking wlld triggers
                            Wet.p1, Wet.p2 = c.sensing.p1(), c.PostTrigger.press
                            Wet.res = c.PostTrigger.res
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
                            printg('Level 3..',Wet.r3_res, _)

                            #R4 = -3mm
                            Wet.r4_res,_ = mainLLT.preReading(-c.PrereadingConfig.stepDown)
                            printg('Level 4..',Wet.r4_res,_)

                            #R5 = -4mm
                            Wet.r5_res,_ = mainLLT.preReading(-c.PrereadingConfig.stepDown)
                            printg('Level 5..',Wet.r5_res,_)

                            #R6 = -110
                            Wet.r6_res,_ = mainLLT.preReading(Wet.expectedSatZ[tip])
                            printg('Level 6..',Wet.r6_res,_)

                            #Saturated Res & Z
                            Wet.satZ, Wet.satRes, Wet.satZlimit, Wet.saturated = mainLLT.findSaturation(Wet.zero, tip)
                            printg('SaturatedRes:',Wet.satRes,'at z:',Wet.satZ)

                            c.move_abs_z(target+30,100,300,0)
                            t_tot = time.time() - t_tot1

                            # DRY DATA PUSH
                            n += 1
                            wrapper = '{}'
                            for i in range(44-1): wrapper += ',{}' 
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
                                c.PLLDConfig.flow[tip],
                                Dry.types,
                                Dry.useDynamic,
                                Dry.pressThres[tip],
                                Dry.pressLimit,
                                Dry.resThres,
                                Dry.resLimit,
                                Dry.press_trig,
                                Dry.res_trig,
                                Dry.NormalZ_trig,
                                Dry.HardZ_trig,
                                Dry.lld_freq,
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
                                int(Dry.expectedSatZ[tip]+Dry.zero),
                                Dry.satRes,
                                Dry.satZ,
                                zeros-Dry.satZ,
                                Dry.satZlimit,
                                Dry.saturated,
                                Dry.t_operation,
                                t_tot
                                )]),filename)
                            
                            # WET DATA PUSH
                            n += 1
                            wrapper = '{}'
                            for i in range(44-1): wrapper += ',{}' 
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
                                c.PLLDConfig.flow[tip],
                                Wet.types,
                                Wet.useDynamic,
                                Wet.pressThres[tip],
                                Wet.pressLimit,
                                Wet.resThres,
                                Wet.resLimit,
                                Wet.press_trig,
                                Wet.res_trig,
                                Wet.NormalZ_trig,
                                Wet.HardZ_trig,
                                Wet.lld_freq,
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
                                int(Wet.expectedSatZ[tip]+Wet.zero),
                                Wet.satRes,
                                Wet.satZ,
                                zeros-Wet.satZ,
                                Wet.satZlimit,
                                Wet.saturated,
                                Wet.t_operation,
                                t_tot
                                )]),filename)

                            printg("Time Remaining: {}m {}s".format(int(t_tot/60*(iters-x-1)), int(t_tot*(iters-x-1)) % 60))

                        printg('Eject Phase..')
                        # Eject phase
                        c.move_abs_z(0,100,100)                        
                        eject(tip=tip,ejectpos=pickpos)
                #align(0, next_pickpos, 0)

        @staticmethod #detectMode with different flows
        def flowReferencing(tip=20,flow=10,detectMode=0,single=False,**kargs): # Single PLLD test in the number of iterations
            # detectMode 0: Hardbrake (Res + Pres))
            # detectMode 1: HardBrake Pres
            if single:
                anchorFlow = c.PLLDConfig.flow[tip]
                c.PLLDConfig.flow[tip] = flow
                zref = lld.findSurface(target, lowSpeed=True, tip=tip); time.sleep(0.5)
                c.move_rel_z(5,100,200)
                wawik(1,'D10',target+30)
                zdet = lld.findSurface(target,detectMode=detectMode, tip=tip); time.sleep(0.5)
                depth = zref - zdet
                print('PLLD FLOW', c.PLLDConfig.flow[tip])
                c.PLLDConfig.flow[tip] = anchorFlow
                wawik(1,'D10',target+30)
                return zref, zdet, depth
            else:
                target = globals()['asp_targets'][tip]
                range1 = kargs['range1'] if 'range1' in kargs else 10
                range2 = kargs['range2'] if 'range2' in kargs else 150
                space = kargs['space'] if 'space' in kargs else 10
                iters = kargs['iters'] if 'iters' in kargs else 1
                datas = []
                refs = list(range(range1,range2+space,space))       
                for it in range(iters):                
                    c.clear_motor_fault()
                    c.clear_estop()
                    c.move_abs_z(target+30,100,200)
                    for flow in refs:
                        zref, zdet, depth = lld.test.flowReferencing(tip,flow,detectMode,True)
                        datas.append([flow, zref, zdet, round(depth,2)])
                        printy('ITER NO:',it,'| FLOW:',flow)
                filename = 'Level/{}_{}xFlowReferencingMode{}_{}.csv'.format(tip,iters,detectMode,int(time.time()))
                df = pd.DataFrame(datas,columns=['Flow','Z Ref','Z PLLD','Depth'])
                df.to_csv(filename, index=False)
                printg('DONE!')

        @staticmethod
        def resReferencing(tip=20,resThres=100,single=False,**kargs): # WLLD test in the number of iterations
            if single:
                anchorRes = c.PLLDConfig.resThres
                c.PLLDConfig.resThres = res
                zref = lld.findSurface(target, lowSpeed=True, tip=tip)
                c.move_rel_z(10,100,200)
                wawik(1,'D7',target)
                zdet = lld.findSurface(target,lld='wet', tip=tip)
                depth = zdet - zref
                print('WLLD resThres', c.WLLDConfig.resThres)
                print('res:',res,'| depth:',depth)
                c.PLLDConfig.resThres = anchorRes
                wawik(1,'D7',target)
                return zref,zdet,depth
            else:
                target = globals()['asp_targets'][tip]
                range1 = kargs['range1'] if 'range1' in kargs else 100
                range2 = kargs['range2'] if 'range2' in kargs else 500
                space = kargs['space'] if 'space' in kargs else 100
                iters = kargs['iters'] if 'iters' in kargs else 1
                datas = []
                refs = list(range(range1,range2+space,space)) 
                for it in range(iters):
                    c.clear_motor_fault()
                    c.clear_estop()
                    c.move_abs_z(target+20,100,200)
                    for res in range(range1,range2,space):
                        zref,zdet,depth = mainLLD.test.resReferencing(tip,res,True)
                        datas.append([res, zref, zdet, round(depth,2)])
                        printy('ITER NO:',it,'| Freq:',res)
                    #datas.append([it+1,it+1,it+1,it+1])
                filename = 'Level/{}_{}resReferencing{}.csv'.format(tip,iters,int(time.time()))
                df = pd.DataFrame(datas,columns=['Res','Z Ref','Z WLLD','Depth'])
                df.to_csv(filename, index=False)
                printg('DONE!')

        @staticmethod #base method for referencing different flows by blowing the stem underwater
        def blowReferencing(tip=20, flow=c.PLLDConfig.flow[20], single=False,**kargs):
            if single:
                target = globals()['asp_targets'][tip]
                c.abort_flow()
                c.move_abs_z(target+20,100,200)
                c.start_flow(flow)
                time.sleep(1)
                c.start_logger(openui=True)
                c.move_abs_z(target-5,15,1000)
                time.sleep(2)
                c.stop_logger()
                c.move_abs_z(target+20,15,1000)
                time.sleep(1)
                c.abort_flow()
                wawik(1,'D10',target)
            else:
                mainLLD.test.runStat = True
                range1 = kargs['range1'] if 'range1' in kargs else 10
                range2 = kargs['range2'] if 'range2' in kargs else 160
                space = kargs['space'] if 'space' in kargs else 10
                refs = list(range(range1,range2+space,space))
                for flow in refs:
                    print('Flow : {}'.format(flow))
                    lld.test.blowReferencing(tip, flow, True)

        @staticmethod #base method for WLLD referencing with different freq
        def freqReferencing(tip=20, freq=c.WLLDConfig.freq, single=False, **kargs):
            if single:
                print('Freq: {}'.format(freq))
                target = globals()['targets'][tip]
                mainLLD.test.runStat = True
                source = 'D10'
                align(1,source,target+60)
                zref = lld.findSurface(target,lowSpeed=True, tip=tip)
                anchor = c.WLLDConfig.freq
                c.WLLDConfig.freq = freq
                depth = zdet - zref
                zdet = lld.findSurface(target,lld='wet', tip=tip)
                printr('Depth: {} | Freq: {}'.format(depth, freq))
                c.WLLDConfig.freq = anchor
                return zref, zdet, depth
            else:
                range1 = kargs['range1'] if 'range1' in kargs else 100
                range2 = kargs['range2'] if 'range2' in kargs else 200
                space = kargs['space'] if 'space' in kargs else 100
                iters = kargs['iters'] if 'iters' in kargs else 1
                datas = []
                refs = list(range(range1,range2+space,space))
                for freq in refs:
                    datas.append([freq])
                    for i in range(iters):
                        zref, zdet, depth = lld.test.freqReferencing(tip,freq,True)
                        datas[len(datas)-1].append(depth)
                    sdev = np.std(datas[len(datas)-1][1:])
                    avg = np.average(datas[len(datas)-1][1:])
                    datas[len(datas)-1].append(avg)
                    datas[len(datas)-1].append(sdev/avg)
                cols = ['depth_'+str(i) for i in range(len(refs))]
                cols.insert(0,'Freq'); cols.append('avg'); cols.append('cv')
                df = pd.DataFrame(datas,columns=cols)
                df.to_csv("Level/FreqReferencing_{}.csv".format(int(time.time())),index=False)

        @staticmethod #method to find false positive of PLLD
        def pthresReferencing(tip=20,thresh=c.PLLDConfig.pressThres[20],single=False,**kargs):
            if single:
                speedMode('f')
                c.move_abs_z(-95,100,1000)
                zref = lld.findSurface(-110,lowSpeed=True, tip=tip)
                c.move_abs_z(0,100,1000)
                wawik(1,'D7',0)
                zdet = lld.findSurface(-110,detectMode=1, tip=tip)
                c.move_abs_z(0,100,1000)
                wawik(1,'D7',0)
                speedMode('m')
                depth = zdet - zref
                return zref, zdet, depth
            else:
                range1 = kargs['range1'] if 'range1' in kargs else 1
                range2 = kargs['range2'] if 'range2' in kargs else 2
                space = kargs['space'] if 'space' in kargs else 1
                iters = kargs['iters'] if 'iters' in kargs else 1
                datas = []
                refs = np.arange(range1,range2+space,space)
                for th in refs:
                    datas.append([th])
                    anchorT = c.PLLDConfig.pressThres[tip]
                    c.PLLDConfig.pressThres[tip] = th
                    for i in range(iters):
                        zref, zdet, depth = lld.test.pthresReferencing(th,tip,True)
                        datas[len(datas)-1].append(depth)
                    c.PLLDConfig.pressThres[tip] = anchorT
                    sdev = np.std(datas[len(datas)-1])
                    avg = np.average(datas[len(datas)-1])
                    datas[len(datas)-1].append(avg)
                    datas[len(datas)-1].append(sdev/avg)
                cols = ['depth_'+str(i) for i in range(len(refs))]
                cols.insert(0,'thres'); cols.append('avg'); cols.append('cv')
                df = pd.DataFrame(datas,columns=cols)
                df.to_csv("Level/PLLDThreshReferencing_{}.csv".format(int(time.time())),index=False)

        @staticmethod
        def farDepthing(tip,pickpos,iters,flow,thres,dyn): #for p1000 long travel LLD
            filename = 'Level/P{}_HardDepthing_{}uLs_th{}_dyn{}_{}.csv'.format(tip,flow,thres,dyn,int(time.time()))
            datas = []
            speedMode('f')
            next_pickpos = str.upper(pickpos)
            pick_target = globals()['pick_targets'][tip]
            target = globals()['asp_targets'][tip]
            target = globals()['safes'][tip]
            source = 'D7'
            anchorF = c.PLLDConfig.flow[tip]
            c.PLLDConfig.flow[tip] = flow
            anchorT = c.PLLDConfig.pressThres[tip]
            c.PLLDConfig.pressThres[tip] = thres
            anchorD = c.PLLDConfig.useDynamic
            c.PLLDConfig.useDynamic = dyn
            for i in range(iters):
                picktipstat = picktip(next_pickpos,tip)
                pickpos         = next_pickpos
                next_pickpos    = picktipstat[1]
                ejectpos        = picktipstat[2]
                if picktipstat[0]:
                    align(1,source,target+10)
                    zref = lld.findSurface(target, lowSpeed=True, tip=tip)
                    c.move_abs_z(0,200,300)         
                    wawik(1,source,0)
                    c.move_abs_z(0,200,300)
                    zdet = lld.findSurface(target,detectMode=1, tip=tip)
                    wawik(0,pickpos,pick_target+15)
                    c.move_abs_z(pick_target+15,200,500)
                    datas.append([c.PLLDConfig.flow[tip], c.PLLDConfig.pressThres[tip], c.PLLDConfig.useDynamic, zref, zdet, zref-zdet])
                    #align(0,pickpos,pick_target+15)
                    eject()
            c.move_abs_z(0,200,300)
            printg('DONE')
            c.PLLDConfig.flow[tip] = anchorF
            c.PLLDConfig.pressThres[tip] = anchorT
            c.PLLDConfig.UseDynamic = anchorD
            df = pd.DataFrame(datas,columns=['Flow','Threshold','Dynamic Thresh', 'Z Ref', 'Z Det', 'Depth'])
            df.to_csv(filename,index=False)
            speedMode('s')
    test = Test

lld = mainLLD
LLD = mainLLD.Operation('LLD')
LLD.zero = -90
LLD.res = 3100
LLD.p2 = 936
Dry = mainLLD.Operation('PLLD')
Wet = mainLLD.Operation('WLLD')
Wet.resThres = c.WLLDConfig.resThres
Wet.lld_freq = c.WLLDConfig.freq
Wet.useDynamic = False

class mainLLT():
    class Geo():
        @staticmethod
        def init(operation='asp'):
            mainLLT.lltMode = 'geo'
            mainLLT.Geo.stop()
            if not mainLLT.threshold: mainLLT.findThreshold(operation=operation)
            print('Geometric LLT initialized..')

        @staticmethod
        def start():
            print('Geometric LLT started..')
            c.set_collision_abort(c.DLLTConfig.Geo.colThres)
            c.p.set_liquid_tracking_limit(True, c.chipCalibrationConfig.upperLimit*c.stem_eng, c.chipCalibrationConfig.lowerLimit*c.stem_eng)
            c.p.set_liquid_tracking_volume_linear_params(c.DLLTConfig.Geo.trackFactor, c.DLLTConfig.Geo.startVolThres)            
            c.p.start_liquid_tracker(1)

        @staticmethod
        def stop():
            c.p.stop_liquid_tracker()
            print('Geometric LLT Stopped..')
            #if c.get_triggered_input(c.AbortID.MOTORDECEL) or c.get_triggered_input(c.AbortID.MOTORHARDBRAKE):
            print('Motion Config Cleared..')
            c.clear_abort_config(c.AbortID.ESTOP)
            c.clear_abort_config(c.AbortID.MOTORDECEL)
            c.clear_abort_config(c.AbortID.MOTORHARDBRAKE)
            c.clear_estop()
            c.clear_motor_fault()

    class Res():
        @staticmethod
        def init(tip=20,operation='asp'):
            mainLLT.lltMode = 'res'
            if not mainLLT.threshold: mainLLT.findThreshold(operation=operation)
            mainLLT.Res.stop()
            c.p.set_liquid_tracking_move_profile(
                c.DLLTConfig.Res.stem_vel[tip]*c.stem_eng,
                c.DLLTConfig.Res.stem_acc[tip]*c.stem_eng,
                1.0,
                c.DLLTConfig.Res.inverted)
            print(f'Resistance LLT P{tip} initialized..')

        @staticmethod
        def start(tip=20):
            print(f'Resistance LLT P{tip} Started..')
            c.set_collision_abort(c.DLLTConfig.Res.colThres)
            #c.p.set_liquid_tracking_limit(True, c.chipCalibrationConfig.upperLimit*c.stem_eng, c.chipCalibrationConfig.lowerLimit*c.stem_eng)
            c.p.set_liquid_tracking_resistance_params(
                c.DLLTConfig.Res.kp[tip],
                c.DLLTConfig.Res.ki,
                c.DLLTConfig.Res.kd[tip],
                abs(mainLLT.threshold),
                c.DLLTConfig.Res.stepSize,
                c.DLLTConfig.Res.bigStep,
                c.DLLTConfig.Res.pidPeriod) 
            print(mainLLT.threshold)
            c.p.start_liquid_tracker(0)

        @staticmethod
        def stop():
            print('Resistance LLT Stopped..')
            c.p.stop_liquid_tracker()            
            print('Motion Config Cleared..')
            c.clear_abort_config(c.AbortID.ESTOP)
            c.clear_abort_config(c.AbortID.MOTORHARDBRAKE)
            c.clear_estop()
            c.clear_motor_fault()
    
    # Main Attributes
    r1 = 0
    r2asp = 0
    r2dsp = 0
    r2diff = 0
    threshold = 0
    lltMode = None
    testStat = False
    resNoise = 0

    @staticmethod
    def run(tip=20,operation='asp'):        
        llt.terminate()
        if mainLLT.findThreshold(operation=operation):
            if str.lower(operation) == 'asp':
                if mainLLT.r2asp > mainLLT.r1:
                    printg('**Geometric LLT Mode**')
                    mainLLT.threshold = 0.0
                    mainLLT.Geo.init(operation=operation)
                    mainLLT.Geo.start()
                elif mainLLT.resNoise < abs(mainLLT.r2asp - mainLLT.r1) < c.PrereadingConfig.dlltMinAspThres:
                    printg('**Geometric LLT Mode**')
                    mainLLT.Geo.init(operation=operation)
                    mainLLT.Geo.start()
                else:
                    printg('**Resistance LLT Mode**')
                    mainLLT.Res.init(tip=tip,operation=operation)
                    mainLLT.Res.start(tip=tip)
            elif str.lower(operation) == 'dsp':
                if not mainLLT.r2dsp or not mainLLT.r2asp: mainLLT.r2diff = mainLLT.r2dsp - mainLLT.r2asp
                if mainLLT.r2dsp > mainLLT.r1:
                    printg('**Geometric LLT Mode**')
                    mainLLT.threshold = 0.0 # to avoid different resistance preread mode n operation
                    mainLLT.Geo.init(operation=operation)
                    mainLLT.Geo.start()
                elif c.PrereadingConfig.dlltMinDspThres < abs(mainLLT.r2dsp - mainLLT.r1) and (c.PrereadingConfig.dlltMinThres<mainLLT.r2diff<c.PrereadingConfig.dlltMaxThres):
                    printg('**Resistance LLT Mode**')
                    mainLLT.Res.init(tip=tip,operation=operation)
                    mainLLT.Res.start(tip=tip)
                else:
                    printg('**Geometric LLT Mode**')
                    mainLLT.Geo.init(operation=operation)
                    mainLLT.Geo.start()
            llt.check()
        else:
            printr("LLT FAILED")

    @staticmethod
    def terminate(postMove=False):
        if mainLLT.lltMode or c.p.get_liquid_tracker_run():
            if mainLLT.lltMode == 'geo':
                mainLLT.Geo.stop()
            elif mainLLT.lltMode == 'res':
                mainLLT.Res.stop()
            else:
                c.p.stop_liquid_tracker()
            if postMove: c.move_rel_z(20,100,200)
            LLD.reset()
            mainLLT.lltMode = None
            printg('LLT Terminated')
        else:
            printr('LLT Unterminated')

    @staticmethod
    def check():
        printg('DLLT limit:');c.readConfig(c.p.get_liquid_tracking_limit)
        printg('DLLT Move Profile:'); c.readConfig(c.p.get_liquid_tracking_move_profile)
        printg('DLLT pid:'); c.readConfig(c.p.get_liquid_tracking_resistance_params)
        printg('Tracking Limit:'); c.readConfig(c.p.get_liquid_tracking_limit)
        printg('Tracking Table Pos:'); c.readConfig(c.p.get_liquid_tracking_table_position,0)
        printg('Tracking Run Status:'); print(c.p.get_liquid_tracker_run())

    @staticmethod
    def findSaturation(z,tip):
        print('Find Saturation Parameters...')
        tipLength = {
                    20:30,
                    200:40,
                    1000:80}
        maxZ = z-tipLength[tip]
        if tip == 1000:
            maxZ = -180
        zpack, respack, decreasePack = [0],[0],[0]
        saturated = False
        n = 0
        z -= 1
        c.move_abs_z(z,15,1000)
        while (z >= maxZ and not saturated):
            time.sleep(0.1)
            z -= 0.5
            c.move_abs_z(z,15,1000)
            pos = c.get_motor_pos(); zpack.append(pos)
            res = c.sensing.res(); respack.append(res)
            decRate = res-respack[-2]; decreasePack.append(decRate)
            if n > 5:
                if decreasePack[-1] < decreasePack[-2]:
                    saturated = True
                    break
            n += 1
        print((decreasePack[-1], decreasePack[-2]))
        if saturated: print('Resistance Saturated!')
        else: print('Resistance is not Saturated!')
        return zpack[-1], respack[-1], maxZ, saturated

    @staticmethod
    def preReading(move=0):
        if c.p.get_AD9833_Frequency() != c.PrereadingConfig.freq: 
            c.set_freq(c.PrereadingConfig.freq, c.PrereadingConfig.freq_delay)
        c.move_rel_z(move,c.PrereadingConfig.stem_vel, c.PrereadingConfig.stem_acc)
        time.sleep(c.PrereadingConfig.readDelay)
        res = np.average([c.sensing.res() for i in range(c.DLLTConfig.sampleSize)])
        z = c.get_motor_pos()
        return res, z

    @staticmethod
    def findThreshold(operation='asp'):
        printb('Finding LLT Threshold..')
        c.set_freq(c.PrereadingConfig.freq, c.PrereadingConfig.freq_delay)
        noise = [c.sensing.res() for i in range(c.DLLTConfig.sampleSize)]
        mainLLT.resNoise = max(noise) - min(noise)
        mainLLT.r1,_ = mainLLT.preReading()
        r2,_ = mainLLT.preReading(-c.PrereadingConfig.stepDown)
        print('r2 :',r2,'| r1:', mainLLT.r1)
        mainLLT.threshold = (r2 - mainLLT.r1)*c.PrereadingConfig.thresMultiplier
        if   str.lower(operation) == 'asp': mainLLT.r2asp = r2
        elif str.lower(operation) == 'dsp': mainLLT.r2dsp = r2
        print('r1: {} | r2: {} | Thres: {}'.format(mainLLT.r1, r2, mainLLT.threshold))
        if abs(mainLLT.r1 - r2) <= mainLLT.resNoise:
            return False
        else:
            return True

    @staticmethod
    def similarityCheck():
        try:
            # Response Delay
            df = pd.read_csv(cplotter.fname)
            tPack = df['tick']
            resPack = df['res']
            velPack = df['vel']
            t_res, t_vel = [], []
            for i, t in enumerate(tPack):
                if i >= 3:
                    if resPack[i] - resPack[i-2] >= 100: t_res.append(t)
                    if velPack[i] - velPack[i-2] >= 100: t_vel.append(t)
            if len(t_res) == 0: t_res = [tPack[len(tPack)-1]]
            if len(t_vel) == 0: t_vel = [tPack[len(tPack)-1]]
            response_delay = t_vel[0] - t_res[0]
            # Similarity
            gaps, devs = [], []
            for i in range(len(tPack)): gaps.append(resPack[i] - velPack[i])
            avgGap = np.average(gaps)
            for gap in gaps: devs.append(abs(gap - avgGap))
            avgDev = np.average(devs)
            similarity = round((avgGap-avgDev)/avgGap,4)
            printb('Res-Vel Similarity: {}% | Response Delay: {} ms'.format(similarity*100, response_delay))
            return similarity, response_delay
        except:
            printr('Last plotter log doesnt exist.. execute llt.pipettingTest() first!')

    @staticmethod
    def test_setUp(tip, volume,iters=1):
        printy("LLT Pipetting Test Started..")
        vol = volume
        lld.findSurface(-190,tip=tip)
        mainLLT.run(tip=tip,operation='asp')
        #c.start_flow(100,1)
        for i in range(iters):
            mainLLT.testStat = True
            time.sleep(1)
            aspirate(vol*0.95, tip)
            time.sleep(2)
            #mainLLT.terminate(postMove=True)
            #mainLLT.run(tip=tip, operation='dsp')
            dispense(vol*1.1, tip)
            time.sleep(0.5)
            cplotter.terminate()
        mainLLT.terminate(postMove=True)
        #time.sleep(2)
        #mainLLT.terminate(postMove=True)
        c.move_rel_z(10,100,200)
        mainLLT.testStat = False
        printy("LLT Pipetting Test Finished..")

    @staticmethod
    def pipettingTest(tip, volume,iters=1,live=True,tool=1):
        if live:
            thread1 = threading.Thread(target=mainLLT.test_setUp,args=(tip,volume,iters))
            thread1.start()
            while not mainLLT.testStat: time.sleep(0.1)
            if tool == 0: 
                plotter.liveplot(p1=True,p2=True,res=True,vel=True)
            else: 
                cplotter.liveplot(p1=True,p2=True,res=True,vel=True)
        else:
            return mainLLT.test_setUp(tip, volume, iters, log=True)

llt = mainLLT

# NOTIFICATION & ALERT
class avoidInpErr():
    inputStat = False
    thread1 = None
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
            inputs = input(words)
            if test_function:
                test_function(inputs)
            avoidInpErr.inputStat = False
            return inputs
        except KeyboardInterrupt:
            avoidInpErr.inputStat = False
            raise    
        except:            
            printy("\n====== Input Error! Check your input and try again!")
            if test_function:
                return avoidInpErr.reInput(words,test_function)
            else:
                return avoidInpErr.reInput(words)

parkingStat = [False, False]
def parkingBeep(run=True):
    def looping():
        globals()['parkingStat'][1] = True
        while globals()['parkingStat'][0]:
            time.sleep(0.3)
            winsound.Beep(1700,900)
        for i in globals()['parkingStat']:
            globals()['parkingStat'][i] = False
    if run:
        globals()['parkingStat'][0] = False
        while parkingStat[1]: time.sleep(0.05)
        globals()['parkingStat'][0] = True
        thread1 = threading.Thread(target=looping)
        thread1.start()
    else:
        globals()['parkingStat'][0] = False