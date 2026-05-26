#!/usr/bin/env python3
import sys
import os
import json
import re
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import argparse

# Logging is done automatically by systemd, it can be viewed with `journalctl -u data-processing@*`


def _compute_files_path(raw_file, verbose=False):
    """
    Flow the raw data file return the path to the flowed file.

    Args:
        raw_file (str): The path to the raw data file.
    Returns:
        folw_file (str): The path to the flowed file.
    """
    # print(f"Flowing {raw_file}")

    # 1. Check that the file exists and is a file (not a directory)
    # if os.path.isfile(raw_file):

    # 2. Get the directory and create the flow directory if it doesn't exist
    file_dir = os.path.dirname(raw_file)
    flow_file_dir = os.path.join(file_dir, "flow")
    # os.makedirs(flow_file_dir, exist_ok=True)
    
    # 3. Get the filename without the extension (removes .data)
    filename = os.path.splitext(os.path.basename(raw_file))[0]
    
    # 4. Construct the flow file
    flow_filename = filename + '.FLOW.hdf5'
    flow_file = os.path.join(flow_file_dir, flow_filename)

    if verbose:
       
        wvfmExamples_filename = filename + '_wvfmsExamples.pdf'
        wvfmExamples = os.path.join(flow_file_dir, wvfmExamples_filename)

    else:
        wvfmExamples = None

    return flow_file, wvfmExamples

def _flow_file(raw_file,flow_file):

    # else:
    #     print(f"ERROR:File does not exist or is not a file: {raw_file}")
    #     return None

    try:
        # Simulate the flow process (replace with actual flow command)
        # For example, if the flow command is `flow_data --input raw_file --output flowed_file`
        # you would use subprocess to call it like this:
        # subprocess.run(["flow_data", "--input", raw_file, "--output", flowed_file], check=True)

        # Here we just simulate the flow by copying the file (replace with actual flow logic)
        
        print(f"Flowing file: {raw_file} to {flow_file}.")

    except Exception as e:
        print(f"Error flowing file {raw_file}: {e}")
        return 1

    return 0

def _compute_metrics(flowed_file, verbose=False, wvfmExamples=None):
    """
    Compute the metrics from the flowed file.

    Args:
        flowed_file (str): The path to the flowed file.
        verbose (bool): Whether to print verbose output.
        wvfmExamples (str): The path to save waveform examples if verbose is True.
    Returns:
        metrics (dict): A dictionary containing the computed metrics.
    """
    # read file

    # compute metrics
    # for i in range(Number of event):
        #do something

    if verbose and wvfmExamples:
        print(f"print some waveform examples to: {wvfmExamples}")
        with PdfPages(wvfmExamples) as pdf:
            for i in range(10):
                # plot the 10 first wavefomrs
                fig, ax = plt.subplots()
                ax.plot(np.random.rand(100))  # Simulate a waveform with random data
                ax.set_title(f"Waveform Example {i+1}")
                pdf.savefig(fig)
                plt.close(fig)
        
                
    
    # Simulate metric computation (replace with actual metric calculation)
    metrics = {
        "metric_1": 0.5,
        "metric_2": 0.8
    }
    
    return metrics

