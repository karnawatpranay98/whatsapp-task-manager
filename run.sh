#!/bin/bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG="$DIR/run.log"
ENV_FILE="$DIR/.env"

# Load env vars
if [ -f "$ENV_FILE" ]; then
    export $(grep -v '^#' "$ENV_FILE" | xargs)
fi

echo "=== $(date) ===" >> "$LOG"

echo "Step 1: Fetching WhatsApp messages..." | tee -a "$LOG"
node "$DIR/whatsapp-fetcher/fetch.js" >> "$LOG" 2>&1

echo "Step 2: Analyzing with Claude..." | tee -a "$LOG"
python3 "$DIR/python-analyzer/analyze.py" >> "$LOG" 2>&1

echo "Step 3: Sending email..." | tee -a "$LOG"
python3 "$DIR/python-analyzer/send_email.py" >> "$LOG" 2>&1

echo "Done." | tee -a "$LOG"
