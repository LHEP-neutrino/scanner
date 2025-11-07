import serial
import time, datetime
import argparse
import subprocess
import os
import numpy as np
import sys

ArCLight_path = '/home/daq/ArCLight_3DScan/scan_ACL3_series'
logfile_name = 'data_position'
data_path = '/data/3dscan/data_files'
root_path = '/data/3dscan/root_files'
#root_path = '/home//workspace/jan/scan'
def mymain():
    global logfile_name

    

    logfile_name = input("Enter the name of the scan that you want convert: ")

    print("Starting the conversion of data files to root files")
    exec_rootconversion = ("(cd "+root_path+"/"+logfile_name+";"
            +"bash "+ArCLight_path+"/3dscan_rt_convert_in_folder.sh "+ArCLight_path+"/"+logfile_name+".log "+logfile_name+"/)")
    subprocess.call([exec_rootconversion],shell=True)
    time.sleep(1)
    print("Conversion to root files has finished")

    print("Creating the integration root file")
    exec_writeintegral = ("(cd "+ArCLight_path+";"
                          +"root -q 'Printer_stab_conv.C(\""+logfile_name+".log\")')")
    subprocess.call([exec_writeintegral],shell=True)
    time.sleep(1)
    print("Integration has finished")

    print(":: conversion script has finished")


if __name__=='__main__':
    mymain()





        
