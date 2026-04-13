'''
Commands for the scanner module.
'''
import click
import fcntl
import os
import sys
import json

import time



from scanctrl.printerctrl import PrinterCtrl

LOCK_FILE = "/tmp/scanner.lock"

class ScannerLock:
    """
    A context manager for acquiring a file lock to ensure that only one instance of the scanner is running at a time.

        __init__(self, lock_path): Initializes the ScannerLock with the path to the lock file.
        __enter__(self): Acquires an exclusive lock on the lock file. If the lock cannot be acquired because
                         another instance is running, it raises a ClickException.
        __exit__(self, *args): Releases the lock and removes the lock file when the context is exited.

    Usage:
        with ScannerLock(LOCK_FILE):
            # Your code here that requires exclusive access to the scanner  

    """
    def __init__(self, lock_path):
        self.lock_path = lock_path
        self.lock_fd = None

    def __enter__(self):
        self.lock_fd = open(self.lock_path, "w")
        try:
            fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self.lock_fd.close()
            raise click.ClickException("The scanner is already running, check your other terminals.")
        return self

    def __exit__(self, *args):
        fcntl.flock(self.lock_fd, fcntl.LOCK_UN)
        self.lock_fd.close()
        os.unlink(self.lock_path)

#-----------------------
# Helper functions
#-----------------------

def _full_scan(self):
        """
        Perform a full scan.
        """
        output = "Performing the scan"
        output = output.ljust(60-len(output), '.')
        click.echo(output, nl=False)
        time.sleep(3)
        output = ".....Performing the scan"
        output = output.ljust(60-len(output), '.')
        click.echo(f"\r{output}", nl=False)
        time.sleep(3)
        output = "..........Performing the scan"
        output = output.ljust(60-len(output), '.')
        click.echo(f"\r{output}", nl=False)
        time.sleep(3)
        output = "Scann finished."
        # print(len(output))
        output = output.ljust(60-len(output), '.')
        click.echo(f"\r{output}")


def _singlePt_scan(self, x, y, z):
    """
    Perform a single point scan at the specified position.
    """


#-----------------------
# CLI Commands
#-----------------------

def print_text(text):
    """
    Print the provided text to the terminal.

    Args:
        text (str): The text to print.
    """
    with ScannerLock(LOCK_FILE):
        click.echo(text)
        time.sleep(5)
        click.echo("Done!")

def run_scanner(config_file):
    """
    Run the scanner with the specified configuration file.

    Args:
        config_file (str): Path to the configuration file.
    """
    with ScannerLock(LOCK_FILE):
        click.echo(f"Running scanner with config: {config_file}")
        # Load configuration
        with open(config_file, 'r') as file:
            config = json.load(file)
        # print(config) 

        # Check config file
        data_folder = config.get("data_folder")
        if not os.path.exists(data_folder):
            raise click.ClickException("Config file has an invalid 'data_folder' path.")
                
        # Initialize printer controller with config
        with PrinterCtrl(config["printer"]) as printer:
        
            # Check with user that the VGA is set correctly
            while not click.confirm("Is the VGA gain set correctly (12dB)?"):
                click.echo("Please go to http://130.92.128.188/ in your favorite browser and set the VGA gain to 12dB to continue.")
                time.sleep(3)


            # Ask the user for the LT serial number
            while True:
                lt_serial = click.prompt('Please enter the light trap serial number', type=str) 
                if lt_serial.strip() == "":
                    click.echo("Light trap serial number cannot be empty. Please try again.")
                else:
                    break

            # Ask the user if there is a scan comment
            scan_comment = click.prompt('Please enter a comment for the scan if needed [Press Enter to continue]', type=str, default="")

            # Define scan name and summary json
            scan_name = f"{time.strftime('%Y%m%d_%H%M')}_{lt_serial}"

            scan_summary_json = {
                "scan_name": scan_name,
                "lt_serial": lt_serial,
                "scan_comment": scan_comment,

                "config_file": config_file
            }

            # Check with user that the scanner box door is closed
            while not click.confirm("Is the scanner box door closed?"):
                click.echo("Please close the scanner box door to continue.")
                time.sleep(3)

            # Bias the SiPMs
            click.echo(f"The scan {scan_name} will start shortly. Biasing the SiPMs...")
            time.sleep(3)
            click.echo("SiPMs biased.")

            # Perform the scan
            self._full_scan(printer)

#-----------------------
# Debugging functions
#-----------------------

def debug_printerCtrl(config_file):
    """
        Debug command: Print 'hello' to the terminal.
    """

    with ScannerLock(LOCK_FILE):
        click.echo(f"Running scanner with config: {config_file}")
        # Load configuration
        with open(config_file, 'r') as file:
            config = json.load(file)
        # print(config) 

        # Check config file
        data_folder = config.get("data_folder")
        if not os.path.exists(data_folder):
            raise click.ClickException("Config file has an invalid 'data_folder' path.")
                
        # Initialize printer controller with config
        try:
            with PrinterCtrl(config["printer"]) as printer:
                # Move to a test position 
                x, y, z = 200, 100, 20

                click.echo(f"DEBUG: Moving to X:{x}, Y:{y}, Z:{z}")
                printer.go_to(x, y, z)
                printer.go_to(200,200,20)
                click.echo("DEBUG: Move complete.")
        except Exception as e:
            click.echo(f"DEBUG Error: {e}")
