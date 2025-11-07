import serial
import time, datetime
import argparse
import subprocess
import os
import math
import numpy as np
import sys
import pandas as pd
from scipy.stats import linregress
from run_LED_pulser import pulser
from open_watchdog import afi_watchdog
from set_bias_voltage import bias_voltage_control

# Open serial port to printer
#s = serial.Serial('/dev/tty.usbserial-AG0K0EZI',115200)
usb_port = subprocess.check_output(['ls /dev/ttyUSB1'],shell=True).decode().strip()
s = serial.Serial(usb_port,115200)
print('Opening Serial Port')

#open serial port to Arduino
Arduino_ser = serial.Serial('/dev/ttyUSB0', 9600)  # Adjust the port as needed

# Dateipfad zur CSV-Datei der Referenz Widerstan zu Temperatur
csv_file_path = 'readout_temp/ntcg163jf103ft1_no_text.csv'
df = pd.read_csv(csv_file_path, names=['Temperatur', 'Min', 'Widerstand','Max','B25/T','-dT','dT'], skiprows=0)

# Pulser settings
hostname = '130.92.128.165'
username = 'pi'
password = 'altisidora'
duration = '24' #s
channel = '1' 
#s_scan = '90' #'90' #90:LCM Scans, Compare LCM vs ACL: 90,120,150,180 
s_scan = '255' #255: ACl scans
p_scan = '0' #only put p larger than zero if s is at zero
s_monitor = '90'
p_monitor = '0' #only put p larger than zero if s is at zero
period = '4' #ms


# Bias voltage settings
hostname_bias = '130.92.128.188'
username_bias = 'pi'
password_bias = 'altisidora'
VGA_board = '15'#'20'
bias_voltage = '56'
#bias_voltage_file = '' #needed if you want to start the just a few channels.... file needs to be on the raspbery

# Path to the afi watchdog program
#afi_watchdog_path = "/home/lhep/afi-new/build/adc64-system/afi-adc64-system"

#Scan settings
tilesizex = 300
tilesizey = 344
ngridy = 300/20 # 20 normal (2cm) #5 #cone width is 5 mm
#ngridy = 2
stepsize = tilesizex/ngridy

offsetx = 50 # Corner of the printerhead aligned with corner of the tile
offsety = 16 # Corner of the printerhead aligned with corner of the tile
offsety_2nd = 220  # Corner of the printerhead aligned with corner of the tile for the 2nd time for the full size
offsetz = 17

fullSize = True


ArCLight_path = '/home/lhep/ArCLight_3DScan/scan_ACLFSD_1'
logfile_name = 'data_position'
#check it
data_path = '/home/lhep/ArCLight_3DScan/data/data'
data_path_in_the_end = '/data/3dscan/data_files'
#check it
root_path = '/home/lhep/ArCLight_3DScan/data'
root_path_in_the_end = '/data/3dscan/root_files'
#check it
#ADCboard = '/0cd8d631_'
#ADCboard = '/0cd913fa_'
ADCboard = '/0cd9414a_'

data_taking_time = 4 # 15 #wait time for one data run

end_run = 0

