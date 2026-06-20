#!/usr/bin/env python3
import sys
import os
import json
import re
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import argparse
import subprocess
import h5py

from calibWvfms import calibWvfms

# Logging is done automatically by systemd, it can be viewed with `journalctl -u data-processing@*`

ADCS =[0]

CHANS = [0,1,2,3,4,5,6]

SIGNAL_WINDOW = [35,70]


def _compute_files_path(raw_file, verbose=False):
    """
    Compute the flow file path from the raw file path.

    Args:
        raw_file (str): The path to the raw data file.
    Returns:
        flow_file (str): The path to the future flowed file.
    """
    # Get the directory and create the flow directory if it doesn't exist
    file_dir = os.path.dirname(raw_file)
    flow_file_dir = os.path.join(file_dir, "flow")
    os.makedirs(flow_file_dir, exist_ok=True)
    
    # Get the filename without the extension (removes .data)
    filename = os.path.splitext(os.path.basename(raw_file))[0]
    
    # Construct the flow file
    flow_filename = filename + '.FLOW.hdf5'
    flow_file = os.path.join(flow_file_dir, flow_filename)

    if verbose:
        # Construct the waveform examples PDF file path
        wvfmExamples_filename = filename + '_wvfmsExamples.pdf'
        wvfmExamples = os.path.join(flow_file_dir, wvfmExamples_filename)

    else:
        wvfmExamples = None

    return flow_file, wvfmExamples

def _flow_file(raw_file,flow_file):
    """
        Flow the raw file using ndlar-flow and save the result to the flow file path.

        Args:
            raw_file (str): The path to the raw data file.
            flow_file (str): The path to save the flowed file.

    """

    print(f"Flowing file: {raw_file} to {flow_file}.")

    try:
        command = ["h5flow", "-c", "/home/lhep/scanner/ndlar_flow/yamls/TUNE_flow/workflows/light/light_event_building_scanner.yaml", "-i", raw_file, "-o", flow_file]
        
        result = subprocess.run(command,
                                cwd="/home/lhep/scanner/ndlar_flow", #Set working directory to where the h5flow command is available
                                capture_output=True,   # Capture stdout and stderr
                                text=True,             # Decode output to string
                                check=True)            # Raise an exception if the command fails

        # Log the standard output
        if result.stdout:
            print("Command output:\n%s", result.stdout)

    except subprocess.CalledProcessError as e:
        # Log the error message and the command output if available
        print(f"WARNING: Flowing for file {raw_file} failed with return code {e.returncode}")
        print(f"Error output:\n{e.stderr if e.stderr else 'No error output'}")

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

    # if verbose and wvfmExamples:
    #     print(f"print some waveform examples to: {wvfmExamples}")
    #     with PdfPages(wvfmExamples) as pdf:
    #         for i in range(10):
    #             # plot the 10 first wavefomrs
    #             fig, ax = plt.subplots()
    #             ax.plot(np.random.rand(100))  # Simulate a waveform with random data
    #             ax.set_title(f"Waveform Example {i+1}")
    #             pdf.savefig(fig)
    #             plt.close(fig)
        
    # Load calibration class
    wvfms = calibWvfms(filedir = os.path.dirname(flowed_file), filename = os.path.basename(flowed_file), output_path=os.path.dirname(flowed_file))
                
    wvfms.compute_mean_integrals(Nevent=9000, adcs=ADCS, chans=CHANS, int_window=SIGNAL_WINDOW, cut = '1peak', baseline_correction=True, minWidth=3, verbose=False)

    metrics = {}
    metrics["mean_integrals"] = {}
    for adc in ADCS:
        metrics["mean_integrals"][adc] = {}
        for chan in CHANS:
            # print(f"ADC: {adc}, CHAN: {chan}, Mean Integral: {wvfms.mean_integrals[adc][chan]}")
            metrics["mean_integrals"][adc][chan] = wvfms.mean_integrals[adc][chan]
    
    return metrics

