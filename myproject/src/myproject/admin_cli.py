import click
import platform
import subprocess
import sys
import os

SERVICE_NAME = "myproject_server"

def log(msg):
    click.echo(msg)
    try:
        subprocess.run(["logger", f"myproject-admin: {msg}"])
    except Exception:
        pass

def ensure_linux():
    if platform.system() != "Linux":
        log("myproject-admin is only supported on Linux systems using systemd.")
        sys.exit(1)

def ensure_root():
    if os.geteuid() != 0:
        log("This command must be run as root. Try again with sudo.")
        sys.exit(1)

def run_systemctl(args):
    subprocess.run(["systemctl"] + args, check=True)

@click.group()
def cli():
    """Administrative commands for MyProject."""
    pass

@cli.group()
def server():
    """Manage the MyProject server service."""
    pass

@server.command()
@click.option("--dry-run", is_flag=True, help="Simulate the command without executing it")
def start(dry_run):
    ensure_linux()
    ensure_root()
    if dry_run:
        log(f"[DRY-RUN] Would run: systemctl start {SERVICE_NAME}")
        return
    run_systemctl(["start", SERVICE_NAME])
    log("Server started.")

@server.command()
@click.option("--dry-run", is_flag=True, help="Simulate the command without executing it")
def stop(dry_run):
    ensure_linux()
    ensure_root()
    if dry_run:
        log(f"[DRY-RUN] Would run: systemctl stop {SERVICE_NAME}")
        return
    run_systemctl(["stop", SERVICE_NAME])
    log("Server stopped.")

@server.command()
@click.option("--dry-run", is_flag=True, help="Simulate the command without executing it")
def restart(dry_run):
    ensure_linux()
    ensure_root()
    if dry_run:
        log(f"[DRY-RUN] Would run: systemctl restart {SERVICE_NAME}")
        return
    run_systemctl(["restart", SERVICE_NAME])
    log("Server restarted.")

@server.command()
def status():
    ensure_linux()
    subprocess.run(["systemctl", "status", SERVICE_NAME])