#gibt die Temperatur gemessen im Monitor mit dem NTC an
def calculate_temperature(df):
    try:
        #first time is a zero sent that's why you need two reads.
        data_Arduino = Arduino_ser.readline().decode('utf-8').rstrip() 

        data_Arduino = Arduino_ser.readline().decode('utf-8').rstrip()
        #print(f'Resistance: {data_Arduino} Ohms')

        # Widerstand vom Arduino Nano einlesen (Beispielwert)
        aktueller_widerstand = float(data_Arduino)/1000  # Aktuellen Widerstand hier eintragen

        # Die beiden Punkte mit dem nächstgelegenen Widerstand zum aktuellen Widerstand auswählen
        naechster_niedrigerer_widerstand = df[df['Widerstand'] <= aktueller_widerstand].max()['Widerstand']
        naechster_hoeherer_widerstand = df[df['Widerstand'] >= aktueller_widerstand].min()['Widerstand']

        # Filtern der Daten für die beiden Punkte
        subset_df = df[(df['Widerstand'] == naechster_niedrigerer_widerstand) | (df['Widerstand'] == naechster_hoeherer_widerstand)]

        # Linearer Fit nur für die beiden Punkte durchführen
        slope, intercept, _, _, _ = linregress(subset_df['Widerstand'], subset_df['Temperatur'])

        # Temperatur für den aktuellen Widerstand berechnen
        aktuelle_temperatur = slope * aktueller_widerstand + intercept
        #aktuelle_temperatur = 0
        print(f'Aktuelle Temperatur: {aktuelle_temperatur} C')
    
    except:
        aktuelle_temperatur = -1

    return aktuelle_temperatur 

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

    #max range of motion for the LED head
    if(x < 35 or x > 360):
        print("Not able to move there!")
        return
    elif(y < 16 or y > 360):
        print("Not able to move there!")
        return
    elif(z<15):
        print("Not able to move there!")
        return


    mystring = 'G0 '+'X'+str(x)+' '+'Y'+str(y)+' '+'Z'+str(z)+'\n'
    s.write(mystring.encode()) # Send g-code block
    grbl_out = s.readline() # Wait for response with carriage return
    grbl_out = grbl_out.decode()
    print(' : ' + grbl_out.strip())#print the feedback


def startdaq(data_taking_time):
    command_start1 = 'echo -n "start_adc64" | socat - UDP4:localhost:6000'
    command_start2 = 'echo -n "start_evb" | socat - UDP4:localhost:6002'
    command_stop1 = 'echo -n "stop_evb" | socat - UDP4:localhost:6002'
    command_stop2 = 'echo -n "stop_adc64" | socat - UDP4:localhost:6000'
    print("start DAQ")
    #subprocess.call(["echo 1 > /home/lhep/.adc_watchdog_file"],shell=True)
    subprocess.run(command_start1, shell=True, check=True)
    subprocess.run(command_start2, shell=True, check=True)
    time.sleep(1)
    #print(subprocess.check_output("cat /home/lhep/.adc_watchdog_file",shell=True).decode().strip())
    time.sleep(data_taking_time-1)
    print("stop DAQ")
    #subprocess.call(["echo 0 > /home/lhep/.adc_watchdog_file"],shell=True)
    subprocess.run(command_stop1, shell=True, check=True)
    subprocess.run(command_stop2, shell=True, check=True)
    time.sleep(1)
    #print(subprocess.check_output("cat ~/.adc_watchdog_file",shell=True).decode().strip())
    out = subprocess.check_output("ls "+data_path+"/*.data -rt | tail -n 1 | tail -c 25",shell=True).decode().strip()
    time.sleep(1)

    return out

def writefile(x,offsetx,y,offsety,z,temp,filename):
    f = open(logfile_name+".log","a")
    f.write(str(x-offsetx)+' '+str(y-offsety)+' '+str(z)+' '+str(temp)+' '+filename+'\n')
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
    goto(300,300,offsetz)
    mycodesender("stopmotor.g")
    time.sleep(20)
    print("Arrived at pre-initialization coordinates")


