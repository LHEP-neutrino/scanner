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
from scanctrl.daqctrl import DAQCtrl
from scanctrl.ppulsectrl import PPULSECtrl
from scanctrl.supplrctrl import SUPPLRCtrl
from scanctrl.ntcreader import NTCReader

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

def _compute_printer_coordinates(scan_params : dict) -> np.ndarray:

    """
    Compute the printer coordinates for the scan based on the scan parameters (LT coordinates)
    and the coordinate transformation defined in the config file.
    
    The transformation to convert LT coordinates to printer coordinates follows these rules:

    - The limits used to assign the LT corrdinate to the drawer positions are defined by
      the max y coordinate of the 'IN' position in the LT coordinates (y_lim):
        1. y < y_lim -> pos_0 aka 'IN'
        2. y > y_lim -> pos_1 aka 'OUT'
    
    - Finally, there is an overlap between the two positions in the LT coordinates so to avoid
      an unecessary drawer movement we check that there is at least a coordinate in the 'IN' 
      region that don't overlap with the 'OUT" one.
       
      This is checked with the boolean 'has_pos_0'.
      If 'has_pos_0' is False, it means that all the coordinates in the 'IN' region are also in
      the 'OUT' region, so we tag all the coordinates as 'OUT' to avoid an unecessary drawer movement.

    Args:
        scan_params (dict): The scan parameters containing the LT coordinates and the coordinate transformation.
    
    Returns:
        printer_coordinates_IN (list): A list of printer coordinates for points tagged as 'IN'.
        printer_coordinates_OUT (list): A list of printer coordinates for points tagged as 'OUT'.
        scan_coordinates (list): An array of the scan coordinates in LT coordinates.


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
    scan_coordinates = np.flip(scan_coordinates, axis=1).tolist() # Flip the coordinates to get (x,y) instead of (y,x) and tranform it into a list

    logger.debug(f"Scan coordinates (LT coords): {scan_coordinates}")


    # Convert to printer coord.

    # Get the max y coordinate in the LT coords to define the limits for the drawer position tagging
    y_lim = scan_params["coord_transform"]["IN"]["LT_coords"][1][1] 
    y_lim_OUT = scan_params["coord_transform"]["OUT"]["LT_coords"][0][1]

    # Initialize the output lists for the printer coordinates of the 'IN' and 'OUT' positions
    printer_coordinates_IN = []
    printer_coordinates_OUT = []

    # Initalize a boolean to check if there is at least a point in the 'IN' position that is not
    #in the 'OUT' position to avoid an unecessary drawer movement
    has_pos_0 = False

    # Get the coordinate transformation parameters from the config file
    lt_coords_in = scan_params["coord_transform"]["IN"]["LT_coords"]
    printer_coords_in = scan_params["coord_transform"]["IN"]["printer_coords"]
    lt_coords_out = scan_params["coord_transform"]["OUT"]["LT_coords"]
    printer_coords_out = scan_params["coord_transform"]["OUT"]["printer_coords"]

    # Compute the scaling parameters for the coordinate transformation
    offset_x = printer_coords_in[0][0] - lt_coords_in[0][0]
    offset_y_in = printer_coords_in[0][1] - lt_coords_in[0][1]
    offset_y_out = printer_coords_out[0][1] - lt_coords_out[0][1]

    logger.debug(f'Scaling parameters: offset_x: {offset_x}, offset_y_in: {offset_y_in}, offset_y_out: {offset_y_out}')

    for x, y in scan_coordinates:
        if y <= y_lim:
            if y < y_lim_OUT:
                has_pos_0 = True

            printer_coordinates_IN.append([int(x + offset_x), int(y + offset_y_in)]) # Drawer position 0

        elif y > y_lim:
            printer_coordinates_OUT.append([int(x + offset_x), int(y + offset_y_out)]) # Drawer position 1

    
    # Check for unnecessary drawer movement
    if has_pos_0 == False:
        logger.debug("No points in position 'IN' found in the dataset, tagging all points as 'OUT'.")
        printer_coordinates_OUT = printer_coordinates_IN + printer_coordinates_OUT
        printer_coordinates_IN = []


    logger.debug(f"Number of points tagged as 'IN': {len(printer_coordinates_IN)}, Number of points tagged as 'OUT': {len(printer_coordinates_OUT)}")
    logger.debug(f"Scan coordinates (printer coords), IN: {printer_coordinates_IN}, OUT: {printer_coordinates_OUT}")  

    return printer_coordinates_IN, printer_coordinates_OUT, scan_coordinates

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


def _scan_pt(printerctrl : PrinterCtrl, pulserctrl : PPULSECtrl, daqctrl : DAQCtrl, ntcreader : NTCReader, x : float, y : float, z : float, data_folder : str) -> dict:
    """
    Perform a single scan at the specified position.

    Args:
        printerctrl (PrinterCtrl): The printer controller instance.
        pulserctrl (PulserCtrl): The pulser controller instance.
        daqctrl (DAQCtrl): The DAQ controller instance.
        ntcreader (NTCReader): The NTC reader instance.
        x (float): X coordinate for the scan.
        y (float): Y coordinate for the scan.
        z (float): Z coordinate for the scan.
        data_folder (str): Path to the folder where scan data will be saved.

    Returns:
        scan_pt_info (dict): A dictionary containing information about the scanned point.
    """
    logger.debug(f"Scanning at X:{x}, Y:{y}, Z:{z}...")
    
    printerctrl.go_to(x, y, z)
    printerctrl.motors_off()

    daqctrl.start_daq()

    pulserctrl.run_pulser()

    daqctrl.stop_daq()
    
    logger.debug("Scan point finished.")

    scan_pt_info = {"x_printer": int(x),
                    "y_printer": int(y),
                    "data_file" : _find_data_file(data_folder),
                    "timestamp": time.strftime("%Y%m%d_%H%M%S"),
                    "temperature": ntcreader.read_temperature()
                    }

    return scan_pt_info


def _full_scan(printerctrl : PrinterCtrl, supplrctrl : SUPPLRCtrl, scan_config : dict, pulser_config : dict) -> dict:
    """
    Perform a full scan.

    Args:
        printerctrl (PrinterCtrl): The printer controller instance.
        supplrctrl (SupplrCtrl): The supplier controller instance.
        scan_config (dict): The scan configuration.
        pulser_config (dict): The pulser configuration.


    Returns:
        scan_summary_json (dict): A dictionary containing a summary of the scan.
    """
    # From the config file define the scan positions
    scan_params = scan_config["scan_params"]
    data_folder = scan_config["data_folder"]

    printer_coordinates_IN, printer_coordinates_OUT, scan_coordinates = _compute_printer_coordinates(scan_params)

    scan_summary_json = {}
    total_scan_points = len(printer_coordinates_IN) + len(printer_coordinates_OUT)

    scan_summary_json = {"N_scan_points": total_scan_points}

    z  = int(scan_params["z_scan_height"])
    
    with NTCReader() as ntcreader:
        with PPULSECtrl(pulser_config = pulser_config) as pulserctrl:
            with DAQCtrl() as daqctrl:

                if len(printer_coordinates_IN) > 0: # Only scan in the 'IN' position if there are points tagged as 'IN'

                    for idx, (x, y) in enumerate(printer_coordinates_IN):
                        _print_progress_bar(iteration=idx, 
                                            total=len(printer_coordinates_IN), 
                                            prefix="Scanning in progress:", 
                                            suffix=f", Currently: X={x:.2f}, Y={y:.2f}, Drawer: IN", 
                                            length=30
                                            )
                        
                        # Perform the scan at the current point
                        scan_pt_info = _scan_pt(printerctrl, pulserctrl, daqctrl, ntcreader, x, y, z, data_folder)

                        # Register scan info
                        scan_summary_json[f"scan_pt_{idx}"] = scan_pt_info
                        scan_summary_json[f"scan_pt_{idx}"]["drawer_position"] = printerctrl.drawer_position
                        scan_summary_json[f"scan_pt_{idx}"]["LT_x"] = int(scan_coordinates[idx][0])
                        scan_summary_json[f"scan_pt_{idx}"]["LT_y"] = int(scan_coordinates[idx][1])

                # Drawer movement

                if len(printer_coordinates_OUT) > 0: # Only ask to move the drawer if there are points to scan in the OUT position

                    supplrctrl.set_default_bias() # Set the bias voltage to the default value before the door is opened
                    logger.info("\n Scan in 'IN' configuration finished. SiPMs biased down. Please change the drawer to the 'OUT' position to continue.")
                    time.sleep(3)
                    while not click.confirm("Is the drawer in the position 'OUT' and the door closed again?"):
                        click.echo("Waiting for the user to change the drawer position...")
                        time.sleep(3)

                    printerctrl.drawer_position = 1 # Set the drawer position to 1 (OUT) after confirming with the user

                    supplrctrl.set_bias_voltage_channels()


                    for idx, (x, y) in enumerate(printer_coordinates_OUT):
                        _print_progress_bar(iteration=idx, 
                                            total=len(printer_coordinates_OUT), 
                                            prefix="Scanning in progress:", 
                                            suffix=f", Currently: X={x:.2f}, Y={y:.2f}, Drawer: OUT", 
                                            length=30
                                            )
                        
                        # Perform the scan at the current point
                        scan_pt_info = _scan_pt(printerctrl, pulserctrl, daqctrl, ntcreader, x, y, z, data_folder)

                        # Register scan info
                        scan_summary_json[f"scan_pt_{idx+len(printer_coordinates_IN)}"] = scan_pt_info
                        scan_summary_json[f"scan_pt_{idx+len(printer_coordinates_IN)}"]["drawer_position"] = printerctrl.drawer_position
                        scan_summary_json[f"scan_pt_{idx+len(printer_coordinates_IN)}"]["LT_x"] = int(scan_coordinates[idx+len(printer_coordinates_IN)][0]) 
                        scan_summary_json[f"scan_pt_{idx+len(printer_coordinates_IN)}"]["LT_y"] = int(scan_coordinates[idx+len(printer_coordinates_IN)][1])

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

        # Check with user that the LT is in the initial position 'IN' to avoid collision between 
        #front panel and printer head during the homing command
        while not click.confirm("\nIs the Drawer in the position 'IN'?"):
            click.echo("Please move the drawer to the 'IN' position to continue.")
            time.sleep(3)
                
        # Initialize printer controller with config
        with PrinterCtrl(config = config["printer"]) as printerctrl:

            printerctrl.drawer_position = 0 # Set the drawer position to 0 (IN) after confirming with the user


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
            scan_comment = click.prompt('\nPlease enter a comment for the scan if needed [Press Enter to continue]', type=str)
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
                supplrctrl.set_bias_voltage_channels()
                logger.info("SiPMs biased.")

                
    
                # Perform the scan
                scan_summary_json = _full_scan(printerctrl = printerctrl, supplrctrl = supplrctrl, scan_config = config["scan"], pulser_config = config["pulser"])

            # Add scan summary info to the json
            scanner_summary_json["scan_summary"] = scan_summary_json

            # Save the scan summary json to the data folder
            summary_path = os.path.join(config["scan"]["data_folder"], f"{scan_name}_summary.json")

            with open(summary_path, 'w') as f:
                json.dump(scanner_summary_json, f)

def printer_calib(config_file):
    """
    Calibration the printer position to respect to the LT one.

    Args:
        config_file:

    """

    logger.info(f"Running printer calibration script with config: {config_file}")
        
    # Load configuration
    config = _load_config(config_file)

    with PrinterCtrl(config = config["printer"]) as printerctrl:
        # Get the z coordinate from the config file
        z = config["printer"].get("initial_position")[2]  
        parsed_coords = []

        while True:
            coords = click.prompt('\nPlease enter a list of 2D coordinates (e.g., [(x1,y1), (x2,y2)]): ', type=str)
            
            if coords.strip() == "":
                click.echo("The list of coordinates cannot be empty. Please try again.")
                continue
                
            try:
                # Safely evaluate the input string into a Python list/tuple structure
                import ast
                parsed_coords = ast.literal_eval(coords)
                
                # Check if the result is a list
                if not isinstance(parsed_coords, list):
                    click.echo("Input must be a list. Please try again")
                    continue
                    
                # Validate each item is a tuple of exactly 2 numeric values
                for i, coord in enumerate(parsed_coords):
                    if not isinstance(coord, (tuple, list)):
                        raise ValueError(f"Coordinates at index {i} is not a tuple or list.")
                    if len(coord) != 2:
                        raise ValueError(f"Coordinates tuple at index {i} has {len(coord)} coordinates, expected 2.")
                    if not all(isinstance(pos, (int, float)) for pos in coord):
                        raise ValueError(f"Coordinates tuple at index {i} contains non-numeric values.")
                        
                # If we reach here, the format is correct
                break
                
            except (SyntaxError, ValueError, NameError) as e:
                click.echo(f"Invalid format: {e}. Please try again using the format [(x1,y1,z1), (x2,y2,z2), ...].")
                continue      

        for x,y in parsed_coords:
            while not click.confirm(f"\nCan it move to the next position ({x}, {y})?"):
                logger.info("Waiting...")
                time.sleep(3)

            printerctrl.go_to(x, y, z)

        
        while click.confirm(f"\nDo you want to add a coordinates?"):
            coord = click.prompt('\nPlease enter a tuple of 2D coordinates (e.g. (x1,y1)): ', type=str)
            
            if coord.strip() == "":
                click.echo("The coordinates cannot be empty. Please try again.")
                continue
                
            try:
                # Safely evaluate the input string into a Python list/tuple structure
                import ast
                parsed_coord = ast.literal_eval(coord)
                
                # Validate each item is a tuple of exactly 2 numeric values
                if not isinstance(parsed_coord, (tuple, list)):
                    click.echo(f"Coordinates are not a tuple or list. Please try again")
                    continue
                if len(parsed_coord) != 2:
                    click.echo(f"{len(parsed_coord)} coordinates were provided, expected 2. PLease try again")
                    continue
                if not all(isinstance(pos, (int, float)) for pos in parsed_coord):
                    click.echo(f"Coordinates contain non-numeric values. Please try again")
                        
                # If we reach here, the format is correct
                
            except (SyntaxError, ValueError, NameError) as e:
                click.echo(f"Invalid format: {e}. Please try again using the format e.g. (x1,y1).")
                continue

            x, y = parsed_coord
            printerctrl.go_to(x, y, z)

    logger.info("Printer calibration  finished")
        




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


def debug_print_text(text: str):
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

    # Compute scan coordinates
    scan_params = config["scan"]["scan_params"]
    _, _, scan_coords = _compute_printer_coordinates(scan_params)

    logger.info(f"Computed {len(scan_coords)} scan coordinates")

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

    with DAQCtrl() as daqctrl:
        daqctrl.run_daq(data_taking_time=data_taking_time)

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
        supplrctrl.set_bias_voltage_channels()

    logger.info("Done!")

def debug_ntcreader(config_file : str):
    """
    Debug function for the NTC reader. It checks the connection to the Arduino and tries to read the temperature.

    Args:
        config_file (str): Path to the scanctrl configuration file.
    """
    logger.info("Running debug-ntcreader")

    config = _load_config(config_file)

    with NTCReader() as ntcreader:
        logger.info("NTC reader initialized successfully.")
        temperature = ntcreader.read_temperature()
        logger.info(f"Read temperature: {temperature} °C")

    logger.info("Done!")
