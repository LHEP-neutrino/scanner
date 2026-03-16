import click
from client import Client

client = Client()

# ----------------------------------------------------------------------
# Define root command
# ----------------------------------------------------------------------

@click.group()
def cli():
    """User commands for MyProject."""
    pass

# ----------------------------------------------------------------------
# Define subcommands
# ----------------------------------------------------------------------

@cli.command()
def status():
    """Check server status."""
    result = client.status()
    if "error" in result:
        click.echo(f"Error: {result['error']}")
    else:
        click.echo(f"Server status: {result.get('status')}")

@cli.command()
@click.option("--msg", default="hello", help="Message for debug command")
def debug(msg):
    """Send debug command to server."""
    result = client.debug({"message": msg})
    if "error" in result:
        click.echo(f"Error: {result['error']}")
    else:
        click.echo(f"Server response: {result.get('message')}")

@cli.command()
@click.option(
    "--path",
    required=True,
    type=click.Path(exists=True, file_okay=False, resolve_path=True),
    help="Path to the files to process",
)
def process_files(path):
    """Start files processing on the server."""
    result = client.process_data(path)

    if "error" in result:
        click.echo(f"Error: {result['error']}")
    else:
        click.echo(result.get("message"))