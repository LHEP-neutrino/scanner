#!/bin/bash
set -e

echo "--- Stopping services"
systemctl stop data-watcher.service 2>/dev/null || true
systemctl stop 'data-processing@*.service' 2>/dev/null || true
systemctl disable data-watcher.service 2>/dev/null || true

echo "--- Removing unit files"
rm -f /etc/systemd/system/data-watcher.service
rm -f /etc/systemd/system/data-processing@.service
systemctl daemon-reload
systemctl reset-failed

echo "--- Removing scripts"
rm -f /usr/local/bin/data-watcher.sh
rm -f /usr/local/bin/data-processing.py

echo "--- Verifying"
systemctl list-unit-files | grep -E 'data-watcher|data-processing' \
    && echo "WARNING: unit files still found" \
    || echo "OK: no unit files remaining"

echo "Done."