def one_measurement(x,offsetx,y,offsety,z,hostname, username, password, duration, stepcounter, nsteps, steptime, y_shift):
    global end_run
    
    print("Step X:"+str(x-offsetx)+' Y:'+str(y-offsety)+' Z:'+str(z)+' Step:'+str(stepcounter)+'/'+str(nsteps),end=" ")
    if stepcounter==1:
        start_time = time.time()
    else:
        print("Time remaining: "+time.strftime("%H:%M:%S",time.gmtime(steptime*(nsteps-stepcounter))))
        
    goto(x,y,z)
                    
    #turn pulser on
    t_start = time.time()
    pulser.run_pulser(hostname, username, password, duration)
                    
    print("Turning off motor for data taking")
    mycodesender("stopmotor.g")
    time.sleep(4)
                    
    filename = startdaq(data_taking_time)
    temp=calculate_temperature(df)
    writefile(x,offsetx,y+y_shift,offsety,z,temp,filename)
                    
    #end of the pulsing
    t_end = time.time()
    t_dif = int(duration) - (t_end-t_start)
    print("time for a run: " + str(t_end-t_start))
    if(t_dif <0):
        end_run = end_run + 1
    if(end_run>1):
        print("Pulser runs too short 2x!! End of the scan initialized!! Timedifference was: " +str(t_dif)+"\n")
        sys.exit()
    else:
        print("The time difference between pulser and measurement is: " + str(t_dif) + "\n")
        time.sleep(t_dif+1)

    if stepcounter==1:
        end_time = time.time()
        steptime = end_time-start_time
        print("steptime: " +str(steptime))
    
    return steptime


def scanTile():
    global end_run

    #set the settings for the pulser
    pulser.period_of_puls(hostname, username, password, period)

    input("Press Enter to start data taking")

    #calibration for the monitoring SiPM
    pulser.setting_of_pulser(hostname, username, password, channel, s_monitor, p_monitor)
    t_start = time.time()
    pulser.run_pulser(hostname, username, password, duration)

    #take the data
    print("Turning off motor for data taking")
    mycodesender("stopmotor.g")
    time.sleep(4)
    filename = startdaq(data_taking_time)
    temp=calculate_temperature(df)
    x_mon = -1
    y_mon = -1
    z_mon = -1
    writefile(x_mon,0,y_mon,0,z_mon,temp,filename)

    t_end = time.time()
    t_dif = int(duration) - (t_end-t_start)
    if(t_dif <0):
        end_run = end_run + 1
    if(end_run>1):
        print("Pulser runs too short!! End of the scan initialized!! Time was: " +str(t_dif)+"\n")
        sys.exit()
    else:
        print("Duration difference (needs to be positive but small): " +str(t_dif))
        time.sleep(t_dif+1)

    #set the pulser to the scanning settings
    pulser.setting_of_pulser(hostname, username, password, channel, s_scan, p_scan)


    if(fullSize):
            xmax = offsetx + tilesizex
            ymax = offsety + tilesizey
            xmin = offsetx
            x = offsetx+stepsize/2.
            y = offsety+stepsize/2.
            z = offsetz
            time.sleep(1)
            y_shift = 0

            #start scan
            goto(x,y,z)
            time.sleep(10)
            stepcounter=0
            nsteps = int(round(tilesizex/stepsize) * round(tilesizey/stepsize))
            steptime = data_taking_time
            while x <= xmax and y <= ymax:
                while x < xmax:
                    stepcounter+=1 
                    steptime = one_measurement(x,offsetx,y,offsety,z,hostname, username, password, duration, stepcounter, nsteps, steptime, y_shift)
                    x += stepsize
                                    
                x -= stepsize
                y += stepsize

                if( y <= ymax):
                    while x > xmin:
                        stepcounter+=1 
                        steptime = one_measurement(x,offsetx,y,offsety,z,hostname, username, password, duration, stepcounter, nsteps, steptime, y_shift)

                        x -= stepsize
                    x += stepsize
                    y += stepsize
            
            bias_voltage_control.set_all_bias_voltage_off(hostname_bias,username_bias,password_bias,VGA_board)

            input("The bias voltage is off, move the ACL, close the box and press Enter to continue")

            #bias_voltage_control.restart_supplr(hostname, username, password)
            bias_voltage_control.set_all_bias_voltage_on(hostname_bias,username_bias,password_bias,bias_voltage,VGA_board)
            #bias_voltage_control.set_all_bias_voltage_from_file_on(hostname_bias, username_bias, password_bias, VGA_board, bias_voltage_file)
            print("Bias voltage set to "+bias_voltage+"\n")
            

            x = offsetx+stepsize/2.
            print(f"y is: {y}")
            y_end = y
            y = offsety_2nd+(y_end-ymax)
            print(f"y_end: {y_end}")
            dif_y_yend = y_end-ymax
            print(f"y-end-y_max is: {dif_y_yend}")
            print(f"y now: {y}")
            z = offsetz
            print(f"This (ymax-y)/stepsize) gives: {(ymax-y)/stepsize}")
            n_steps2 = int(round((ymax-y)/stepsize)*round(tilesizex/stepsize))
            time.sleep(1)
            stepcounter=0
            y_shift = tilesizey

            while x <= xmax and y <= ymax:
                while x < xmax:
                    stepcounter+=1 
                    steptime = one_measurement(x,offsetx,y,offsety_2nd,z,hostname, username, password, duration, stepcounter, n_steps2, steptime, y_shift)

                    x += stepsize

                x -= stepsize
                y += stepsize

                if( y <= ymax):
                    while x > xmin:
                        stepcounter+=1
                        steptime = one_measurement(x,offsetx,y,offsety_2nd,z,hostname, username, password, duration, stepcounter, n_steps2, steptime, y_shift)

                        x -= stepsize
                    x += stepsize
                    y += stepsize


    else:
            xmax = offsetx + tilesizex
            ymax = offsety + tilesizey
            xmin = offsetx
            x = offsetx+stepsize/2.
            y = offsety+stepsize/2.
            z = offsetz
            time.sleep(1)
            y_shift =  0

            #start scan
            goto(x,y,z)
            time.sleep(10)
            stepcounter=0
            nsteps = int(round(tilesizex/stepsize) * round(tilesizey/stepsize))
            steptime = data_taking_time
            while  x <= xmax and y <= ymax:
                while x < xmax:
                    stepcounter+=1 
                    steptime = one_measurement(x,offsetx,y,offsety,z,hostname, username, password, duration, stepcounter, nsteps, steptime, y_shift)

                    x += stepsize

                x -= stepsize
                y += stepsize

                if( y <= ymax):
                    while x > xmin:       
                        stepcounter+=1
                        steptime = one_measurement(x,offsetx,y,offsety,z,hostname, username, password, duration, stepcounter, nsteps, steptime, y_shift)

                        x -= stepsize
                    x += stepsize
                    y += stepsize

    #gotoPreInit()
    print("Scan finished in "+time.strftime("%H:%M:%S",time.gmtime(time.time()-t_start)))


