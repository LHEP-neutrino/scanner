import click
import os

import scanctrl.client as cl



#-----------------------
# Group declaration
#-----------------------

@click.group()
def cli():
    """
    Scanner CLI - A command-line interface for managing the scanner.
    """
    pass

#-----------------------
# Main commands
#-----------------------
    
@cli.command()
@click.option('--config-file', '-c', help='Path to a configuration file. Default is "default_config.json".', default=os.path.normpath(os.path.join(os.path.dirname(__file__), '../default_config.json')))
def run_scanner(config_file):
    """
    Run the scanner.

    Usage: scanctrl run-scanner [OPTION]
    """
    # Check the provided argument
    config_file = os.path.normpath(config_file) 

    # Run the scanner with the provided config file
    cl.run_scanner(config_file)

@cli.command()
@click.option('--config-file', '-c', help='Path to a configuration file. Default is "default_config.json".', default=os.path.normpath(os.path.join(os.path.dirname(__file__), '../default_config.json')))
@click.option('--x-position', '-x', type=int, help='The x-coordinate of the scan position.', required=True)
@click.option('--y-position', '-y', type=int, help='The y-coordinate of the scan position.', required=True)
@click.option('--z-position', '-z', type=int, help='The z-coordinate of the scan position.', required=False, default=20)
def run_pt_scan(config_file, x_position, y_position, z_position):
    """
    Perform a single point scan at a specified position (X,Y).

    Usage: scanctrl run-pt-scan -x X -y Y [-z Z --config-file CONFIG_FILE]
    """
    # Check the provided argument
    config_file = os.path.normpath(config_file) 
    
    # Run the point scan with the provided config file and coordinates
    cl.run_point_scan(config_file, x=x_position, y=y_position, z=z_position) 


#-----------------------
# Hidden debug commands (not shown in help)
#-----------------------

@cli.command(hidden=True)
@click.option('--config-file', '-c', help='Path to a configuration file. Default is "default_config.json".', default=os.path.normpath(os.path.join(os.path.dirname(__file__), '../default_config.json')))
def debug_printerctrl(config_file):
    """
    Command to debug the printer controller.

    Usage: scanctrl debug-printerctrl
    """
    cl.debug_printerCtrl(config_file)

@cli.command(hidden=True)
@click.option('--text', '-t', required=True, help='The text to print.')
def debug_print_text(text):
    """Print the provided text to the terminal.
    
    Usage: myproject print --text "Hello World"
    """
    cl.debug_print_text(text)

#-----------------------
# Main entry point
#-----------------------

if __name__ == '__main__':
    cli()