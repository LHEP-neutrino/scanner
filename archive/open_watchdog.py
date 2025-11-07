import subprocess
import os
class afi_watchdog:
    def open_watchdog_afi(afi_watchdog_path):
        # Open the program in a new process
        #process = subprocess.Popen(afi_watchdog_path)
        process = subprocess.Popen(afi_watchdog_path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Continue with the rest of the code
        print("Afi Watchdog opened successfully!")
        return process
    
    def stop_program(process):
        # Stop the program
        
        process.terminate()
        print("Afi Watchdog stopped successfully!")
        

# Path to the afi watchdog program
#afi_watchdog_path = "/home/lhep/afi-new/build/adc64-system/afi-adc64-system"

# Call the function to open the program and continue
#open_watchdog_afi(afi_watchdog_path)