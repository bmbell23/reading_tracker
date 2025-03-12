#!/bin/bash

# Set up environment
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# Use absolute paths
PROJECT_DIR="/home/brandon/projects/reading_tracker"
VENV_DIR="$PROJECT_DIR/venv"
LOG_FILE="$PROJECT_DIR/logs/cron_chain_report.log"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Log start time
echo "Starting chain report at $(date)" >> "$LOG_FILE"

# Change to project directory
cd "$PROJECT_DIR" || {
    echo "Failed to change to project directory" >> "$LOG_FILE"
    exit 1
}

# Activate virtual environment
source "$VENV_DIR/bin/activate" || {
    echo "Failed to activate virtual environment" >> "$LOG_FILE"
    exit 1
}

# Run the chain report command using the reading-list CLI
# Redirect both stdout and stderr to log file
reading-list chain-report >> "$LOG_FILE" 2>&1

# Capture the exit status
EXIT_STATUS=$?

# Log completion status
if [ $EXIT_STATUS -eq 0 ]; then
    echo "Chain report completed successfully at $(date)" >> "$LOG_FILE"
else
    echo "Chain report failed with status $EXIT_STATUS at $(date)" >> "$LOG_FILE"
fi

# Deactivate virtual environment
deactivate

exit $EXIT_STATUS
```

To troubleshoot:

1. Check if the cron job is actually installed:
```bash
crontab -l | grep chain-report
```

2. Check the log file:
```bash
cat /home/brandon/projects/reading_tracker/logs/cron_chain_report.log
```

3. Test the script manually:
```bash
/home/brandon/projects/reading_tracker/scripts/automation/daily_chain_report.sh
```

4. Verify cron job installation:
```bash
/home/brandon/projects/dotfiles/scripts/cron/install_crons.sh check
```

The enhanced script should help identify where any failures might be occurring. Let me know what the above checks reveal and we can further diagnose the issue.
