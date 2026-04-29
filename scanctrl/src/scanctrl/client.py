'''
Commands for the scanner module.
'''
import click
import fcntl
import os
import json
import time
from itertools import product

import numpy as np

from scanctrl.printerctrl import PrinterCtrl
from scanctrl.logger import logger, update_log_levels 
from scanctrl.daqctrl import run_daq, start_daq, stop_daq
from scanctrl.ppulsectrl import PPULSECtrl
from scanctrl.supplrctrl import SUPPLRCtrl

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

def _load_config(config_file : str) -> dict:
    """
    Load the configuration from a JSON file.

    Args:
        config_file (str): Path to the scanctrl configuration file.

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

    # 3. Check that the data folder exists, if not create it
    data_folder = os.path.abspath(config["scan"]["data_folder"])  
    if not os.path.exists(data_folder):   
        logger.info(f"Data folder does not exist. Creating it at: {data_folder}")
        os.makedirs(data_folder)

    config["scan"]["data_folder"] = data_folder

    return config

def _compute_scan_coordinates(scan_params : dict) -> np.ndarray:
    """
    Compute the scan coordinates based on the scan parameters.

    Args:
        scan_params (dict): The scan parameters containing start_pos, end_pos, and N_steps.

    Returns:
        scan_coordinates (np.ndarray): An array of scan coordinates ([[X1, Y1], [X2, Y2], ...]).
    """
    # From the config file define the scan positions
    start_pos = np.array(scan_params["start_pos"], dtype=int)
    end_pos = np.array(scan_params["end_pos"], dtype=int)
    N_steps = np.array(scan_params["N_steps"], dtype=int)

    # Get the axis coordinates
    coord_x, x_step = np.linspace(start_pos[0], end_pos[0], N_steps[0], endpoint=False, retstep=True)
    coord_y, y_step = np.linspace(start_pos[1], end_pos[1], N_steps[1], endpoint=False, retstep=True)

    # Shift the coordinates by half a step to scan in the middle of the pixels
    coord_x += int(x_step/2)
    coord_y += int(y_step/2)

    # Get the Cartesian product of the coordinates to get the scan positions
    # Note that we want to iterate first over the x coordinates (fast axis), so we have to flip them after the product
    scan_coordinates = np.array(list(product(coord_y, coord_x))).astype(int)
    scan_coordinates = np.flip(scan_coordinates, axis=1) # Flip the coordinates to get (x,y) instead of (y,x)

    logger.debug(f"Scan coordinates: {scan_coordinates}")
    return scan_coordinates

def _print_progress_bar(iteration : int, total : int, prefix : str = '', suffix : str = '', length : int = 20, fill : str = '='):
    """
    Calls in a loop to create a terminal progress bar.
    
    Args:
        iteration (int): Current iteration count (1-based).
        total (int): Total number of iterations.
        prefix (str): Prefix string.
        suffix (str): Suffix string.
        length (int): Length of the progress bar in characters.
        fill (str): Character used to fill the bar.
    """
    percent = ("{0:.1f}".format(100 * (iteration / float(total))))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    
    # \r moves the cursor back to the start of the line
    # end='' prevents a newline from being printed
    print(f'\r{prefix} [{bar}] ({iteration}/{total}){suffix}', end='')
    
    if iteration == total:
        print() # Print a newline at the end


def _find_data_file(data_folder : str, max_time_diff: int = 300) -> str | None:
    """
    Find the most recent data file in the specified folder. If `cutoff_time` is provided,
    it checks that the most recent file was modified within that time difference (in seconds)
    from the current time. If not, it returns None and logs a warning.

    Args:
        data_folder (str): Path to the folder where scan data is saved.
        max_time_diff (int, optional): Maximum allowed modification time difference in seconds. Defaults to 300.

    Returns:
        latest_file (str | None): The name of the most recent data file, or None if no suitable file is found.
    """
    cutoff_time = time.time()-max_time_diff

    files = [os.path.join(data_folder, f) for f in os.listdir(data_folder) if (os.path.isfile(os.path.join(data_folder, f)) and f.endswith('.data'))]
    if not files:
        logger.warning(f"No data files found in folder: {data_folder}")
        return None
    
    latest_file = max(files, key=lambda f: os.path.getctime(f))
    modif_time = os.path.getctime(latest_file)
    if modif_time < cutoff_time:
        logger.warning(f"Most recent file in folder {data_folder} was modified too long ago.")
        return None
        
    return latest_file


def _scan_pt(printerctrl, pulserctrl, x, y, z, data_folder) -> dict:
    """
    Perform a single scan at the specified position.

    Args:
        printerctrl (PrinterCtrl): The printer controller instance.
        pulserctrl (PulserCtrl): The pulser controller instance.
        x (float): X coordinate for the scan.
        y (float): Y coordinate for the scan.
        z (float): Z coordinate for the scan.
        data_folder (str): Path to the folder where scan data will be saved.

    Returns:
        scan_pt_info (dict): A dictionary containing information about the scanned point.
    """
    logger.debug(f"Scanning at X:{x}, Y:{y}, Z:{z}...")
    
    printerctrl.go_to(x, y, z)
    printerctrl.motor_off()

    start_daq()

    pulserctrl.run_pulser()

    stop_daq()
    
    logger.debug("Scan point finished.")

    scan_pt_info = {"x": int(x),
                    "y": int(y),
                    "data_file" : _find_data_file(data_folder),
                    "timestamp": time.strftime("%Y%m%d_%H%M%S")
                    }

    return scan_pt_info


def _full_scan(printerctrl : PrinterCtrl, pulserctrl : PPULSECtrl, scan_config : dict) -> dict:
    """
    Perform a full scan.

    Args:
        printerctrl (PrinterCtrl): The printer controller instance.
        pulserctrl (PulserCtrl): The pulser controller instance.
        scan_config (dict): The scan configuration.
    """
    # From the config file define the scan positions
    scan_params = scan_config["scan_params"]
    data_folder = scan_config["data_folder"]

    scan_coordinates = _compute_scan_coordinates(scan_params)

    scan_summary_json = {}
    total_scan_points = len(scan_coordinates)

    scan_summary_json = {"N_scan_points": total_scan_points}

    z  = int(scan_params["z_scan_height"])

    for idx, (x, y) in enumerate(scan_coordinates):
        _print_progress_bar(iteration=idx, 
                            total=total_scan_points, 
                            prefix="Scanning in progress:", 
                            suffix=f", Currently: X={x:.2f}, Y={y:.2f}", 
                            length=30
                            )
        
        scan_pt_info = _scan_pt(printerctrl, pulserctrl, x, y, z, data_folder)


        # Register scan info
        scan_summary_json[f"scan_pt_{idx}"] = scan_pt_info

    _print_progress_bar(iteration=total_scan_points, 
                        total=total_scan_points, 
                        prefix="Scan finished!       :",
                        suffix=len(", Currently: X={x:.2f}, Y={y:.2f}")*" ",
                        length=30
                        )

    return scan_summary_json

#-----------------------
# CLI Commands
#-----------------------

def run_scanner(config_file : str):
    """
    Run the scanner with the specified configuration file.

    Args:
        config_file (str): Path to the scanctrl configuration file.
    """
    with ScannerLock(LOCK_FILE):
        logger.info(f"Running scanner with config: {config_file}")
        
        # Load configuration
        config = _load_config(config_file)
                
        # Initialize printer controller with config
        with PrinterCtrl(config = config["printer"]) as printerctrl:
        
            # Check with user that the VGA is set correctly
            
            while not click.confirm("\nIs the VGA gain set correctly (12dB)?"):
                logger.warning("VGA gain is not set correctly. Please set it to 12dB to continue.")
                click.echo("Please go to http://130.92.128.188/ in your favorite browser and set the VGA gain to 12dB to continue.")
                time.sleep(3)


            # Ask the user for the LT serial number
            while True:
                lt_serial = click.prompt('\nPlease enter the light trap serial number', type=str) 
                if lt_serial.strip() == "":
                    click.echo("Light trap serial number cannot be empty. Please try again.")
                else:
                    break

            # Ask the user if there is a scan comment
            scan_comment = click.prompt('\nPlease enter a comment for the scan if needed [Press Enter to continue]', type=str, default="")
            logger.debug(f"Prompted user for scan comment: {scan_comment}")

            # Define scan name and summary json
            scan_name = f"{time.strftime('%Y%m%d_%H%M')}_{lt_serial}"

            scanner_summary_json = {
                "scan_name": scan_name,
                "lt_serial": lt_serial,
                "scan_comment": scan_comment,
                "config_file": config_file
            }

            # Check with user that the scanner box door is closed
            while not click.confirm("\nIs the scanner box door closed?"):
                click.echo("Please close the scanner box door to continue.")
                time.sleep(3)

            # Bias the SiPMs
            with SUPPLRCtrl(supplr_config = config["supplr"]) as supplrctrl:
                logger.info(f"The scan {scan_name} will start shortly. Biasing the SiPMs...")
                time.sleep(3)
                logger.info("SiPMs biased.")

                with PPULSECtrl(pulser_config = config["pulser"]) as pulserctrl:
    
                    # Perform the scan
                    scan_summary_json = _full_scan(printerctrl, pulserctrl, config)

            # Add scan summary info to the json
            scanner_summary_json["scan_summary"] = scan_summary_json

            # Save the scan summary json to the data folder
            summary_path = os.path.join(config["scan"]["data_folder"], f"{scan_name}_summary.json")

            with open(summary_path, 'w') as f:
                json.dump(scanner_summary_json, f)


# def run_point_scan(config_file : str, x : int, y : int, z : int, scan_comment: str = None):
#     """
#     Run a single point scan at the specified position.