def gainCalibration(data_taking_time):
    xArr = [offsetx + stepsize/2., monitorx, offsetx + tilesizex - stepsize/2.]
    y = offsety + tilesizey - stepsize/4.
    z = offsetz
    time.sleep(1)
    input("Press Enter to start data taking")

    #do the points in xArr
    for x in xArr:
        goto(x, y, z)
        time.sleep(10)
        mycodesender("stopmotor.g")
        time.sleep(2)
        filename = startdaq(data_taking_time)
        writefile(x,0, y,0, z, filename)

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
    
    #x = offsetx + tilesizex/2
    #y = offsety + tilesizey/3
    #z = offsetz
    #time.sleep(1)
    input("Press Enter to start the LED stability test")

    #Go to the point where the stability test takes place
    #goto(x,y,z)
    #time.sleep(15)
    #mycodesender("stopmotor.g")
    #time.sleep(2)

    
    for step in range(1,steps+1):
        print("Starting step ",step," of ",steps,".")
        filename = startdaq(data_taking_time)
        #writefile(step+offsetx, y, z, filename)
        temp=calculate_temperature(df)
        writefile(step,0,0,0,0,temp, filename)
        print("Completed step ",step," of ",steps,".")
        time.sleep(interval-data_taking_time-2)

    #gotoPreInit()
    print("The LED stability test has finished.")

