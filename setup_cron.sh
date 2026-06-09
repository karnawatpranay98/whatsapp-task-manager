#!/bin/bash
# Adds a 9pm nightly cron job. Run once to set up.

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CRON_LINE="0 21 * * * $DIR/run.sh"

# Check if already added
if crontab -l 2>/dev/null | grep -qF "$DIR/run.sh"; then
    echo "Cron job already exists."
else
    (crontab -l 2>/dev/null; echo "$CRON_LINE") | crontab -
    echo "Cron job added: runs daily at 9pm"
fi

echo ""
echo "Current cron jobs:"
crontab -l