def _data_process(summary_file, verbose=False):
    """
    Process the data files to calculate metrics for plotting.

    1. Read the summary file

    2. Flow the data
    
    3. Exploit the data
    
    Return the variables necessary for plotting.

    TODO: Step 2 and 3 are designed to handle one file at a time, in the optic to parallelize the processing in the future. 

    Args:
        summary_file (str): The path to the summary JSON file.
            verbose (bool): Whether to print verbose output.
    Returns:
        scan_summary (dict): A dictionary containing the scan summary information.
        plotting_info (dict): A dictionary containing scan information for plotting.
    """
    # Initialize variables
    plotting_info = {}

    # Read the summary file and extract the data files and scan info
    print(f"Processing summary file: {summary_file}")

    with open(summary_file, 'r') as f:
        summary_data = json.load(f)
        scan_name = summary_data.get("scan_name", {})
        lt_serial = summary_data.get("lt_serial", {})
        # scan_comment = summary_data.get("scan_comment", {})
        # config_file = summary_data.get("config_file", {})
        scan_summary = summary_data.get("scan_summary", {})

    plotting_info["scan_name"] = scan_name
    plotting_info["lt_serial"] = lt_serial

       
    # Regex to capture the number after 'scan_pt_'
    pattern = re.compile(r'^scan_pt_(\d+)$')

    for key in scan_summary.keys():
        if pattern.match(key):
            raw_file = scan_summary[key].get("data_file", "")
            flow_file, wvfmExamples = _compute_files_path(raw_file, verbose=verbose)
            is_flowed = _flow_file(raw_file, flow_file)
            if is_flowed == 0:
                scan_summary[key]["flowed_file"] = flow_file
                metrics = _compute_metrics(flow_file, verbose=verbose, wvfmExamples=wvfmExamples)
                scan_summary[key]["metrics"] = metrics
            else:
                scan_summary[key]["flowed_file"] = None
            

    # print(f"Scan info: {plotting_info}")

    return scan_summary, plotting_info
    
def _plot_and_save(scan_summary, scan_info, verbose=False):
    """
    Plot the calculated metrics and save the results to files.
    
    Args:
        scan_summary (dict): A dictionary containing the scan summary information.
        scan_info (dict): A dictionary containing scan information for plotting.
        verbose (bool): Whether to print verbose output.
    """
    # Simulate plotting (replace with actual plotting logic)
    corner1 = [0,0]
    corner2 = [296, 461]
    N_steps = [2, 5]
    x_edges = np.linspace(corner1[0], corner2[0], N_steps[0]+1)
    y_edges = np.linspace(corner1[1], corner2[1], N_steps[1]+1)
    bin_2d = np.random.rand(N_steps[1], N_steps[0])

    print(f"X edges: {x_edges}")
    print(f"Y edges: {y_edges}")
    print(f"2D bins: {bin_2d}")


    fig, ax = plt.subplots()
    mesh = ax.pcolormesh(x_edges, y_edges, bin_2d)
    # Add text in the center of each 2D bin
    for i in range(len(y_edges) - 1):
        for j in range(len(x_edges) - 1):
            x_center = (x_edges[j] + x_edges[j+1]) / 2
            y_center = (y_edges[i] + y_edges[i+1]) / 2
            ax.text(x_center, y_center, str(f"{bin_2d[i, j]:.2f}"),
                    ha='center', va='center', fontsize=9, color='white', fontweight='bold')
            
    fig.colorbar(mesh, ax=ax, label='Pulse Integral [ADC unit]')
    ax.set_xlabel('X [mm]')
    ax.set_ylabel('Y [mm]')
    ax.set_title(f"Scan: {scan_info.get('scan_name', 'Unknown Scan')}")
    plt.show()
    # print(f"Plotting and saving results for scan: {scan_info.get('scan_name', 'Unknown')}")


def main():
    parser = argparse.ArgumentParser(description='Process the scanner data from a summary file and plot the results.')

    # Optional flag: -v / --verbose
    parser.add_argument('-v', '--verbose',
                        action='store_true',       # True if flag is present, False otherwise
                        help='Enable verbose output')

    # Positional argument: required file path
    parser.add_argument('file_path',
                        type=str,
                        help='Path to the JSON summary file')

    args = parser.parse_args()

    # Use the arguments
    if args.verbose:
        print(f"Verbose mode on. Processing: {args.file_path}")

    print(f"File path: {args.file_path}")

    summary_file_path = args.file_path
    
    #DEBUG
    summary_file_path = "/Users/nsallin/develop/scanner/data/scanner_summary/20260522_1811_4-09_summary.json"  
    if not os.path.isfile(summary_file_path):
        print(f"File does not exist or is not a file: {summary_file_path}")
        sys.exit(1)

    # Process the summary file
    scan_summary, scan_info = _data_process(summary_file_path, verbose=args.verbose)

    # Plot and store the results
    _plot_and_save(scan_summary, scan_info, verbose=args.verbose)

if __name__ == "__main__":
    main()