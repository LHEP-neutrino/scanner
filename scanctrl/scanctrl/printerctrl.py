import serial
import click
from typing import Optional
import time

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
        self.init_x, self.init_y, self.init_z = config["init_pos_LT"]  # Initial position for the LT (X, Y, Z)
        self.current_x, self.current_y, self.current_z = -1, -1, -1
        
        self.ports: Optional[serial.Serial] = None
        self.timeout = 2.0  # Seconds to wait for response

        click.echo(f"Initializing PrinterCtrl...")
        click.echo(f"Opening connection to: {config['usb_port']} @ {config['baudrate']}")
        
        try:
            # Add timeout=2.0 to prevent hanging if printer is unresponsive
            self.ports = serial.Serial(
                config["usb_port"], 
                config["baudrate"], 
                timeout=self.timeout
            )
            # Small delay to let the hardware settle
            time.sleep(1)
            
            if not self.ports.is_open:
                raise ConnectionError("Failed to open serial port.")
            
            click.echo(f"Port opened successfully.")

            # Initialization Sequence
            click.echo("Performing initialization sequence...")
            #self._send_command('\r\n\r\n') # Hit enter to wake up the printer
            #self.ports.flushInput() # Flush startup test in serial input
            #self._send_command('G71\n')
            self._send_command('G21\n') # Metric units
            self._send_command('G90\n') # Absolute positioning
            self._send_command('G28\n') # Home all axes

            click.echo(f" in_waiting: {self.ports.in_waiting}")
            i:int = 0
            while self.ports.in_waiting > 0:
                click.echo(f"loop {i}: {self.ports.readline().decode('utf-8', errors='ignore').strip()}")
                i += 1

            # Go to initial position
            click.echo(f"Moving to initial position: {self.init_x}, {self.init_y}, {self.init_z}")
            self.go_to(self.init_x, self.init_y, self.init_z)
            
            click.echo("Initialization complete. Printer ready.")

        except serial.SerialException as e:
            click.echo(f"Error: Could not connect to serial port. ({e})")
            raise
        except Exception as e:
            click.echo(f"Error during initialization: {e}")
            raise

    def __enter__(self):
        """Enter context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager and ensure port is closed."""
        self._close()
        return False # Let exceptions propagate if needed

    #-----------------------
    # Internal Helper functions
    #-----------------------

    def _close(self):
        """Close the serial connection safely."""
        if self.ports and self.ports.is_open:
            click.echo("Closing connection to the printer.")
            self.ports.close()
            self.ports = None

    def _send_command(self, command: str) -> str:
        """
        Send a G-code command and wait for a response.
        Returns the response string (stripped) or raises an error if response indicates failure.
        """
        if not self.ports or not self.ports.is_open:
            raise RuntimeError("Serial port is not open. Re-initialize or check connection.")

        # Send command
        click.echo(f"Send command {command}")
        self.ports.write(command.encode())
        
        time.sleep(1)
        # Wait for response with timeout
        try:
            response_bytes = self.ports.readline()
            
            # Check if we timed out (empty bytes)
            if not response_bytes:
                click.echo(f"Warning: No response received for command: {command.strip()}")
                return "TIMEOUT"
            
            response = response_bytes.decode('utf-8', errors='ignore').strip()
            click.echo(f"Response: {response}")
            
            # Basic error checking
            if "error" in response.lower() or "alarm" in response.lower():
                raise RuntimeError(f"Printer Error: {response}")
                
            return response

        except serial.SerialException as e:
            click.echo(f"Serial communication error: {e}")
            raise

    #-----------------------
    # Public API functions
    #-----------------------

    def go_to(self, x: float, y: float, z: float):
        """
        Move the printer to the specified position with range checks.
        """
        # Validate range
        if not (40 <= x <= 360):
            raise click.ClickException(f"X coordinate ({x}) out of range! Must be in range 40 to 360")
        if not (60 <= y <= 360):
            raise click.ClickException(f"Y coordinate ({y}) out of range! Must be in range 60 to 360")
        if z < 19:
            raise click.ClickException(f"Z coordinate ({z}) out of range! Must be >= 19")

        # Construct G0 command (Rapid Move)
        g_code = f'G0 X{x} Y{y} Z{z}\n'
        
        self._send_command(g_code)
        
        # Update internal state
        self.current_x, self.current_y, self.current_z = x, y, z
        return

    def motors_off(self):
        """
        Disable stepper motors.
        """
        # M18 is standard for disabling all axes (Note: M84 is also widely supported).
        self._send_command('M18\n')
        return
