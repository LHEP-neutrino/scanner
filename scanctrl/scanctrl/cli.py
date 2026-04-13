import click
import os

import scanctrl.client as cl


@click.group()
def cli():
    """
    Scanner CLI - A command-line interface for managing the scanner.
    """
    pass


    

@cli.command()
@click.option('--text', '-t', required=True, help='The text to print.')
def print_cmd(text):
    """Print the provided text to the terminal.
    
    Usage: myproject print --text "Hello World"
    """
    cl.print_text(text)
    
@cli.command()
@click.option('--config-file', '-c', help='Path to a configuration file. Default is "default_config.json".', default=os.path.normpath(os.path.join(os.path.dirname(__file__), '../default_config.json')))
def run_scanner(config_file):
    """
    Run the scanner.

    Usage: scanctrl run-scanner [OPTION]
    """
    # Check the provided argument
    config_file = os.path.normpath(config_file) 
    if not os.path.isfile(config_file):
        raise click.ClickException(f"The specified config file does not exist: {config_file}")

    # Run the scanner with the provided config file
    cl.run_scanner(config_file)

@cli.command(hidden=True)
def debug_printerctrl():
    """
    Command to debug the printer controller.

    Usage: scanctrl debug-printerctrl
    """
    cl.debug_printerCtrl()

if __name__ == '__main__':
    cli()