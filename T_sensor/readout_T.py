import serial
from numpy import log

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

with serial.Serial(PORT, BAUDRATE, timeout=2) as ser:
    print(f"Listening on {PORT} at {BAUDRATE} baud...")
    while True:
        line = ser.readline().decode('utf-8').strip()
        if line:
            try:
                R = float(line)
                #print(f"R: {R} and type: {type(R)}")
                T = resistance_to_temperature(R)
                #print(f"T: {T} and type: {type(T)}")
                print(f"Resistance: {R:.2f} Ohm -> Temperature: {T:.2f} deg. C")
            except (IndexError, ValueError) as e:
                print(f"Could not parse line: '{line}' — {e}")
