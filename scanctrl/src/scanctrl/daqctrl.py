import subprocess
import time
from scanctrl.logger import logger  # Import the global loggercan you 

# Configuration
CONFIG = {
    "adc64": {"port": 6000, "start_cmd": "start_adc64", "stop_cmd": "stop_adc64"},
    "evb": {"port": 6002, "start_cmd": "start_evb", "stop_cmd": "stop_evb"},
}

def _send_command(component: str, command: str, port: int):
    """
    Sends a command string to a local UDP port using socat.
    Captures stdout/stderr and logs them at DEBUG level.
    """
    try:
        # Run socat with capture_output=True to get the output
        proc = subprocess.run(
            ["socat", "-", f"UDP4:localhost:{port}"],
            input=command,
            text=True,
            check=True,
            capture_output=True  # Capture stdout and stderr
        )
        
        # Log the output at DEBUG level
        # stdout contains the result of the command (often empty for UDP send)
        if proc.stdout:
            logger.debug(f"[{component} Port {port}] STDOUT: {proc.stdout.strip()}")
        if proc.stderr:
            logger.debug(f"[{component} Port {port}] STDERR: {proc.stderr.strip()}")
            
        logger.info(f"Sent '{command}' to {component} on port {port}")
        
    except subprocess.CalledProcessError as e:
        # Log the error details if the command fails
        logger.error(f"Failed to send command to {component}: {e.stderr}")
        raise

def start_daq():
    logger.debug("Starting DAQ")
    
    # Start ADC64
    _send_command("adc64", CONFIG["adc64"]["start_cmd"], CONFIG["adc64"]["port"])
    # Start EVB
    _send_command("evb", CONFIG["evb"]["start_cmd"], CONFIG["evb"]["port"])

    time.sleep(1)

def stop_daq():
    logger.debug("Stopping DAQ")
    
    # Stop EVB
    _send_command("evb", CONFIG["evb"]["stop_cmd"], CONFIG["evb"]["port"])
    # Stop ADC64
    _send_command("adc64", CONFIG["adc64"]["stop_cmd"], CONFIG["adc64"]["port"])
    
    time.sleep(1)

def run_daq(data_taking_time: int = 10):
    logger.debug("Starting DAQ")
    
    # Start daq
    start_daq()
    
    time.sleep(1)
    
    # Wait for data taking
    wait_duration = max(1, data_taking_time - 1)
    time.sleep(wait_duration)
    logger.debug("DAQ data taking complete.")
    logger.debug("Stopping DAQ")
    
    # Stop daq
    stop_daq()
