import uproot
import pandas as pd
import os
import glob

# List of relevant ROOT files to search for
files = [
"FACL_4p01_2_2_stabConv.root","FACL_4p04_2_2_stabConv.root","FACL_4p21_2_9_stabConv.root","FACL_4p09_2_1_stabConv.root",\
"FACL_4p02_2_2_stabConv.root","FACL_4p13_2_2_stabConv.root","FACL_4p20_2_5_stabConv.root",\
"FACL_4p07_2_1_stabConv.root","FACL_4p27_2_4_stabConv.root","FACL_4p11_2_3_stabConv.root","FACL_4p19_2_2_stabConv.root","FACL_4p14_2_2_stabConv.root",\
"FACL_4p24_2_4_stabConv.root","FACL_4p15_2_2_stabConv.root","FACL_4p08_2_2_stabConv.root","FACL_4p18_2_3_stabConv.root","FACL_4p22_2_6_stabConv.root",\
"FACL_4p06_2_3_stabConv.root","FACL_4p23_2_3_stabConv.root","FACL_4p05_2_3_stabConv.root",\
"FACL_4p12_2_3_stabConv.root","FACL_4p17_2_2_stabConv.root","FACL_4p00_2_2_stabConv.root","FACL_4p16_2_2_stabConv.root"   
]

# Output file for results
output_file = "ArCLight_scan_temp_results_dichroic_mirror_on_edge.txt"

# Delete old results file if it exists
if os.path.exists(output_file):
    os.remove(output_file)
    print(f"Existing file '{output_file}' was deleted.")

# Create a new results file with a header
with open(output_file, "w") as file:
    file.write("File_Name, Mean_Temperature, Std_Deviation\n")

# Track processed files to avoid duplicates
processed_files = set()

# Search for and process only the relevant files
for file_name in files:
    # Search for the file anywhere in the system
    found_files = glob.glob(f"**/{file_name}", recursive=True)

    if not found_files:
        print(f"File '{file_name}' not found. Skipping...")
        continue

    # Process the first found instance of the file
    root_file_path = found_files[0]

    # Check if the file has already been processed
    if file_name in processed_files:
        print(f"File '{file_name}' has already been processed. Skipping duplicate.")
        continue

    print(f"Processing file: {root_file_path}")

    # Open the ROOT file
    file = uproot.open(root_file_path)

    # Find the first tree
    keys = file.keys()
    if not keys:
        print(f"No trees found in file {file_name}. Skipping...")
        continue

    tree_name = keys[0].split(";")[0]  # Removes ";1"
    tree = file[tree_name]

    # Convert to Pandas DataFrame
    df = tree.arrays(library="pd")

    # Define column names (update if necessary)
    x_col = "x"
    y_col = "y"
    temp_col = "temp"

    # Remove invalid temperature values (-1 and values above 80)
    filtered_df = df[(df[temp_col] != -1) & (df[temp_col] <= 80)]

    # Compute mean temperature and standard deviation
    mean_temp = filtered_df[temp_col].mean()
    std_temp = filtered_df[temp_col].std()

    # Save results to file
    with open(output_file, "a") as result_file:
        result_file.write(f"{file_name}, {mean_temp:.2f}, {std_temp:.2f}\n")

    # Mark file as processed
    processed_files.add(file_name)

    # Display results in console
    print(f"File: {file_name}")
    print(f"Mean Temperature: {mean_temp:.2f} °C")
    print(f"Standard Deviation: {std_temp:.2f} °C")

print(f"All measurements completed. Results saved in '{output_file}'.")