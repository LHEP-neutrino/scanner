const int pt100Pin = A2;  // ADC channel for PT100
const float refVoltage = 5.0;  // Reference voltage for ADC
const float rDivider = 10000.0;  // Resistance of the voltage divider

void setup() {
  Serial.begin(9600);
}

void loop() {
  int rawValue = analogRead(pt100Pin);
  float voltage = (rawValue / 1023.0) * refVoltage;
  float pt100Resistance = (rDivider * voltage) / (refVoltage - voltage);

  Serial.println(pt100Resistance);

  delay(1000);  // Adjust the delay as needed
}
