#!/bin/bash

# Set up environment
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# Use absolute paths
PROJECT_DIR="/home/brandon/projects/reading_tracker"
VENV_DIR="$PROJECT_DIR/venv"
LOG_FILE="$PROJECT_DIR/logs/cron_owned_report.log"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Log start time
echo "Starting owned books report at $(date)" >> "$LOG_FILE"

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

# Run the owned report command using the reading-list CLI
# Redirect both stdout and stderr to log file
reading-list owned-report >> "$LOG_FILE" 2>&1

# Capture the exit status
EXIT_STATUS=$?

# Log completion status
if [ $EXIT_STATUS -eq 0 ]; then
    echo "Owned books report completed successfully at $(date)" >> "$LOG_FILE"
else
    echo "Owned books report failed with status $EXIT_STATUS at $(date)" >> "$LOG_FILE"
fi

# Deactivate virtual environment
deactivate

exit $EXIT_STATUS
```

Now, let's add the cron job to your crontab configuration:

<augment_code_snippet path="reading_tracker/config/cron/crontab.txt" mode="EDIT">
```
# Reading Tracker Reports
0 8 * * * /home/brandon/projects/reading_tracker/scripts/automation/daily_chain_report.sh
15 8 * * * /home/brandon/projects/reading_tracker/scripts/automation/daily_owned_report.sh