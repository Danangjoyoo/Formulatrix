class DLLTConfig():
	class res:
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
	
	class geo:
		upperlimit = 9.0
		lowerLimit = -148.0
		trackFactor = 6.36
		stem_vel = 150
		stem_acc = 2000
		inverted = False
		startVolThres = 0
		colThres = 40
		trackProfile = 'ProfileLookUpTable'