def _data_process(summary_file, verbose=False):
    """
    Process the scanner data files to compute metrics for plotting.

    1. Read the summary file, get the raw data files path

    2. Flow the data, store them in a 
    
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
        scan_summary = summary_data.get("scan_summary", {})


       
    # Regex to capture the number after 'scan_pt_'
    pattern = re.compile(r'^scan_pt_(\d+)$')

    # Loop through the scan points in the summary and process each data file
    for scan_pt in scan_summary.keys():
        if pattern.match(scan_pt):
            # Get raw file path
            raw_file = scan_summary[scan_pt].get("data_file", "")

            # Compute flow_file and pdf example name 
            flow_file, wvfmExamples = _compute_files_path(raw_file, verbose=verbose)

            # Flow the file
            is_flowed = _flow_file(raw_file, flow_file)

            if is_flowed == 0:
                # Save flowed file path in the summary for reference
                scan_summary[scan_pt]["flowed_file"] = flow_file

                # Compute metrics
                metrics = _compute_metrics(flow_file, verbose=verbose, wvfmExamples=wvfmExamples)
                scan_summary[scan_pt]["metrics"] = metrics
            else:
                scan_summary[scan_pt]["flowed_file"] = None
            
    summary_data["scan_summary"] = scan_summary
    
    # Save the updated summary data back to the file
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, indent=4, ensure_ascii=False)

def _2d_plots(start, end, N_steps, metrics, title="Scan Metrics", xlabel="X [mm]", ylabel="Y [mm]", colorbar_label="Metric Value", verbose=False):
    """
    Create 2D plots of the metrics.

    Args:
        start (list): The starting position of the scan [x, y].
        end (list): The ending position of the scan [x, y].
        N_steps (list): The number of steps in x and y directions [N_x, N_y].
        metrics (numpy.ndarray): A dictionary containing the computed metrics for each scan point.
        title (str): The title of the plot.
        xlabel (str): The label for the x-axis.
        ylabel (str): The label for the y-axis.
        colorbar_label (str): The label for the colorbar.
    """
    x_edges = np.linspace(start[0], end[0], N_steps[0]+1)
    y_edges = np.linspace(start[1], end[1], N_steps[1]+1)
    bin_2d = metrics

    if verbose:
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
            
    fig.colorbar(mesh, ax=ax, label=colorbar_label)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    plt.show()
    # print(f"Plotting and saving results for scan: {scan_info.get('scan_name', 'Unknown')}")
    
def _plot_and_save(summary_file, verbose=False):
    """
    Plot the calculated metrics and save the results to files.
    
    Args:
        summary_file (str): The path to the summary JSON file containing the metrics.
        verbose (bool): Whether to print verbose output.
    """
    # Read the summary file and extract the scan info and metrics
    print(f"Plotting results from summary file: {summary_file}")
    with open(summary_file, 'r') as f:
        summary_data = json.load(f)
        scan_summary = summary_data.get("scan_summary", {})
        # scan_info = summary_data.get("scan_info", {})

    # Extract necessary information for plotting
    start_point = scan_summary.get("start_pos", [0, 0])
    end_point = scan_summary.get("end_pos", [296, 461])
    N_steps = scan_summary.get("N_steps", None)
    integrals = scan_summary.get("metrics", {}).get("mean_integrals", {})
    
    if N_steps is not None:
        _2d_plots(start_point, end_point, N_steps, integrals, colorbar_label='Pulse Integral [ADC unit]', verbose=verbose)


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
    else:
        print(f"Processing: {args.file_path}")

    summary_file_path = args.file_path
    
    # #DEBUG
    # summary_file_path = "/Users/nsallin/develop/scanner/data/scanner_summary/20260522_1811_4-09_summary.json"  
    if not os.path.isfile(summary_file_path):
        print(f"File does not exist or is not a file: {summary_file_path}")
        sys.exit(1)

    # Process the summary file
    _data_process(summary_file_path, verbose=args.verbose)
    
    print("File updated successfully.")

    # # Plot and store the results
    # _plot_and_save(summary_file_path, verbose=args.verbose)
    print("TODO: Plotting is not implemented yet.")

if __name__ == "__main__":
    main()