import serial
import time, datetime
import argparse
import subprocess
import os
import numpy as np
import sys

# Open serial port
#s = serial.Serial('/dev/tty.usbserial-AG0K0EZI',115200)
usb_port = subprocess.check_output(['ls /dev/ttyUSB*'],shell=True).decode().strip()
s = serial.Serial(usb_port,115200)
print('Opening Serial Port')

newreadout = True #Set if new or  old readout used
tilesizex = 300
tilesizey = 280
ngridy = 14
stepsize = tilesizey/ngridy

offsetx = 7.5 # Corner of the printerhead aligned with corner of the tile
offsety = 49.5 # Corner of the printerhead aligned with corner of the tile
offsetz = 185
monitorx = offsetx + 165 - 32
monitory = offsety + 305

ArCLight_path = '/home/daq/ArCLight_3DScan/scan_ACL3_series'
logfile_name = 'data_position'
data_path = '/data/3dscan/data_files'
root_path = '/data/3dscan/root_files'
ADCboard = '/0cd8d631_'
data_taking_time = 15 #wait time for one data run


def removeComment(string):
    if (string.find(';')==-1):
        return string
    else:
        return string[:string.index(';')]


def mycodesender(mygcode):#Chose wich gcode file you want to send, first initialization (init.g), then sequence (only works when connected to printer)
    #mygcode = str(input('Enter the gcode file to be used (XYZ.g): \n'))
    # Open g-code file
    f = open(mygcode,'r');
    print('Opening gcode file')
 
    # Wake up 
    s.write(str.encode("\r\n\r\n")) # Hit enter a few times to wake the Printrbot
    time.sleep(2)   # Wait for Printrbot to initialize
    s.flushInput()  # Flush startup text in serial input
    print('Sending gcode')
    time.sleep(2)
 
    # Stream g-code
    for line in f:
    	l = removeComment(line)
    	l = l.strip() # Strip all EOL characters for streaming
    	if  (l.isspace()==False and len(l)>0) :
    		print('Sending: ' + l)
    		l = (l + '\n')
    		time.sleep(1)
    		s.write(l.encode()) # Send g-code block
    		time.sleep(1)
    		while s.in_waiting >0:
    			grbl_out = s.readline() # Wait for response with carriage return
    			grbl_out = grbl_out.decode()
    			print(' : ' + grbl_out.strip())

    #Close file
    f.close()
    time.sleep(3)
    while s.in_waiting >0:
    	grbl_out = s.readline() # Wait for response with carriage return
    	grbl_out = grbl_out.decode()
    	print(' : ' + grbl_out.strip())


def goto(x,y,z):
    mystring = 'G0 '+'X'+str(x)+' '+'Y'+str(y)+' '+'Z'+str(z)+'\n'
    s.write(mystring.encode()) # Send g-code block
    grbl_out = s.readline() # Wait for response with carriage return
    grbl_out = grbl_out.decode()
    print(' : ' + grbl_out.strip())#print the feedback


def startdaq(data_taking_time):
    if newreadout:
        print("start DAQ")
        subprocess.call(["echo 1 > ~/.adc_watchdog_file"],shell=True)
        time.sleep(1)
        print(subprocess.check_output("cat ~/.adc_watchdog_file",shell=True).decode().strip())
        time.sleep(data_taking_time-1)
        print("stop DAQ")
        subprocess.call(["echo 0 > ~/.adc_watchdog_file"],shell=True)
        time.sleep(1)
        print(subprocess.check_output("cat ~/.adc_watchdog_file",shell=True).decode().strip())
        out = subprocess.check_output("ls "+data_path+ADCboard+"*.data -rt | tail -n 1 | tail -c 30",shell=True).decode().strip()
        time.sleep(1)

    else:
        print("old readout process \n")
        f = open("/data/3dscan/mylog.log","w")
        subprocess.call(["/home/lhep/afi-adc64-without-watchdog/build/adc64-system/afi-adc64-system","--cli_mode","--data_dir","/data/3dscan","--event_number","15000"],stderr=f)
        out = subprocess.check_output("grep -a \"MStreamFileWriter opened file: /data/3dscan/\" /data/3dscan/mylog.log | tail -c 30",shell=True)[:-1].decode()
        while(not subprocess.call("grep \"AdcSelfTest failed\" /data/3dscan/mylog.log",shell=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)):
            os.remove("/data/3dscan/"+str(out))
            f.close()
            f = open("/data/3dscan/mylog.log","w")
            subprocess.call(["/home/lhep/afi-adc64-without-watchdog/build/adc64-system/afi-adc64-system","--cli_mode","--data_dir","/data/3dscan","--event_number","15000"],stderr=f)
            out = subprocess.check_output("grep -a \"MStreamFileWriter opened file: /data/3dscan/\" /data/3dscan/mylog.log | tail -c 30",shell=True)[:-1].decode()
    return out


