import serial
from numpy import log
import time
from scanctrl.logger import logger  # Import the global logger

PORT     = '/dev/ttyUSB1'
BAUDRATE = 9600

# NTC constants — adjust to match your sensor's datasheet
R_NOMINAL = 10000.0  # resistance at 25°C
BETA      = 3380.0   # beta coefficient
T_NOMINAL = 25.0     # reference temperature in Celsius

def resistance_to_temperature(resistance):
    '''
        Use the Steinhart-Hart Beta Equation to convert the resistance of the NTC sensor to a temperature
        
        Args:
            resistance:     resistane readout on the NTC sensor
    
        Return:
            The temperature in Celsius equivalant to input 'resistance'
    '''
    steinhart  = resistance / R_NOMINAL        # R/R0
    steinhart  = log(steinhart)                # ln(R/R0)
    steinhart /= BETA                          # (1/Beta) * ln(R/R0)
    steinhart += 1.0 / (T_NOMINAL + 273.15)    # + 1/T0 (Kelvin)
    steinhart  = 1.0 / steinhart               # invert → Kelvin
    return steinhart - 273.15                  # convert to Celsius

class NTCReader:
    def __init__(self, port=PORT, baudrate=BAUDRATE, timeout=2, r_nominal=R_NOMINAL, beta=BETA, t_nominal=T_NOMINAL):
        """
        Initialize the connection to the Arduino.
        """
        self.port = port
        self.baudrate = baudrate

        self.r_nominal = r_nominal
        self.beta = beta
        self.t_nominal = t_nominal

        logger.debug(f"Opening connection to: {self.port} @ {self.baudrate}")
        logger.info(f"Initializing NTCReader...")
        
        
        try:
            # Add timeout=2.0 to prevent hanging if printer is unresponsive
            self.ports = serial.Serial(port, baudrate, timeout=timeout)
            # Small delay to let the hardware settle (mandatory otherwise the first command often gets lost)
            time.sleep(1)
            
            if not self.ports.is_open:
                logger.error(f"Failed to open serial port: {self.port}")
                raise ConnectionError("Failed to open serial port.")
            
            while True:
                T = self.read_temperature()  # Try to read a temperature to confirm the connection is working
                if isinstance(T, float):
                    logger.info(f"Initialization complete. NTCReader ready.Successfully read initial temperature: {T:.2f} °C")
                    break
            
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
        logger.info("Exiting NTCRReader, closing connection.")
        self._close()

    #-----------------------
    # Internal Helper functions
    #-----------------------

    def _close(self):
        """Close the serial connection safely."""
        if self.ports and self.ports.is_open:
            self.ports.close()
            self.ports = None
            logger.debug("Connection to the NTCReader closed.")

    #-----------------------
    # Main function
    #-----------------------

    def read_temperature(self):
        """
            Read a single temperature value from the NTC sensor. This function will block until a valid reading is obtained or a timeout occurs.
            
            Returns:
                The temperature in Celsius read from the sensor.
        """
        try:
            line = self.ports.readline().decode('utf-8').strip()
            logger.debug(f"Raw line read from NTCReader: '{line}'")
            
            if line:
                cleaned_line = line.replace('\x00', '').strip()
                if cleaned_line:
                    R = float(cleaned_line)
                    T = resistance_to_temperature(R)
                    logger.debug(f"Read resistance: {R:.2f} Ohm, converted to temperature: {T:.2f} deg. C")
                    return T
            else:
                logger.warning("No data received from NTCReader.")
                return None
            
        except (IndexError, ValueError) as e:
            logger.error(f"Could not parse line: '{line}' — {e}")
            return None

    