const int T_sensor_pin = A2;  // ADC channel for NTC temp. sensor
const float ref_V = 5.0;  // Reference voltage for ADC
const float ref_R = 10000.0;  // Resistance of the voltage divider

void setup() {
  Serial.begin(9600);
}

void loop() {
  int sensor_rawVal = analogRead(T_sensor_pin); // ADC value (0-1023)
  float sensor_V = sensor_rawVal * (ref_V / 1023.0); // Measured voltage drop across sensor 
  float sensor_R = (ref_R * sensor_V) / (ref_V - sensor_V); // Measured resistance of the sensor

  Serial.println(sensor_R); // Send out the measured resistance

  delay(1000);  // Adjust the delay as needed [ms]
}