def writefile(x,y,z,filename):
    f = open(logfile_name+".log","a")
    f.write(str(x-offsetx)+' '+str(y-offsety)+' '+str(z)+' '+filename+'\n')
    f.close()


def initializePrinter():
    input("Press Enter to start printer initialization")
    mycodesender('init.g')
    print("Wait 60s")
    time.sleep(60)

    while s.in_waiting >0:
    	grbl_out = s.readline() # Wait for response with carriage return
    	grbl_out = grbl_out.decode()
    	print(' : ' + grbl_out.strip())

    print("Moving to scan height")
    goto(180,180,offsetz)
    time.sleep(15)
    mycodesender("stopmotor.g")

    print("Initialisation over\n Ready\n")


def gotoPreInit():
    print("Returning to pre-initialization coordinates")
    goto(300,300,200)
    mycodesender("stopmotor.g")
    time.sleep(20)
    print("Arrived at pre-initialization coordinates")


def scanTile():
    xmax = offsetx + tilesizex
    ymax = offsety + tilesizey
    xmin = offsetx
    x = offsetx+stepsize/2.
    y = offsety+stepsize/2.
    z = offsetz
    time.sleep(1)
    input("Press Enter to start data taking")

    #make monitor run
    i_mon = -1
    print("Step Monitor, start of scan")
    goto(monitorx,monitory,offsetz)
    time.sleep(20)
    print("Turning off motor for data taking")
    mycodesender("stopmotor.g")
    time.sleep(4)
    filename = startdaq(data_taking_time)
    writefile(monitorx,monitory,i_mon,filename)
    i_mon=i_mon-1

    time.sleep(25)

    #make monitor run
    print("Step Monitor")
    goto(monitorx,monitory,offsetz)
    time.sleep(20)
    print("Turning off motor for data taking")
    mycodesender("stopmotor.g")
    time.sleep(4)
    filename = startdaq(data_taking_time)
    writefile(monitorx,monitory,i_mon,filename)
    i_mon=i_mon-1
   
    #start scan
    goto(x,y,z)
    time.sleep(15)
    stepcounter=0
    nsteps = (int(tilesizex/stepsize)) * (int(tilesizey/stepsize))
    steptime = 30
    while x < xmax and y < ymax:
        while x < xmax:
            stepcounter+=1
            print("Step X:"+str(x-offsetx)+' Y:'+str(y-offsety)+' Z:'+str(z)+' Step:'+str(stepcounter)+'/'+str(nsteps),end=" ")
            if stepcounter==1:
            	start_time = time.time()
            else:
            	print("Time remaining: "+time.strftime("%H:%M:%S",time.gmtime(steptime*(nsteps-stepcounter))))
            goto(x,y,z)
            print("Turning off motor for data taking")
            mycodesender("stopmotor.g")
            time.sleep(4)
            filename = startdaq(data_taking_time)
            writefile(x,y,z,filename)
            x += stepsize
            if stepcounter==1:
            	end_time = time.time()
            	steptime = end_time-start_time
        x -= stepsize
        y += stepsize

        #make monitor run
        print("Step Monitor")
        goto(monitorx,monitory,offsetz)
        time.sleep(20)
        print("Turning off motor for data taking")
        mycodesender("stopmotor.g")
        time.sleep(4)
        filename = startdaq(data_taking_time)
        writefile(monitorx,monitory,i_mon,filename)
        i_mon=i_mon-1

        while x > xmin:
            stepcounter+=1 
            print("Step X:"+str(x-offsetx)+' Y:'+str(y-offsety)+' Z:'+str(z)+' Step:'+str(stepcounter)+'/'+str(nsteps),end=" ")
            print("Time remaining: "+time.strftime("%H:%M:%S",time.gmtime(steptime*(nsteps-stepcounter))))         
            goto(x,y,z)
            print("Turning off motor for data taking")
            mycodesender("stopmotor.g")
            time.sleep(4)
            filename = startdaq(data_taking_time)
            writefile(x,y,z,filename)
            x -= stepsize
        x += stepsize
        y += stepsize
    
    #monitor run
    print("Step Monitor, end of scan")
    goto(180,180,offsetz)
    time.sleep(20)
    goto(monitorx,monitory,offsetz)
    time.sleep(20)
    print("Turning off motor for data taking")
    mycodesender("stopmotor.g")
    time.sleep(4)
    filename = startdaq(data_taking_time)
    writefile(monitorx,monitory,i_mon,filename)

    gotoPreInit()
    print("Scan finished in "+time.strftime("%H:%M:%S",time.gmtime(time.time()-start_time)))


