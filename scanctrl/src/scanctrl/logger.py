import logging
import os

# Get the script name 
script_name = 'scanctrl'  

# Create a global logger instance
logger = logging.getLogger(script_name)
logger.setLevel(logging.INFO)

# Create a logbook and a file handler
# Get the directory where THIS file (logger.py) is located
current_file_path = os.path.abspath(__file__)
module_dir = os.path.dirname(current_file_path)
src_dir = os.path.dirname(module_dir)
project_dir = os.path.dirname(src_dir)

# Define the log folder inside the module directory
log_dir = os.path.join("../", project_dir, "log")
log_file_name = "scanctrl.log"
log_file_path = os.path.join(log_dir, log_file_name)

# Ensure the directory exists
os.makedirs(log_dir, exist_ok=True)
file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
file_handler.setLevel(logging.INFO)

# Create a formatter
formatter = logging.Formatter('%(asctime)s - %(module)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
file_handler.setFormatter(formatter)

# Add the handler to the logger
# Check if handler is already added to avoid duplicates if this file is imported multiple times
if not logger.handlers:
    logger.addHandler(file_handler)

# Add console handler to log on screen too
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

def update_log_levels(levels):
    """
    Update the log level of the logger and its handlers.

    Args:
        levels (dict): The new log levels (e.g., 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL') for the logbook ('log_level') and console output ('console_verbose').
    """
    if not levels:
        logger.info("No logging levels provided to update. Keeping existing levels.")
        return

    log_level = getattr(logging, levels.get("log_level").upper(), None)
    if not isinstance(log_level, int):
            logger.warning(f'Invalid log level. Should be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL. Defaulting to INFO.')
            log_level = getattr(logging, 'INFO') # Default to INFO if invalid

    console_verbose = getattr(logging, levels.get("console_verbose").upper(), None)
    if not isinstance(console_verbose, int):
            logger.warning(f'Invalid console verbose. Should be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL. Defaulting to INFO.')
            console_verbose = getattr(logging, 'INFO') # Default to INFO if invalid
    
    # Logger level is the minimum of the logbook and console levels to ensure all messages are captured by the lower level handler
    # Note: DEBUG=10 is lower than INFO=20, min == more verbose level
    logger_level = min(log_level, console_verbose)
    logger.setLevel(logger_level)
    logger.debug(f"Log level (logger) updated to: {logging.getLevelName(logger_level)}")

    if log_level:
        file_handler.setLevel(log_level)
        logger.debug(f"Log level (logbook) updated to: {logging.getLevelName(log_level)}")
   
    if console_verbose:
        console_handler.setLevel(console_verbose)
        logger.debug(f"Console verbose updated to: {logging.getLevelName(console_verbose)}")
    