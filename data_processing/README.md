# Summary File Watcher

Watches data folder for new `*_summary.json` files and dispatches each one to `data-processing.py` as an isolated systemd unit.

---

## How It Works

```
inotifywait detects /mnt/data/scanRun_summary.json (close_write or moved_to)
        ↓
data-watcher.sh calls systemd-escape on the file path
        ↓
systemctl start data-processing@"-mnt-data-scanRun_summary.json"
        ↓
systemd spawns data-processing@.service with %I = /mnt/data/scanRun_summary.json
        ↓
python3 data_processing.py /mnt/data/scanRun_summary.json
```

## File Structure

```
/etc/systemd/system/
  data-watcher.service     # Keeps the watcher script running
  data-processing@.service # Templated unit, one instance per file

/usr/local/bin/
  data-watcher.sh          # inotifywait loop, dispatches to systemd
  data_processing.py       # Your processing script
```

---

## Installation

After the installation of the necessary tool you can either install it through `install.sh` or manually

### Install dependencies

```bash
# Debian/Ubuntu
sudo apt install inotify-tools

# RHEL/Fedora
sudo dnf install inotify-tools
```

### Install script

To install the services direclty run

```bash
sudo bash /path/to/data_processing/install.sh
```

### Manual Installation
### 2. Install the watcher script

```bash
sudo cp data-watcher.sh /usr/local/bin/data-watcher.sh
sudo chmod +x /usr/local/bin/data-watcher.sh
```

### 3. Install your processing script

```bash
sudo cp data_processing.py /usr/local/bin/data_processing.py
sudo chmod +x /usr/local/bin/data_processing.py
```

### 4. Install the systemd units

```bash
sudo cp data-watcher.service /etc/systemd/system/
sudo cp data-processing@.service /etc/systemd/system/
```

### 5. Enable and start

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now data-watcher.service
```

### 6. Verify

```bash
sudo systemctl status data-watcher.service
```

---

## Usage

Once running, any `*_summary.json` file written to or moved into `/mnt/data/` will automatically trigger `data_processing.py`.

### Watch live logs from the watcher

```bash
sudo journalctl -u data-watcher.service -f
```

### Watch logs for a specific file processing run

```bash
# List recent dataprocessor instances
sudo journalctl -u 'data_processing@*' --since "10 minutes ago"

# Logs for a specific file
sudo journalctl -u "dataprocessor@$(systemd-escape '/mnt/data/scanRun_summary.json')"
```

### Test manually

```bash
# Trigger via close_write
echo '{}' > /data/test_summary.json

# Trigger via moved_to
echo '{}' > /tmp/test_summary.json && mv /tmp/test_summary.json /data/
```

---

## Troubleshooting

**Watcher not triggering**
- Confirm `inotify-tools` is installed: `which inotifywait`
- Check the watcher is running: `systemctl status data-watcher.service`
- Verify the `--include` regex matches your filename pattern

**Too many watches error**
- The kernel limits the number of inotify watches. Raise the limit if needed:
```bash
echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

**Files on NFS or network mounts not detected**
- `inotify` does not work on NFS, CIFS, or other remote filesystems. Use `fswatch` instead for network-mounted paths.

**Files arriving via atomic write (temp file + rename) not detected**
- Make sure `-e moved_to` is present in the `inotifywait` call. Atomic writes bypass `close_write` but always fire `moved_to`.

## Remove 

To remove the services run the following commands. There are condensed in cleanup.sh script.

### Cleanup script
To run the `cleanup.sh` script

```bash
sudo bash cleanup.sh
```

### Manual cleanup
#### 1. Stop the Running Units and disable the service
First, stop the path and service units immediately so they don't restart.

```bash
# Stop the watcher and any running processor instances
sudo systemctl stop data-watcher.service
sudo systemctl stop 'data-processing@*.service'

# Disable the watcher from starting on boot
sudo systemctl disable data-watcher.service
```

#### 2. Remove the systemd unit files
Remove the files and refresh systemd list of units.

```bash
sudo rm /etc/systemd/system/data-watcher.service
sudo rm /etc/systemd/system/data-processing@.service

# Reload systemd so it forgets the units
sudo systemctl daemon-reload

# Clear any lingering unit state (failed, etc.)
sudo systemctl reset-failed
```
#### 3. Remove teh scipts
```bash
sudo rm /usr/local/bin/data-watcher.sh
sudo rm /usr/local/bin/data_processing.py
```
#### 4. Verify nothing is left

```bash
# No units should match
systemctl list-units | grep -E 'data-watcher|data-processing'

# No unit files should match
systemctl list-unit-files | grep -E 'data-watcher|data-processing'

# No scripts left
ls /usr/local/bin/data-watcher.sh /usr/local/bin/data_processing.py 2>&1
```