def gainCalibration(data_taking_time):
    xArr = [offsetx + stepsize/2., monitorx, offsetx + tilesizex - stepsize/2.]
    y = offsety + tilesizey - stepsize/4.
    z = offsetz
    time.sleep(1)
    input("Press Enter to start data taking")
    
    #make monitor run
    goto(180,180,z)
    time.sleep(20)
    goto(monitorx,monitory,offsetz)
    time.sleep(20)
    mycodesender("stopmotor.g")
    time.sleep(2)
    filename = startdaq(data_taking_time)
    writefile(monitorx,monitory,-99,filename)

    #do the points in xArr
    for x in xArr:
        goto(x, y, z)
        time.sleep(15)
        mycodesender("stopmotor.g")
        time.sleep(2)
        filename = startdaq(data_taking_time)
        writefile(x, y, z, filename)

    gotoPreInit()
    print("Gain calibration data taking finished.")


def HVCalibration(y):
    y = offsety+y
    z = offsetz
    channels = ['ch'+str(ch_id) for ch_id in range(10,16)]
    xArr = [30,70,130,170,230,270]

    for sipm in range(len(xArr)):
        x = offsetx + xArr[sipm]
        channel = channels[sipm]
        goto(x,y,z)
        time.sleep(15)
        mycodesender("stopmotor.g")
        print("Current position X:"+str(x-offsetx)+" Y:"+str(y-offsety)+" Z:"+str(z))
        print("Corresponding to channel "+channel)
        input("Press enter if you are ready to continue to the next channel")

    gotoPreInit()
    print("HV calibration has finished")


def LEDstabilityTest(data_taking_time, interval, steps):
    if data_taking_time>interval+2:
        print("The interval must be greater than the data taking time + 2s.")
        return

    # initializePrinter()
    
    x = offsetx + tilesizex/2
    y = offsety + tilesizey/3
    z = offsetz
    time.sleep(1)
    input("Press Enter to start the LED stability test")

    #Go to the point where the stability test takes place
    goto(x,y,z)
    time.sleep(15)
    mycodesender("stopmotor.g")
    time.sleep(2)

    for step in range(1,steps+1):
        print("Starting step ",step," of ",steps,".")
        filename = startdaq(data_taking_time)
        writefile(step+offsetx, y, z, filename)
        print("Completed step ",step," of ",steps,".")
        time.sleep(interval-data_taking_time-2)

    gotoPreInit()
    print("The LED stability test has finished.")


def mymain():
    global logfile_name

    initializePrinter()

    logfile_name = input("Enter the name of the scan: ")
    print("Creating data and root directories")
    subprocess.call(["mkdir "+data_path+"/"+logfile_name],shell=True)
    print("Created "+logfile_name+" at "+data_path)
    time.sleep(0.2)
    subprocess.call(["mkdir "+root_path+"/"+logfile_name],shell=True)
    print("Created "+logfile_name+" at "+root_path)
    time.sleep(0.2)
    copy_gateFile = "cp /home/daq/.config/AFIViewer/charge.gt "+root_path+"/"+logfile_name+"/charge.gt"
    subprocess.call([copy_gateFile],shell=True)
    copy_settingFile = "cp /home/daq/.config/AFIViewer/settings.cfg "+root_path+"/"+logfile_name+"/settings.cfg"
    subprocess.call([copy_settingFile],shell=True)
    print("Copied the gate and settings file for the AFIViewer workaround")

    scanTile()
    # LEDstabilityTest(15, 120, 200)

    # print("Before the file conversion can begin, please terminate any instances of watchdog.")

    print("Moving the data files to directory "+logfile_name+" at "+data_path)
    exec_mv = "(cd "+data_path+"; mv *.data "+logfile_name+")"
    subprocess.call([exec_mv],shell=True)
    time.sleep(1)
    print("Data files have been moved")

    print(":: printersheet script has finished, convert the files now")


if __name__=='__main__':
    mymain()





        
