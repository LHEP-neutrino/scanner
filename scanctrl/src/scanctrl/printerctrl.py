import serial
import click
from typing import Optional
import time

from scanctrl.logger import logger  # Import the global logger

X_LIM = [40, 360]
Y_LIM = [60, 360]
Z_LIM = [19, -1]

DEFAULT = [350,350,41]

class PrinterCtrl:
    """
    Controller for the 3D printer used in the scanning setup.
    Handles serial communication, initialization, and movement commands.
    """
    #-----------------------
    # Class Initialization and Context Management
    #-----------------------

    def __init__(self, config):
        """
        Initialize the printer connection and perform homing.
        """
        self.init_x, self.init_y, self.init_z = DEFAULT  # Initial position for the LT (X, Y, Z)
        self.current_x, self.current_y, self.current_z = -1, -1, -1
        
        self.ports: Optional[serial.Serial] = None
        self.timeout = 2.0  # Seconds to wait for response

        logger.info(f"Initializing PrinterCtrl...")
        logger.debug(f"Opening connection to: {config['usb_port']} @ {config['baudrate']}")
        
        try:
            # Add timeout=2.0 to prevent hanging if printer is unresponsive
            self.ports = serial.Serial(
                config["usb_port"], 
                config["baudrate"], 
                timeout=self.timeout
            )
            # Small delay to let the hardware settle (mandatory otherwise the first command often gets lost)
            time.sleep(1)
            
            if not self.ports.is_open:
                logger.error(f"Failed to open serial port: {config['usb_port']}")
                raise ConnectionError("Failed to open serial port.")
            
            logger.info(f"Port opened successfully.")

            # Initialization Sequence
            logger.info("Performing initialization sequence...")
            self._send_command('\r\n\r\n') # Hit enter to wake up the printer
            self._send_command('G21\n') # Metric units
            self._send_command('G90\n') # Absolute positioning
            self._send_command('G28\n') # Home all axes

            # Go to initial position
            logger.info(f"Moving to initial position.")
            self.go_to(self.init_x, self.init_y, self.init_z)

            # Position 0 = IN, Position 1 = OUT, -1 = UNKNOWN
            self.drawer_position = -1  
            
            logger.info("Initialization complete. Printer ready.")

        except serial.SerialException as e:
            logger.error(f"Serial communication error during initialization: {e}")
            raise
        except Exception as e:
            logger.error(f"Error during initialization: {e}")
            raise

    def __enter__(self):
        """
            Enter context manager. (Allow the class to be used with 'with' statement for automatic cleanup)
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
            Exit context manager:
                - Move printer head close to reference position (to avoid wrong initialization in next scan)
                - ensure port is closed.
        """
        logger.info("Exiting PrinterCtrl: Moving to safe position and closing connection.")
        self.go_to(*DEFAULT)
        self._close()

    #-----------------------
    # Internal Helper functions
    #-----------------------

    def _close(self):
        """Close the serial connection safely."""
        if self.ports and self.ports.is_open:
            self.ports.close()
            self.ports = None
            logger.debug("Connection to the printer closed.")

    def _send_command(self, command: str) -> str:
        """
        Send a G-code command and wait until the printer responds with 'ok'.
        Reads and prints all intermediate messages (busy, echo, etc.) in between.
        """
        if not self.ports or not self.ports.is_open:
            raise RuntimeError("Serial port is not open.")

        # 1. Send the command
        self.ports.write(command.encode())
        logger.debug(f"Sent: {command.strip()}")
        
        try:
            # 2. Loop until we get 'ok' or timeout/error
            # We use a counter to prevent infinite loops if the printer stops responding
            wait_counter = 0
            while True:
                # Read a line (blocks until data or timeout)
                response_bytes = self.ports.readline()
                
                # Check for timeout (empty bytes)
                if not response_bytes:
                    if wait_counter > 2:  # After 3 consecutive timeouts, give up
                        logger.debug(f"Timeout waiting for response to: {command.strip()}")
                        logger.debug(f"Bytes in waiting: {self.ports.in_waiting}")
                        return "TIMEOUT"
                    logger.debug(f"No response received yet for: {command.strip()} (waited {wait_counter+1} times)")
                    time.sleep(0.5)  # Wait a bit before trying again
                    wait_counter += 1
                    continue

                wait_counter = 0  # Reset counter on successful read    

                response = response_bytes.decode('utf-8', errors='ignore').strip()
                
                # A. Success: Command finished
                if response == "ok":
                    logger.debug("[Command completed successfully]")
                    logger.debug(f"Bytes in waiting: {self.ports.in_waiting}")
                    return "ok"
                
                # B. Error: Something went wrong
                if "error" in response.lower() or "alarm" in response.lower():
                    raise RuntimeError(f"Printer Error: {response}")
                
                # C. Busy or Status: Printer is still working or echoing info
                # We print it and continue the loop to wait for 'ok'
                if "busy" in response.lower() or response.startswith("echo:"):
                    if "busy" in response.lower():
                        logger.debug(f"[Printer is busy, waiting...: {response}]")
                    else:
                        logger.debug(f"[Status update: {response}]")
                    continue
                
                # D. Unexpected: Print and keep waiting
                # Some firmware versions send weird messages before 'ok'
                logger.debug(f"[Unexpected response, waiting for 'ok': {response}]")

        except serial.SerialException as e:
            logger.error(f"Serial communication error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise

    

    #-----------------------
    # Public API functions
    #-----------------------

    def go_to(self, x: float, y: float, z: float):
        """
        Move the printer to the specified position with range checks.
        """
        # Validate range
        if not (X_LIM[0] <= x <= X_LIM[-1]):
            raise click.ClickException(f"X coordinate ({x}) out of range! Must be in range {X_LIM[0]} to {X_LIM[-1]}")
        if not (Y_LIM[0] <= y <= Y_LIM[-1]):
            raise click.ClickException(f"Y coordinate ({y}) out of range! Must be in range {Y_LIM[0]} to {Y_LIM[-1]}")
        if z < Z_LIM[0]:
            raise click.ClickException(f"Z coordinate ({z}) out of range! Must be >= {Z_LIM[0]}")

        # Construct G0 command (Rapid Move) and send it
        g_code = f'G0 X{x} Y{y} Z{z}\n'
        self._send_command(g_code)
        
        # Wait time based on the travel distance
        max_diff = max(abs(self.current_x-x), abs(self.current_y-y), abs(self.current_z-z))
        wait_time = min(int(max_diff/20), 15)
        logger.debug(f"Current position: {self.current_x, self.current_y, self.current_z}; aim: {x,y,z}; max diff: {max_diff}; time waiting: {wait_time}")
        time.sleep(wait_time)

        # Update the current position
        self.current_x, self.current_y, self.current_z = x, y, z
        logger.debug(f"Printer head moved to ({x}, {y}, {z})")


    def motors_off(self):
        """
        Disable stepper motors.
        """
        # M18 is standard for disabling all axes (Note: M84 is also widely supported).
        self._send_command('M18\n')
        logger.debug(f"Printer motors disabled.")

