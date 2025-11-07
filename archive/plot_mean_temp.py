import pandas as pd
import matplotlib.pyplot as plt
import re 

# Name der Datei mit den Temperaturdaten
input_file = "ArCLight_scan_temp_results_dichroic_mirror_on_edge.txt"

# Read the temperature stats file
df = pd.read_csv(input_file)

# Strip spaces from column names
df.columns = df.columns.str.strip()

# Function to clean file names
def format_filename(filename):
    # Remove the "FACL_" prefix
    filename = filename.replace("FACL_", "")
    # Remove the "_x_x_stabConv.root" suffix (matches "_number_number_stabConv.root")
    filename = re.sub(r"_\d+_\d+_stabConv\.root$", "", filename)
    # Replace "p" with "."
    filename = filename.replace("p", ".")
    return filename

# Apply the formatting function to file names
df["Formatted_Filename"] = df["File_Name"].apply(format_filename)

x_positions = range(len(df))
y_values = df["Mean_Temperature"]
y_errors = df["Std_Deviation"]

# Create the plot
plt.figure(figsize=(10, 6))
plt.errorbar(x_positions, y_values, yerr=y_errors, fmt='x', capsize=5, color='black', ecolor='black', linestyle='None')

plt.xlabel("Label")
plt.ylabel("Temperature (°C)")
plt.title("Average Temperatures of ArCLight Units")
plt.xticks(x_positions, labels=df["Formatted_Filename"], rotation=45, ha='right')
plt.grid(True, linestyle="--", alpha=0.6)

# Show the plot
plt.tight_layout()
plt.show()