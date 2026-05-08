import subprocess
import time
from scanctrl.logger import logger  # Import the global loggercan you 
import fcntl
import os

# Configuration
CONFIG = {
    "adc64": {"port": 6000, "start_cmd": "start_adc64", "stop_cmd": "stop_adc64"},
    "evb": {"port": 6002, "start_cmd": "start_evb", "stop_cmd": "stop_evb"},
}

LOCK_FILE = "/tmp/daq.lock"

        
class DAQCtrl:
    """
    A class to manage sending of commands to the Data Acquisition (DAQ) system. Note that only one instance
    of DAQCtrl should be active at a time to avoid conflicts, which is enforced by the DAQLock context manager.
    Provides methods to start, stop, and run the DAQ for a specified duration. Additionally it handles
    exceptions and crashed; the daq is stopped in case of unexpected errors.

    Usage:
        while DAQCtrl() as daq_ctrl:
            daq_ctrl.start_daq()
            daq_ctrl.stop_daq()
    """

    def __init__(self):
        self.lock_path = LOCK_FILE
        self.lock_fd = None

        self._is_running = False

    def __enter__(self):
        self.lock_fd = open(self.lock_path, "w")
        try:
            fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as e:
            self.lock_fd.close()
            logger.error(f"A DAQCtrl instance is already running, check your other terminals: {e}")
            raise e
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Check that the DAQ is not still running, if it is, attempt to stop it
        if self._is_running:
            logger.warning("DAQ was still running during exit. Attempting to stop it.")
            try:
                self.stop_daq()
            except Exception as e:
                logger.error(f"Failed to stop DAQ during exit: {e}")
        else:
            logger.debug("DAQ ctrl exited cleanly with DAQ not running.")

        # Release the lock and clean up
        fcntl.flock(self.lock_fd, fcntl.LOCK_UN)
        self.lock_fd.close()
        os.unlink(self.lock_path)

    def _send_command(self, component: str, command: str, port: int):
        """
        Sends a command string to a local UDP port using socat.
        Captures stdout/stderr and logs them at DEBUG level.

        Args:
            component (str): The name of the component (e.g., "adc64", "evb") for logging purposes.
            command (str): The command string to send.
            port (int): The local UDP port to send the command to.
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
                
            logger.debug(f"Sent '{command}' to {component} on port {port}")
            
        except subprocess.CalledProcessError as e:
            # Log the error details if the command fails
            logger.error(f"Failed to send command to {component}: {e.stderr}")
            raise

    def start_daq(self):
        """
        Starts the DAQ by sending the appropriate commands to the ADC64 and EVB components.
        """
        logger.debug("Starting DAQ")
        
        # Start ADC64
        self._send_command("adc64", CONFIG["adc64"]["start_cmd"], CONFIG["adc64"]["port"])
        # Start EVB
        self._send_command("evb", CONFIG["evb"]["start_cmd"], CONFIG["evb"]["port"])

        self._is_running = True

        time.sleep(1)

    def stop_daq(self):
        """
        Stops the DAQ by sending the appropriate commands to the ADC64 and EVB components.
        """
        logger.debug("Stopping DAQ")
        
        # Stop EVB
        self._send_command("evb", CONFIG["evb"]["stop_cmd"], CONFIG["evb"]["port"])
        # Stop ADC64
        self._send_command("adc64", CONFIG["adc64"]["stop_cmd"], CONFIG["adc64"]["port"])
        
        self._is_running = False
        time.sleep(1)

    def run_daq(self, data_taking_time: int = 10):
        """
        Runs the DAQ for a specified duration.
        
        Args:
            data_taking_time (int): The duration in seconds for which the DAQ should run. Default is 10 seconds.
        """
        logger.debug("Starting DAQ")
        
        # Start daq
        self.start_daq()
        
        time.sleep(1)
        
        # Wait for data taking
        wait_duration = max(1, data_taking_time - 1)
        time.sleep(wait_duration)
        logger.debug("DAQ data taking complete.")
        logger.debug("Stopping DAQ")
        
        # Stop daq
        self.stop_daq()
