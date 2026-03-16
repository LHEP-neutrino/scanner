import os
import click
import requests
from . import config

API_KEY = os.environ.get("YOUR_SERVICE_API_KEY", config.API_KEY)
DEFAULT_SERVER = config.SERVER_URL

@click.group()
def cli():
    """Remote CLI to control the server."""
    pass

@cli.command()
@click.option("--server", default=DEFAULT_SERVER, help="Server URL")
def start(server):
    """Start background task on server"""
    try:
        r = requests.post(f"{server}/start", headers={"X-API-KEY": API_KEY})
        r.raise_for_status()
        click.echo(r.json())
    except requests.RequestException as e:
        click.echo(f"Error: {e}")

@cli.command()
@click.option("--server", default=DEFAULT_SERVER, help="Server URL")
def stop(server):
    """Stop background task on server"""
    try:
        r = requests.post(f"{server}/stop", headers={"X-API-KEY": API_KEY})
        r.raise_for_status()
        click.echo(r.json())
    except requests.RequestException as e:
        click.echo(f"Error: {e}")

@cli.command()
@click.option("--server", default=DEFAULT_SERVER, help="Server URL")
def status(server):
    """Check status of background task"""
    try:
        r = requests.get(f"{server}/status", headers={"X-API-KEY": API_KEY})
        r.raise_for_status()
        click.echo(r.json())
    except requests.RequestException as e:
        click.echo(f"Error: {e}")
