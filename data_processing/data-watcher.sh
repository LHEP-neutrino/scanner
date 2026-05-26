#!/bin/bash

WATCH_DIR="/mnt/data/"
PATTERN="_summary.json"

inotifywait -m "$WATCH_DIR" \
    -e close_write \
    -e moved_to \
    --format '%e %w%f' \
    | grep --line-buffered "${PATTERN}$" \
    # IF inotifywait version is 3.20.11 or higher, you can use the following command instead of grep:
    # --include ".*${PATTERN}$" \
    | while read -r event filepath; do
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Event: $event — dispatching: $filepath"
        systemctl start data-processing@"$(systemd-escape "$filepath")"
    done