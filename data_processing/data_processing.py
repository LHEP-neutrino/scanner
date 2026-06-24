#!/usr/bin/env python3
import sys
import os
import json
import re
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.patches as patches
import argparse
import subprocess
import h5py

from calibWvfms import calibWvfms

# Logging is done automatically by systemd, it can be viewed with `journalctl -u data-processing@*`

ADC = 0

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
                
    wvfms.compute_mean_integrals(Nevent=9000, adcs=[ADC], chans=CHANS, int_window=SIGNAL_WINDOW, cut = '1peak', baseline_correction=True, minWidth=3, verbose=False)

    metrics = {}
    metrics["mean_integrals"] = {}
    metrics["mean_integrals"][ADC] = {}
    for chan in CHANS:
        # print(f"ADC: {adc}, CHAN: {chan}, Mean Integral: {wvfms.mean_integrals[adc][chan]}")
        metrics["mean_integrals"][ADC][chan] = wvfms.mean_integrals[ADC][chan]
    
    return metrics

def _data_process(summary_file, verbose=0):
    """
    Process the scanner data files to compute metrics for plotting.

    1. Read the summary file, get the raw data files path

    2. Flow the data, save the flowed file path in the summary for reference
    
    3. Compute the metrics and save them in the summary file

    TODO: Step 2 and 3 are designed to handle one file at a time, in the optic to parallelize the processing in the future. 

    Args:
        summary_file (str): The path to the summary JSON file.
            verbose (int): The level of verbosity for output messages.
    """
    # Initialize variables
    plotting_info = {}

    # Read the summary file and extract the data files and scan info
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

