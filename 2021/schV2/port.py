from path import*

def Device(address):
    PIPETTE_ADDRESS = address
    flavor="1"
    if flavor=='1':
        import serial.tools.list_ports   # import serial module
        comPorts = list(serial.tools.list_ports.comports())    # get list of all devices connected through serial port
        if len(comPorts)==0:
            exit("No COM port found!, abort...")
            return False
        else:
            serial_port = str(comPorts[comNum])[0:5]
            drv=SlcanFlmxDriver(PIPETTE_ADDRESS,serial_port)
            print('connected to',serial_port)
            return FmlxDevice(drv, PIPETTE_ADDRESS, path_ch)
    elif flavor=='2':
        drv=KvaserFmlxDriver(PIPETTE_ADDRESS)
        return False
    else:
        exit("Invalid flavor")
        return False