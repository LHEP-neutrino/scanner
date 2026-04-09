import click

@click.group()
def cli():
    """My Project CLI: A tool with multiple commands."""
    pass

@cli.command()
def debug():
    """Print 'hello' to the terminal."""
    click.echo("hello")

@cli.command()
@click.option('--text', '-t', required=True, help='The text to print.')
def print_cmd(text):
    """Print the provided text to the terminal.
    
    Usage: myproject print --text "Hello World"
    """
    click.echo(text)

if __name__ == '__main__':
    cli()