#!/bin/bash
set -euo pipefail

# -------------------------------------------------------
# Configuration — adjust these to match your environment
# -------------------------------------------------------
WATCH_DIR="/mnt/data/"
PROCESS_SCRIPT="$(dirname "$0")/data_processing.py"
WATCHER_SCRIPT="$(dirname "$0")/data-watcher.sh"
WATCHER_SERVICE="data-watcher.service"
PROCESS_SERVICE="data-processing@.service"
INSTALL_DIR="/usr/local/bin"
SYSTEMD_DIR="/etc/systemd/system"

# -------------------------------------------------------
# Helpers
# -------------------------------------------------------
info()  { echo "[INFO]  $*"; }
ok()    { echo "[OK]    $*"; }
warn()  { echo "[WARN]  $*"; }
die()   { echo "[ERROR] $*" >&2; exit 1; }

# -------------------------------------------------------
# Checks
# -------------------------------------------------------
info "Checking prerequisites"

[[ "$EUID" -ne 0 ]] && die "This script must be run as root (sudo)"

command -v inotifywait &>/dev/null || die "inotifywait not found — install inotify-tools first:
  Debian/Ubuntu: sudo apt install inotify-tools
  RHEL/Fedora:   sudo dnf install inotify-tools"

command -v python3 &>/dev/null || die "python3 not found"

[[ -f "$WATCHER_SCRIPT" ]] \
    || die "Watcher script not found at: $WATCHER_SCRIPT"

[[ -f "$PROCESS_SCRIPT" ]] \
    || die "Processor script not found at: $PROCESS_SCRIPT"

[[ -f "$WATCHER_SERVICE" ]] \
    || die "Watcher service file not found at: $WATCHER_SERVICE"

[[ -f "$PROCESS_SERVICE" ]] \
    || die "Data processing service file not found at: $PROCESS_SERVICE"

[[ -d "$WATCH_DIR" ]] \
    || die "Data directory does not exist: $WATCH_DIR — create it first"

ok "All prerequisites met"

# -------------------------------------------------------
# Install scripts
# -------------------------------------------------------

# Note: Install is like cp but sets permissions in the same step.
info "Installing scripts to $INSTALL_DIR"

install -m 755 "$WATCHER_SCRIPT"  "$INSTALL_DIR/data-watcher.sh"
install -m 755 "$PROCESS_SCRIPT" "$INSTALL_DIR/data_processing.py"

ok "Scripts installed"

# -------------------------------------------------------
# Install systemd units
# -------------------------------------------------------
info "Installing systemd unit files to $SYSTEMD_DIR"

cp "$WATCHER_SERVICE" "$SYSTEMD_DIR/data-watcher.service"
cp "$PROCESS_SERVICE" "$SYSTEMD_DIR/data-processing@.service"

ok "Unit files installed"

# -------------------------------------------------------
# Enable and start the watcher service
# -------------------------------------------------------
info "Reloading systemd"
systemctl daemon-reload

info "Enabling and starting data-watcher.service"
systemctl enable --now data-watcher.service

# -------------------------------------------------------
# Verify
# -------------------------------------------------------
info "Verifying installation"

systemctl is-active data-watcher.service &>/dev/null \
    && ok "data-watcher.service is running" \
    || die "data-watcher.service failed to start — check: journalctl -u data-watcher.service"

ok "Installation complete"
echo ""
echo "Useful commands:"
echo "  Watch live logs:       journalctl -u data-watcher.service -f"
echo "  Watch processor logs:  journalctl -u 'data-processing@*' -f"
echo "  Check status:          systemctl status data-watcher.service"
echo "  Uninstall:             sudo bash cleanup.sh"