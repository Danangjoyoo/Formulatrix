import sys
import clr
import time
from path import*
from numpy import allclose,arange,array
import itertools
from port import Device


path_deck = r"../DeviceOpfuncs/FloDeck.yaml"
device_addr = 1

d = Device(device_addr)
d.connect()

#Abort ID's
MOTOR_0         = 0
MOTOR_1         = 1
ESTOP_OUT       = 2
TOUCH_OFF_OUT   = 3

#Abort Inputs
MOTOR_0_FAULT   = 0
MOTOR_1_FAULT   = 1
ESTOP_IN        = 2
TOUCH_OFF_IN    = 3
DOOR_OPENED     = 4
TRASH_BIN       = 5
DOOR_CLOSED     = 6

eng_value = 4.54545454
syringe_eng_val = 25
syringe_factor = 41.718
syringe_vel = 1 / syringe_factor * syringe_eng_val
travel_velocity = 24 * eng_value
travel_acceleration = 1000 * eng_value
travel_jerk = 20*eng_value

homing_flag = 0
homing_flag_edge = 1
homing_direction = 0
home_velocity = 20 * eng_value
home_slow_velocity = 5 * eng_value
home_acceleration = 500 * eng_value
home_jerk = 150 * eng_value
#Motors Event

home_done = [False,False]
move_done = [False,False]

def handle_on_input_changed(input_id, is_on):
    #print "Input changed on:" + str(input_id) + ", is On =" + str(is_on)
    pass
def handle_move_done(motor_id,status,position):
    global move_done
    print("Move Done:id=" + str(motor_id) + ", Status=" + str(status) + ", position=" + str(position))
    move_done[motor_id] = True
def handle_motor_error_occured(motor_id,motor_error_code):
    print("Motor Error ", motor_id, motor_error_code)
def handle_home_done(motor_id,home_pos,pos):
    global home_done
    print("Home Done on Motor:" + str(motor_id) + ", Home Pos=" + str(home_pos) + ", pos=" + str(pos))
    home_done[motor_id] = True

d.motor_home_done += handle_home_done
d.motor_move_done += handle_move_done
d.on_input_changed += handle_on_input_changed

def home_motor(id,wait=1):
    global home_done
    d.home_motor(id, homing_flag, homing_flag_edge, homing_direction, home_slow_velocity, home_velocity, home_acceleration,home_jerk)
    home_done[id] = False
    while wait and not home_done[id]:
        pass

def home_all_motor():
    home_motor(0,wait=0)
    home_motor(1,wait=0)
    while not(home_done[0] and home_done[1]):
        pass
def current_pos():
    currentpos =[d.get_motor_pos(0)['curr_pos']/eng_value,d.get_motor_pos(1)['curr_pos']/eng_value]
    currentpos = [round(currentpos[0],3), round(currentpos[1],3)]    
    return currentpos

def move_motor_abs(id,pos,wait=True,estop=False):
    global move_done,travel_velocity, travel_acceleration,travel_jerk
    currentpos = d.get_motor_pos(id)['curr_pos']/eng_value
    if estop:
        set_abort_estop()
    if not allclose(currentpos,pos,2e-3) :
        d.move_motor_abs(id,pos*eng_value,travel_velocity,travel_acceleration,travel_jerk)
        move_done[id] = False
        if wait: wait_moves([id])
    else:
        print("Already in pos")
        move_done[id] = True

def wait_moves(ids):
    if len(ids)==1:
        ids.append(ids[0])
    while not(move_done[ids[0]]and move_done[ids[1]]):
        pass

def encoder_live(id):
    while(1):
        print(d.get_encoder_position(id))
        time.sleep(0.1)

zero_deck = [[261,122],[160,122],[59,122]]
row0 = arange(zero_deck[0][0],zero_deck[0][0]-72,-8.9)
col0 = arange(zero_deck[0][1],zero_deck[0][1]-108,-9)
row1 = arange(zero_deck[1][0],zero_deck[1][0]-72,-9)
col1 = arange(zero_deck[1][1],zero_deck[1][1]-108,-9)
row2 = arange(zero_deck[2][0],zero_deck[2][0]-72,-9)
col2 = arange(zero_deck[2][1],zero_deck[2][1]-108,-9)

Points0 = array(list(itertools.product(row0, col0)))
Points1 = array(list(itertools.product(row1, col1)))
Points2 = array(list(itertools.product(row2, col2)))


colname = ["A","B","C","D","E","F","G","H"]
rowname = ['1','2','3','4','5','6','7','8','9','10','11','12']
a=list (itertools.product( colname,rowname))
wellname = [''.join(s) for s  in a  ]

Rack_coord_0 = dict(list(zip(wellname, Points0.tolist())))
Rack_coord_1 = dict(list(zip(wellname, Points1.tolist())))
Rack_coord_2 = dict(list(zip(wellname, Points2.tolist())))

racks = [Rack_coord_0,Rack_coord_1,Rack_coord_2]
def move_to_zero(rack = 0):
    pos0 = zero_deck[rack][0]
    pos1 = zero_deck[rack][1]
    move_motor_abs(0, pos0,False)
    move_motor_abs(1, pos1,False)
    wait_moves([0,1])

def align_deck(rack,well,wait=1):
    coord = racks[rack][well]
    move_motor_abs(0,coord[0],0)
    move_motor_abs(1,coord[1],0)
    if wait: wait_moves([0,1])