def LEDPulserScan(s_min, s_max):
    global end_run
    if data_taking_time<1:
        print("The data taking time must be larger.")
        return
    #set the settings for the pulser
    pulser.period_of_puls(hostname, username, password, period)

    input("Press Enter to start the LED Pulser scan test")
    for s in range(s_min,s_max+1):
        print("Starting s value ",s," of ",s_max,".")
        p = 0
        pulser.setting_of_pulser(hostname, username, password, channel, s, p)

        t_start = time.time()
        pulser.run_pulser(hostname, username, password, duration)

        filename = startdaq(data_taking_time)
        #writefile(step+offsetx, y, z, filename)
        temp=calculate_temperature(df)
        writefile(s,0,0,0,0,temp,filename)

        t_end = time.time()
        t_dif = int(duration) - (t_end-t_start)
        if(t_dif <0):
            end_run = end_run + 1
        if(end_run>1):
            print("Pulser runs too short!! End of the scan initialized!! Time was: " +str(t_dif)+"\n")
            sys.exit()
        else:
            print("Duration difference (needs to be positive but small): " +str(t_dif))
            time.sleep(t_dif+1)

        time.sleep(1)

def mymain():
    global logfile_name
    global end_run

    initializePrinter()

    #open the afi watchdog
    #afi_process = afi_watchdog.open_watchdog_afi(afi_watchdog_path)
    print("Check the location where to save the data to!\n")

    input("Set now the VGA Gain on 12 here (browser): http://130.92.128.188/ \n CLOSE THE BOX NOW BIAS WILL BE TURNED ON! (Press enter afterwards)")

    bias_voltage_control.restart_supplr(hostname, username, password)
    bias_voltage_control.set_all_bias_voltage_on(hostname_bias,username_bias,password_bias,bias_voltage,VGA_board)
    #bias_voltage_control.set_all_bias_voltage_from_file_on(hostname_bias, username_bias, password_bias, VGA_board, bias_voltage_file)
    print("Bias voltage set to "+bias_voltage+"\n")

    logfile_name = input("Enter the name of the scan: ")
    print("Creating data and root directories")
    subprocess.call(["mkdir "+data_path_in_the_end+"/"+logfile_name],shell=True)
    print("Created "+logfile_name+" at "+data_path_in_the_end)
    time.sleep(0.2)
    subprocess.call(["mkdir "+root_path_in_the_end+"/"+logfile_name],shell=True)
    print("Created "+logfile_name+" at "+root_path_in_the_end)
    time.sleep(0.2)
    copy_gateFile = "cp /home/lhep/soft/AFIViewer_new_hardware_FSDI/adc64-tlv/AFIViewer/build/configs/charge.gt "+root_path_in_the_end+"/"+logfile_name+"/charge.gt"
    #copy_gateFile = "cp /home/lhep/.config/AFIViewer/charge.gt "+root_path_in_the_end+"/"+logfile_name+"/charge.gt"
    subprocess.call([copy_gateFile],shell=True)
    copy_settingFile = "cp /home/lhep/soft/AFIViewer_new_hardware_FSDI/adc64-tlv/AFIViewer/build/configs/settings.cfg "+root_path_in_the_end+"/"+logfile_name+"/settings.cfg"
    #copy_settingFile = "cp /home/lhep/.config/AFIViewer/settings.cfg "+root_path_in_the_end+"/"+logfile_name+"/settings.cfg"
    subprocess.call([copy_settingFile],shell=True)
    print("Copied the gate and settings file for the AFIViewer workaround")


    scanTile()
    #LEDstabilityTest(10, 15, 200)
    #LEDPulserScan(51,255)

    # print("Before the file conversion can begin, please terminate any instances of watchdog.")

    print("Moving the data files to directory "+logfile_name+" at "+data_path_in_the_end)
    exec_mv = "(cd "+data_path_in_the_end+"; mv "+data_path+"/*.data "+logfile_name+")"
    subprocess.call([exec_mv],shell=True)
    time.sleep(1)
    print("Data files have been moved")

    print(":: printersheet script has finished, convert the files now")

    #afi_watchdog.stop_program(afi_process)
    bias_voltage_control.set_all_bias_voltage_off(hostname_bias,username_bias,password_bias,VGA_board)


if __name__=='__main__':
    mymain()





        