#     Args:
#         config_file (str): Path to the configuration file.
#         x (float): X coordinate for the scan.
#         y (float): Y coordinate for the scan.
#         z (float): Z coordinate for the scan.
#     """
#     with ScannerLock(LOCK_FILE):
#         logger.info(f"Running single point scan with config: {config_file} at X:{x}, Y:{y}, Z:{z}")

#         config = _load_config(config_file)

#         scan_name = f"{time.strftime('%Y%m%d_%H%M')}_scan_pt_x{x}_y{y}_z{z}"

#         scanner_summary_json = {
#                 "scan_name": scan_name,
#                 "config_file": config_file,
#             }
        
#         if scan_comment is not None:
#             scanner_summary_json["scan_comment"] = scan_comment
                
#         # Bias the SiPMs
#         with SUPPLRCtrl(config["supplr"]) as supplrctrl:
#             logger.info(f"The scan {scan_name} will start shortly. Biasing the SiPMs...")
#             time.sleep(3)
#             logger.info("SiPMs biased.")

#             with PPULSECtrl(config["pulser"]) as pulserctrl:

#                 # Perform the scan
#                 scan_summary_json = _scan_pt(printerctrl, pulserctrl, x, y, z, config)

#             # Add scan summary info to the json
#             scanner_summary_json["scan_summary"] = scan_summary_json

