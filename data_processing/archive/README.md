# Data Processing Automation with systemd

This project automates the processing of new summary JSON files using `systemd` path units. It monitors the `/data/` directory and executes a Python script whenever a new file matching `*_summary.json` is created or modified.

## Architecture

1. **`data-processing.path`**: Monitors `/data/` for files matching `*_summary.json`.
2. **`data-processing.service`**: Executes `data_processing.py` upon detection.

## Prerequisites

- A Linux system with `systemd` (most modern distributions).
- Python 3 installed.
- Necessary Python dependencies for your script.

## Installation Steps

### 1. Place Files
Copy the configuration files to the systemd directory (requires root privileges):

```bash
sudo cp data-processing.path /etc/systemd/system/
sudo cp data-processing.service /etc/systemd/system/
```

### 2. Edit Configuration

Update the placeholders in data-processing.service with your actual values:

- `ExecStart`: Change `/full/path/to/data_processing.py` to the absolute path of your script.
- `WorkingDirectory`: Set to the directory containing your script.
- `User`: Set to the username that should own the script execution.
- `Group`: Set to the group that should own the script execution.
Note: Standard `systemd.path` triggers do not automatically pass the filename as `$PATH`. You may need to verify if your script expects the filename via an environment variable or if it needs to scan the directory itself.

### 3. Reload and Enable

Reload the systemd manager configuration and enable the units to start on boot:
```bash
sudo systemctl daemon-reload
sudo systemctl enable data-processing.path
sudo systemctl start data-processing.path
```

### 4. Verify Status

Check if the path unit is active and watching the directory:
```bash
systemctl status data-processing.path
```

## Usage

1. Ensure the `/data/` directory exists.
2. Place a new JSON file in `/data/` with a name ending in `_summary.json` (e.g., `report_summary.json`).
The service will automatically trigger, run the Python script, and log output to the journal.

## Monitoring Logs

View the output of the script in the system journal:

View logs for the path unit
```bash
journalctl -u data-processing.path -f
```
View logs for the service execution
```bash
journalctl -u data-processing.service -f
```
## Troubleshooting

- Script not running? Check journalctl -u data-processing.service for error messages.
- Permissions? Ensure the User defined in the service has read access to /data/ and execute permissions for the Python script.
- Trigger Limit? If you are generating files too fast, the TriggerLimitIntervalSec=1s might be throttling execution. Adjust this value in the .path file if necessary.