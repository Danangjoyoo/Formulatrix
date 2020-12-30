class LLD():
	zero = -90
	p1 = 942
	p2 = 936
	res = 3100

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

def lld_goZero(manual=False,flow=3,dllt=True,tip=200):
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
		lld_goZero(manual=False)
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
		printg('\n Zero Surface Found! Auto Tuning GoZERO Finished')
		LLD.set_value(z,p1,p2+1,r)
		print 'LLD Set >>', LLD.get_value(True)
		c.abort_flow()
		c.clear_motor_fault()
	c.set_estop_abort(500)