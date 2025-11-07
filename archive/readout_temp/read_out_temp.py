import serial
import time
import pandas as pd
from scipy.stats import linregress

def calculate_temperature(aktueller_widerstand, df):
    # Die beiden Punkte mit dem nächstgelegenen Widerstand zum aktuellen Widerstand auswählen
    naechster_niedrigerer_widerstand = df[df['Widerstand'] <= aktueller_widerstand].max()['Widerstand']
    naechster_hoeherer_widerstand = df[df['Widerstand'] >= aktueller_widerstand].min()['Widerstand']

    # Filtern der Daten für die beiden Punkte
    subset_df = df[(df['Widerstand'] == naechster_niedrigerer_widerstand) | (df['Widerstand'] == naechster_hoeherer_widerstand)]

    # Linearer Fit nur für die beiden Punkte durchführen
    slope, intercept, _, _, _ = linregress(subset_df['Widerstand'], subset_df['Temperatur'])

    # Temperatur für den aktuellen Widerstand berechnen
    aktuelle_temperatur = slope * aktueller_widerstand + intercept

    return aktuelle_temperatur

ser = serial.Serial('/dev/ttyUSB0', 9600)  # Adjust the port as needed

# Dateipfad zur CSV-Datei anpassen
csv_file_path = 'ntcg163jf103ft1_no_text.csv'
df = pd.read_csv(csv_file_path, names=['Temperatur', 'Min', 'Widerstand','Max','B25/T','-dT','dT'], skiprows=0)
#print(df)
try:
    while True:
        if ser.in_waiting > 0:
            #first time is a zero sent that's why you need two reads.
            data = ser.readline().decode('utf-8').rstrip() 
            print(f'Resistance: {data} Ohms')
            time.sleep(3)
            data = ser.readline().decode('utf-8').rstrip()
            print(f'Resistance: {data} Ohms')

            # Widerstand vom Arduino Nano einlesen (Beispielwert)
            aktueller_widerstand = float(data)/1000  # Aktuellen Widerstand hier eintragen

            # Temperatur berechnen
            aktuelle_temperatur = calculate_temperature(aktueller_widerstand, df)

            # Ausgabe
            #print(f'Aktueller Widerstand: {aktueller_widerstand} Ohm')
            print(f'Berechnete Temperatur: {aktuelle_temperatur} °C')

            time.sleep(1)  # Adjust the delay as needed

except KeyboardInterrupt:
    ser.close()

