'''
Commands for the scanner module.
'''
import click
import fcntl
import os
import json

import time


from scanctrl.printerctrl import PrinterCtrl
from logger import logger, update_log_levels  # Import the global logger and log level update function

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
        except BlockingIOError as e:
            self.lock_fd.close()
            logger.error(f"The scanner is already running, check your other terminals: {e}")
            raise e
        return self

    def __exit__(self, *args):
        fcntl.flock(self.lock_fd, fcntl.LOCK_UN)
        self.lock_fd.close()
        os.unlink(self.lock_path)

#-----------------------
# Helper functions
#-----------------------

def _load_config(config_file):
    """
    Load the configuration from a JSON file.

    Args:
        config_file (str): Path to the configuration file.

    Returns:
        dict: The loaded configuration.
    """
    # 1. Load configuration
    try:
        with open(config_file, 'r') as file:
            config = json.load(file)

    except FileNotFoundError as e:
        logger.error(f"Config file not found: {e}")
        raise e
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in config file: {e}")
        raise e

    
    # 2. Check for log level in config
    logging = config.get("logging") if config.get("logging") else None

    if logging:
        update_log_levels(logging)
    else:
        logger.info("No logging configuration found in config file. Using default INFO level.")  


    return config

def _full_scan(printerctrl):
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

#-----------------------
# CLI Commands
#-----------------------

def run_scanner(config_file):
    """
    Run the scanner with the specified configuration file.

    Args:
        config_file (str): Path to the configuration file.
    """
    with ScannerLock(LOCK_FILE):
        logger.info(f"Running scanner with config: {config_file}")
        
        # Load configuration
        config = _load_config(config_file)
                
        # Initialize printer controller with config
        with PrinterCtrl(config["printer"]) as printer:
        
            # Check with user that the VGA is set correctly
            while not click.confirm("Is the VGA gain set correctly (12dB)?"):
                logger.warning("VGA gain is not set correctly. Please set it to 12dB to continue.")
                click.echo("Please go to http://130.92.128.188/ in your favorite browser and set the VGA gain to 12dB to continue.")
                time.sleep(3)


            # Ask the user for the LT serial number
            while True:
                lt_serial = click.prompt('Please enter the light trap serial number', type=str) 
                if lt_serial.strip() == "":
                    logger.warning("Light trap serial number cannot be empty. Please try again.")
                    click.echo("Light trap serial number cannot be empty. Please try again.")
                else:
                    break

            # Ask the user if there is a scan comment
            scan_comment = click.prompt('Please enter a comment for the scan if needed [Press Enter to continue]', type=str, default="")
            logger.debug(f"Prompted user for scan comment: {scan_comment}")

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
                logger.warning("Scanner box door is not closed. Please close it to continue.")
                click.echo("Please close the scanner box door to continue.")
                time.sleep(3)

            # Bias the SiPMs
            logger.info(f"The scan {scan_name} will start shortly. Biasing the SiPMs...")
            time.sleep(3)
            logger.info("SiPMs biased.")

            # Perform the scan
            _full_scan(printer)

    return

def run_point_scan(config_file, x, y, z):
    """
    Run a single point scan at the specified position.

    Args:
        config_file (str): Path to the configuration file.
        x (float): X coordinate for the scan.
        y (float): Y coordinate for the scan.
        z (float): Z coordinate for the scan.
    """
    with ScannerLock(LOCK_FILE):
        logger.info(f"Running single point scan with config: {config_file} at X:{x}, Y:{y}, Z:{z}")

        config = _load_config(config_file)
                
        # Initialize printer controller with config
        with PrinterCtrl(config["printer"]) as printer:
            logger.info(f"Moving to X:{x}, Y:{y}, Z:{z}...")
            printer.go_to(x, y, z)
            printer.motor_off()
            logger.info("Start single point scan.")
            time.sleep(3)
            logger.info("Single point scan finished.")
            return

#-----------------------
# Debugging functions
#-----------------------

def debug_printerCtrl(config_file):
    """
        Debug function for the printer controller. Make a little and cute square to test the printer movements and the connection.
    """

    with ScannerLock(LOCK_FILE):
        logger.info(f"Running debug-printer-controller with config: {config_file}")
        
        # Load configuration
        config = _load_config(config_file)
                
        # Initialize printer controller with config
        try:
            with PrinterCtrl(config["printer"]) as printer:
                # Move to test positions
                x, y, z = 200, 200, 20
                logger.info(f"Moving to X:{x}, Y:{y}, Z:{z}")
                printer.go_to(x, y, z)

                x, y, z = 200, 100, 20
                logger.info(f"Moving to X:{x}, Y:{y}, Z:{z}")
                printer.go_to(x, y, z)

                x, y, z = 100, 100, 20
                logger.info(f"Moving to X:{x}, Y:{y}, Z:{z}")
                printer.go_to(x, y, z)

                x, y, z = 100, 200, 20
                logger.info(f"Moving to X:{x}, Y:{y}, Z:{z}")
                printer.go_to(x, y, z)

                x, y, z = 200, 200, 20
                logger.info(f"Moving to X:{x}, Y:{y}, Z:{z}")
                printer.go_to(x, y, z)

                logger.info("DEBUG: Moves complete.")

        except Exception as e:
            logger.error(f"DEBUG Error: {e}")

def debug_print_text(text):
    """
    Print the provided text to the terminal.

    Args:
        text (str): The text to print.
    """
    with ScannerLock(LOCK_FILE):
        logger.info("Running debug-print-text")
        click.echo(text)
        time.sleep(5)
        logger.info("Done!")