def clear_motor():
    d.set_abort_config(0,0,0,0)
    d.set_abort_config(1,0,0,0)
    d.clear_motor_fault(0)
    d.clear_motor_fault(1)

def set_abort_estop():
    clear_motor()
    d.set_abort_config(0,0,1<<2,0)
    d.set_abort_config(1,0,1<<2,0)
    

def lifetime_syringe(x):
    count = 0
    cint = 0
    home_motor(0)
    for i in range(0,x):
        print("speed 50uL/s")
        move_syringe(2000,50)
        time.sleep(1)
        move_syringe(0,50)
        time.sleep(1)
        print("speed 500uL/s")
        move_syringe(2000,500)
        time.sleep(1)
        move_syringe(0,500)
        time.sleep(1)
        print("speed 1000uL/s")
        move_syringe(2000,1000)
        time.sleep(1)
        move_syringe(0,1000)
        time.sleep(1)
        print("speed 1500uL/s")
        move_syringe(2000,1500)
        time.sleep(1)
        move_syringe(0,1500)
        time.sleep(1)
        count = count + 1
        cint = cint + 1
        print("Counter", count)
        if cint == 20:
            print("Leren sik Gan..")
            time.sleep(5)
            cint = 0

def move_syringe(vol,vel,wait=True,estop=False):
    global move_done
    currentpos = d.get_motor_pos(0)['curr_pos']/eng_value
    if estop:
        set_abort_estop()
    if not allclose(currentpos,vol,2e-3) :
        d.move_motor_abs(0,vol/syringe_factor*syringe_eng_val,vel*syringe_vel,travel_acceleration,travel_jerk)
        move_done[0] = False
        if wait: wait_moves([0])
    else:
        print("Already in pos")
        move_done[0] = True


################### IMPROVEMENTS ################################ IMPROVEMENTS ################################################## IMPROVEMENTS #################################################
# IMPROVEMENTS ######################### IMPROVEMENTS ################################ IMPROVEMENTS ################################################## IMPROVEMENTS ############################
################### IMPROVEMENTS ################################ IMPROVEMENTS ################################################## IMPROVEMENTS #################################################
# IMPROVEMENTS ######################### IMPROVEMENTS ################################ IMPROVEMENTS ################################################## IMPROVEMENTS ############################
################### IMPROVEMENTS ################################ IMPROVEMENTS ################################################## IMPROVEMENTS #################################################

# Speed SETTER
def setTravelMode(mode):
    global travel_velocity, travel_acceleration, travel_jerk, eng_value
    if mode == 'slow' or mode == 's':
        travel_velocity = 30 * eng_value #gravimetric
        travel_acceleration = 500 * eng_value #gravimetric
        travel_jerk = 20*eng_value #gravimetric
    elif mode == 'medium' or mode == 'm':
        travel_velocity = 60 * eng_value #platereader
        travel_acceleration = 750 * eng_value #platereader
        travel_jerk = 50*eng_value #platereader
    elif mode == 'fast' or mode == 'f':
        travel_velocity = 100 * eng_value #platereader
        travel_acceleration = 1000 * eng_value #platereader
        travel_jerk = 90*eng_value #platereader

#zero mode SETTER
def setZeroDeckMode(tip):
    global zero_deck, row0,row1,row2,col0,col1,col2,Rack_coord_0, Rack_coord_1,Rack_coord_2,racks
    if tip == 20:
        zero_deck = [[260.5,122],[160,122],[59,122]] # UNTUK CADDY P20 NONCOATING
        #zero_deck = [[261,122],[160,122],[59,122]] # UNTUK CADDY P20 COATING
        #zero_deck = [[260,122.5],[160,122],[59,122]] # UNTUK CADDY P20 COATING
    elif tip == 200:
        zero_deck = [[260.5,122],[160,122],[59,122]] # UNTUK CADDY P200 NONCOATING
        #zero_deck = [[261.5,122],[160,122],[59,122]] # UNTUK CADDY P200 COATING
    elif tip == 1000:
        zero_deck = [[260.5,122],[160,122],[59,122]] # UNTUK CADDY P1000 NONCOATING
    row0 = arange(zero_deck[0][0],zero_deck[0][0]-72,-9)
    col0 = arange(zero_deck[0][1],zero_deck[0][1]-108,-9)
    row1 = arange(zero_deck[1][0],zero_deck[1][0]-72,-9)
    col1 = arange(zero_deck[1][1],zero_deck[1][1]-108,-9)
    row2 = arange(zero_deck[2][0],zero_deck[2][0]-72,-9)
    col2 = arange(zero_deck[2][1],zero_deck[2][1]-108,-9)

    Points0 = array(list(itertools.product(row0, col0)))
    Points1 = array(list(itertools.product(row1, col1)))
    Points2 = array(list(itertools.product(row2, col2)))


    colname = ["A","B","C","D","E","F","G","H"]
    rowname = ['1','2','3','4','5','6','7','8','9','10','11','12']
    a=list (itertools.product( colname,rowname))
    wellname = [''.join(s) for s  in a  ]

    Rack_coord_0 = dict(list(zip(wellname, Points0.tolist())))
    Rack_coord_1 = dict(list(zip(wellname, Points1.tolist())))
    Rack_coord_2 = dict(list(zip(wellname, Points2.tolist())))

    racks = [Rack_coord_0,Rack_coord_1,Rack_coord_2]