def _2d_plots(x, y, val, title="Scan Metrics", xlabel="X [mm]", ylabel="Y [mm]",
              colorbar_label="Metric Value", x_lim=None, y_lim=None, equal_aspect=True, max_xticks = 10, max_yticks=15, max_xcell_label=10, z_scale=1):
    """
    Create a 2D histogram/heatmap of scan metrics, automatically inferring bin edges from the unique scan positions.

    Args:
        x (array-like): X position of each scan point.
        y (array-like): Y position of each scan point.
        val (array-like): Metric value at each scan point (same length as x, y).
        title (str): The title of the plot.
        xlabel (str): The label for the x-axis.
        ylabel (str): The label for the y-axis.
        colorbar_label (str): The label for the colorbar.
        x_lim (tuple): Optional (xmin, xmax) to set the x-axis limits.
        y_lim (tuple): Optional (ymin, ymax) to set the y-axis limits.
        max_xticks (int): Maximum number of ticks on the x-axis.
        max_yticks (int): Maximum number of ticks on the y-axis.
        max_xcell_label (int): Maximum number of x-cell when labels are displayed.
        z_scale (float): Scale factor for the z-axis.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    val = np.asarray(val, dtype=float)

    # Unique sorted positions along each axis -> these are the bin centers
    x_unique = np.unique(x)
    y_unique = np.unique(y)

    # Bin edges = midpoints between neighboring unique centers,
    # extrapolated by half a step on each end.
    def edges_from_centers(centers):
        if len(centers) == 1:
            # Single point: just make up a unit-width bin around it
            c = centers[0]
            return np.array([c - 0.5, c + 0.5])
        mids = (centers[:-1] + centers[1:]) / 2
        first_half_step = mids[0] - centers[0]
        last_half_step = centers[-1] - mids[-1]
        return np.concatenate(([centers[0] - first_half_step], mids, [centers[-1] + last_half_step]))

    x_edges = edges_from_centers(x_unique)
    y_edges = edges_from_centers(y_unique)

    # Map each scan point to its grid index
    x_idx = np.searchsorted(x_unique, x)
    y_idx = np.searchsorted(y_unique, y)

    # Get the bin values, np.nan for empty bins
    bin_2d = np.full((len(y_unique), len(x_unique)), np.nan)
    bin_2d[y_idx, x_idx] = val*z_scale

    # Create the 2D plot
    fig, ax = plt.subplots()
    mesh = ax.pcolormesh(x_edges, y_edges, bin_2d)

    # Add text in the center of each 2D bin (skip empty/NaN cells)
    if len(x_unique) <= max_xcell_label:
        for i in range(len(y_unique)):
            for j in range(len(x_unique)):
                if not np.isnan(bin_2d[i, j]):
                    ax.text(x_unique[j], y_unique[i], f"{bin_2d[i, j]:.2f}",
                            ha='center', va='center', fontsize=6, color='white', fontweight='bold')

    fig.colorbar(mesh, ax=ax, label=colorbar_label)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)

    if equal_aspect:
        ax.set_aspect('equal', adjustable='box')

    def centers_to_ticks(centers, max_ticks=10):
        """
        Compute the tick positions for the given centers, limiting to max_ticks.

        Args:
            centers (array-like): The unique center positions along an axis.
            max_ticks (int): The maximum number of ticks to display.
        Returns:
            ticks (array-like): The tick positions to use for the axis.
        """
        n = len(centers)
        if n <= max_ticks:
            return centers
        idx = np.linspace(0, n - 1, max_ticks).round().astype(int)
        idx = np.unique(idx)
        return centers[idx]
    
    # Define the height of the PCB box (3% of the y-axis range)
    pcb_height = abs(y_lim[1] - y_lim[0]) * 0.03

    if x_lim is not None:
        ax.set_xlim(x_lim)
        ax.set_xticks(centers_to_ticks(x_unique, max_ticks=max_xticks))
    if y_lim is not None:
        y_lim_wPCB = (y_lim[0]-pcb_height, y_lim[1])
        ax.set_ylim(y_lim_wPCB)
        ax.set_yticks(centers_to_ticks(y_unique, max_ticks=max_yticks))

    # Green box representing the cold PCB with label
    if x_lim is not None and y_lim is not None:
        box = patches.Rectangle(
            (x_lim[0], y_lim[0]-pcb_height),  # bottom left corner
            x_lim[1] - x_lim[0],
            pcb_height,
            linewidth=1, edgecolor='black', facecolor='green', alpha=0.8, clip_on=False
        )
        ax.add_patch(box)
        ax.text(
            (x_lim[0] + x_lim[1]) / 2, y_lim[0] - pcb_height*0.6,
            "COLD PCB",
            ha='center', va='center', fontsize=8, color='darkorange', fontweight='bold',
            clip_on=False
        )

    return fig, ax

def _extract_metric_data(scan_summary, metric_name):
    """
    Extract LT_x, LT_y, and summed metric (indices 0-5 of mean_integrals)
    for each scan point in scan_summary.

    Args:
        scan_summary (dict): Scan data, containing position and metric information.
        metric_name (str): The name of the metric to extract.

    Returns:
        x (np.ndarray): LT_x positions
        y (np.ndarray): LT_y positions
        val (np.ndarray): summed metric per scan point
    """
    n_points = np.prod(scan_summary["N_steps"])

    x_list = []
    y_list = []
    val_list = []

    for i in range(n_points):
        scan_pt = scan_summary[f"scan_pt_{i}"]

        x_list.append(scan_pt["LT_x"])
        y_list.append(scan_pt["LT_y"])

        val_list.append([scan_pt["metrics"][metric_name][str(ADC)][str(chan)] for chan in CHANS])

    return np.array(x_list), np.array(y_list), np.array(val_list)

def _get_sumIntegrals(scan_summary):
    """
    Compute the sum of integrals for each scan point in scan_summary.

    Args:
        scan_summary (dict): Scan data, containing position and metric information.

    Returns:
        sumIntegrals (np.ndarray): summed metric per scan point
    """
    x_coords, y_coords, Integrals = _extract_metric_data(scan_summary, "mean_integrals")

    return x_coords, y_coords, np.sum(Integrals[:, :6], axis=1)  # Sum over the channels (axis=1)

def _get_singleChanIntegrals(scan_summary, chan):
    """
    Get the integrals for a single channel for each scan point in scan_summary.

    Args:
        scan_summary (dict): Scan data, containing position and metric information.
        chan (int): The channel number to extract integrals for.

    Returns:
        x (np.ndarray): LT_x positions
        y (np.ndarray): LT_y positions
        val (np.ndarray): integrals for the specified channel per scan point
    """
    x_coords, y_coords, Integrals = _extract_metric_data(scan_summary, "mean_integrals")

    return x_coords, y_coords, Integrals[:, chan]  # Return only the specified channel's integrals
    
def _plot_and_save(summary_file, output=None, show_plots=False):
    """
    Plot the calculated metrics and save the results as plot(s).
    
    Args:
        summary_file (str): The path to the summary JSON file containing the metrics.
        output (str): The path to the output folder for the plot (default: Same folder as summary file).
    """
    # Read the summary file and extract the scan info and metrics
    print(f"Plotting results from summary file: {summary_file}")
    with open(summary_file, 'r') as f:
        summary_data = json.load(f)
        scan_summary = summary_data.get("scan_summary", {})
        scan_name = summary_data.get("scan_name", {})

    # Extract necessary information for plotting
    start_point = scan_summary.get("start_pos", [0, 0])
    end_point = scan_summary.get("end_pos", [296, 461])
    x_lim = (min(start_point[0], end_point[0]), max(start_point[0], end_point[0]))
    y_lim = (min(start_point[1], end_point[1]), max(start_point[1], end_point[1]))

    def get_output_filename(suffix):
        """
        Generate the output filename for the plot.

        Args:
            suffix (str): The suffix to add to the filename instead of 'summary'.

        Returns:
            str: The generated output filename.
        """
        if output:
            return os.path.join(output, os.path.basename(summary_file).replace("_summary.json", f"_{suffix}.png"))
        else:
            return summary_file.replace("_summary.json", f"_{suffix}.png")
    
    #---------------------------------------------------------------------
    # Sum of integrals over the channel plot
    #---------------------------------------------------------------------

    # Extract the data 
    sumIntegrals_val_plot = _get_sumIntegrals(scan_summary)
    
    # Make the plot
    fig_sumIntegrals, _ = _2d_plots(*sumIntegrals_val_plot, x_lim=x_lim, y_lim=y_lim,title=f"{scan_name} - Sum of Integrals", xlabel='X Position [mm]', ylabel='Y Position [mm]', colorbar_label=r'Sum of Integrals [$10^6$ ADC unit]', z_scale=1e-6)

    # Save the plot
    sumIntegrals_plot_filename = get_output_filename("sumIntegrals_plot")
    fig_sumIntegrals.savefig(sumIntegrals_plot_filename, dpi=300)
    print(f"Sum integrals plot saved to: {sumIntegrals_plot_filename}")

    #---------------------------------------------------------------------
    # Integrals of individual channel plots
    #---------------------------------------------------------------------

    figs_singleChanIntegrals = {}
    for chan in CHANS:
        # Extract the data
        chanIntegrals_val_plot = _get_singleChanIntegrals(scan_summary, chan=chan)

        # Make the plot for the single channel integrals
        figs_singleChanIntegrals[chan] = _2d_plots(*chanIntegrals_val_plot, x_lim=x_lim, y_lim=y_lim,title=f"{scan_name} - Channel {chan} Integrals", xlabel='X Position [mm]', ylabel='Y Position [mm]', colorbar_label=rf'Channel {chan} Integrals [$10^6$ ADC unit]', z_scale=1e-6)[0]  # Only keep the figure object

        # Save the channel 4 integrals plot
        chanIntegrals_plot_filename = get_output_filename(f"chan{chan}Integrals_plot")
        figs_singleChanIntegrals[chan].savefig(chanIntegrals_plot_filename, dpi=300)
        print(f"Channel {chan} integrals plot saved to: {chanIntegrals_plot_filename}")

    if show_plots:
        plt.show()  

    # Free the memory used by the figure(s)
    plt.close()

def main():
    """
    Main function to process the scanner data and plot the results.

    Usage:
        python data_processing.py [-v | -vv] [-o OUTPUT_FOLDER] [--plot-only] SUMMARY_FILE
    """
    parser = argparse.ArgumentParser(description='Process the scanner data from a summary file and plot the results.')

    # Optional flag: -v / --verbose
    parser.add_argument(
        "-v", 
        "--verbose", 
        action="count", 
        default=0,
        help="Increase verbosity: -v for detailed flow files summaries, -vv for additionally printing debug information"
    )
    
    # Optional flag: -o / --output
    parser.add_argument('-o', '--output',
                        type=str,
                        help='Path to the output folder for the plot(s) (default: Same folder as summary file)')

    # Positional argument: required file path
    parser.add_argument('file_path',
                        type=str,
                        help='Path to the scan JSON summary file')
    
    # Add the --plot-only flag
    parser.add_argument(
        "--plot-only", 
        action="store_true", 
        help="Skip data processing and run only the plotting step"
    )

    args = parser.parse_args()

    # Use the arguments
    summary_file_path = args.file_path
    if not os.path.isfile(summary_file_path):
        print(f"File does not exist or is not a file: {summary_file_path}")
        sys.exit(1)

    

    if args.output:
        if not os.path.isdir(args.output):
            print(f"Output path is not a valid directory: {args.output}")
            sys.exit(1)

    if args.verbose == 0:
        print(f"Processing file {summary_file_path}")
    elif args.verbose == 1:
        print(f"Processing file {summary_file_path} with detailed summaries")
    elif args.verbose >= 2:
        print(f"Processing file {summary_file_path} with detailed summaries and debug information")


    
    # Process the summary file
    show_plots = False
    if not args.plot_only:
        _data_process(summary_file_path, verbose=args.verbose)
    else:
        print("Skipping data processing phase. Running only the plotting phase.")
        if args.verbose > 0:
            show_plots = True
            print("Verbose mode is ON: Plots will be displayed interactively.")

    # Plot and store the results
    _plot_and_save(summary_file_path, output=args.output, show_plots=show_plots)

if __name__ == "__main__":
    main()