#     return

#-----------------------
# Debugging functions
#-----------------------

def debug_printerCtrl(config_file : str):
    """
    Debug function for the printer controller. Make a little and cute square to test the printer movements and the connection.

    Args:
        config_file (str): Path to the scanctrl configuration file.
    """

    with ScannerLock(LOCK_FILE):
        logger.info(f"Running debug-printer-controller with config: {config_file}")
        
        # Load configuration
        config = _load_config(config_file)
                
        # Initialize printer controller with config
        try:
            with PrinterCtrl(config = config["printer"]) as printer:
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

def debug_scan_coordinates(config_file : str):
    """
    Debug function to compute and print the scan coordinates based on the configuration file.

    Args:
        config_file (str): Path to the scanctrl configuration file.
    """
    
    logger.info(f"Running debug-scan-coordinates with config: {config_file}")
    
    # Load configuration
    config = _load_config(config_file)

    # scan_summary_json = _full_scan(None, config['scan'])

    # Compute scan coordinates
    scan_params = config["scan"]["scan_params"]
    scan_coordinates = _compute_scan_coordinates(scan_params)

    logger.info(f"Computed {len(scan_coordinates)} scan coordinates")

def debug_pulserctrl(config_file : str):
    """
    Debug function for the pulser controller. It checks the connection to the pulser server and
    tries to set the configuration.

    Args:
        config_file (str): Path to the scanctrl configuration file.
    """
    logger.info(f"Running debug-pulserctrl with config: {config_file}")

    config = _load_config(config_file)

    try:
        with PPULSECtrl(config = config["pulser"]) as pulserctrl:
            logger.info("Pulser controller initialized successfully.")
            pulserctrl.run_pulser()
    except Exception as e:
        logger.error(f"Failed to initialize pulser controller: {e}")

    logger.info("Done!")

def debug_daqctrl(data_taking_time : int = 10):
    """
    Debug function for the DAQ controller. It runs a simple data taking session to check if the DAQ is working correctly.

    Args:
        data_taking_time (int, optional): The duration of the data taking in seconds. Defaults to 10.
    """
    logger.info("Running debug-daqctrl")

    run_daq(data_taking_time=data_taking_time)

    logger.info("Done!")



def debug_supplrctrl(config_file : str):
    """
    Debug function for the SiPM bias voltage control. It checks the connection to the supply server and tries to set the bias voltage.

    Args:
        config_file (str): Path to the scanctrl configuration file.
    """
    logger.info("Running debug-supplrctrl")

    config = _load_config(config_file)

    with SUPPLRCtrl(supplr_config = config["supplr"]) as supplrctrl:
        logger.info("Supply controller initialized successfully.")
        supplrctrl.set_bias_channels()

    logger.info("Done!")
