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
            # Small delay to let the hardware settle (mandatory otherwise doesn't work)
            time.sleep(1)
            
            if not self.ports.is_open:
                raise ConnectionError("Failed to open serial port.")
            
            click.echo(f"Port opened successfully.")

            # Initialization Sequence
            click.echo("Performing initialization sequence...")
            self._send_command('\r\n\r\n') # Hit enter to wake up the printer
            #self.ports.flushInput() # Flush startup test in serial input
            #self._send_command('G71\n')
            click.echo(f"0: in_waiting: {self.ports.in_waiting}")
            self._send_command('G21\n') # Metric units
            self._send_command('G90\n') # Absolute positioning
            self._send_command('G28\n') # Home all axes

            click.echo(f"1: in_waiting: {self.ports.in_waiting}")
            #self._wait_for_idle() # Wait for homing to complete

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
        self.go_to(350, 350, 20)
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

    # def _send_command(self, command: str) -> str:
    #     """
    #     Send a G-code command and wait for a response.
    #     Returns the response string (stripped) or raises an error if response indicates failure.
    #     """
    #     if not self.ports or not self.ports.is_open:
    #         raise RuntimeError("Serial port is not open. Re-initialize or check connection.")

    #     # Send command
    #     click.echo(f"Send command {command}")
    #     self.ports.write(command.encode())
        
    #     time.sleep(1)
    #     # Wait for response with timeout
    #     try:
    #         response_bytes = self.ports.readline()
            
    #         # Check if we timed out (empty bytes)
    #         if not response_bytes:
    #             click.echo(f"Warning: No response received for command: {command.strip()}")
    #             return "TIMEOUT"
            
    #         response = response_bytes.decode('utf-8', errors='ignore').strip()
    #         click.echo(f"Response: {response}")
            
    #         # Basic error checking
    #         if "error" in response.lower() or "alarm" in response.lower():
    #             raise RuntimeError(f"Printer Error: {response}")
                
    #         return response

    #     except serial.SerialException as e:
    #         click.echo(f"Serial communication error: {e}")
    #         raise

    def _send_command(self, command: str) -> str:
        """
        Send a G-code command, read the immediate response, 
        AND drain all remaining messages from the buffer before returning.
        """
        if not self.ports or not self.ports.is_open:
            raise RuntimeError("Serial port is not open.")

        # 1. Send the command
        self.ports.write(command.encode())
        
        try:
            # 2. Read the PRIMARY response (e.g., "ok")
            # This blocks until a line is received or timeout occurs
            response_bytes = self.ports.readline()
            
            #if not response_bytes:
            #    click.echo(f"Warning: Timeout waiting for response to: {command.strip()}")
            #    return "TIMEOUT"
            
            primary_response = response_bytes.decode('utf-8', errors='ignore').strip()
            click.echo(f"Cmd: {command.strip()} -> Resp: {primary_response}")
            
            # Check for immediate errors in the first response
            if "error" in primary_response.lower() or "alarm" in primary_response.lower():
                raise RuntimeError(f"Printer Error: {primary_response}")
            

            # 3. DRAIN THE BUFFER
            # Loop while there are bytes waiting to be read
            click.echo("Draining remaining buffer messages...")
            buffer_messages = []
            
            # We use a small internal timeout (e.g., 0.1s) to check if data is coming
            # without blocking indefinitely if the printer is silent.
            wait = 0
            while True: #self.ports.in_waiting > 0:
                # Read a line. If in_waiting > 0, this returns immediately (non-blocking for this specific read)
                # However, to be safe against a stream of data, we use a short timeout for this specific read
                #self.ports.timeout = 20 
                line_bytes = self.ports.readline()
                
                if line_bytes:
                    line = line_bytes.decode('utf-8', errors='ignore').strip()
                    if line:
                        buffer_messages.append(line)
                        click.echo(f"Buffer Msg: {line}")
                        wait = 0
                else:
                    # No line received within 0.1s, likely buffer is empty or closed
                    if wait == 3:
                        break
                    else:
                        click.echo(f"waiting for more messages ({wait})")
                        time.sleep(1)
                        wait += 1 
                        #break

            
            # Restore the main timeout for future operations
            # self.ports.timeout = self.timeout
            
            if buffer_messages:
                click.echo(f"  [Drained {len(buffer_messages)} extra messages]")
            else:
                click.echo("  [Buffer was empty after primary response]")
            
            click.echo(f"    Buffer size after command: {self.ports.in_waiting}")

            return primary_response

        except serial.SerialException as e:
            click.echo(f"Serial communication error: {e}")
            raise

    def _wait_for_idle(self):
        """
        Blocks execution until the printer is fully idle.
        Ensures physical movement (like homing) is complete.
        """
        click.echo("  [Waiting for printer to finish current action...]")
        
        max_wait = 30.0 
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                if self.ports.in_waiting > 0:
                    response = self.ports.readline().decode('utf-8', errors='ignore').strip()
                    click.echo(f" while waiting for idle: {response}")
                    if response == 'ok':
                        # Small extra delay to ensure buffer is truly empty
                        time.sleep(0.2) 
                        if self.ports.in_waiting == 0:
                            click.echo("  [Printer is Idle]")
                            return
                    elif "error" in response.lower() or "alarm" in response.lower():
                        raise RuntimeError(f"Printer Error during wait: {response}")
                
                time.sleep(0.1)
                
            except serial.SerialException:
                break
        
        click.echo("Warning: Timeout waiting for printer to become idle.")


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
        wait_time = abs(self.current_x-x) + abs(self.current_y-y) + abs(self.current_z-z)
        print(f" current: {self.current_x, self.current_y, self.current_z}; aim: {x,y,z}; sum of coordinate distance difference {wait_time}; time waiting: {min(int(wait_time/50), 15)}")
        time.sleep(min(int(wait_time/50), 15))
        print("finished waiting")
        self.current_x, self.current_y, self.current_z = x, y, z
        return

    def motors_off(self):
        """
        Disable stepper motors.
        """
        # M18 is standard for disabling all axes (Note: M84 is also widely supported).
        self._send_command('M18\n')
        return
