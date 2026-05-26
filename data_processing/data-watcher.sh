#!/bin/bash

WATCH_DIR="/mnt/data/"
PATTERN="_summary.json"

inotifywait -m "$WATCH_DIR" \
    -e close_write \
    -e moved_to \
    --format '%e %w%f' \
    --include ".*${PATTERN}$" \
    | while read -r event filepath; do
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Event: $event — dispatching: $filepath"
        systemctl start dataprocessor@"$(systemd-escape "$filepath")"
    done