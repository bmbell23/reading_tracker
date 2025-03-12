#!/bin/bash

# Set up environment
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# Use absolute paths
PROJECT_DIR="/home/brandon/projects/reading_tracker"
VENV_DIR="$PROJECT_DIR/venv"
LOG_FILE="$PROJECT_DIR/logs/cron_db_backup.log"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Log start time
echo "Starting database backup at $(date)" >> "$LOG_FILE"

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

# Run the database backup using the reading-list CLI
# Redirect both stdout and stderr to log file
reading-list backup-db >> "$LOG_FILE" 2>&1

# Capture the exit status
EXIT_STATUS=$?

# Log completion status
if [ $EXIT_STATUS -eq 0 ]; then
    echo "Database backup completed successfully at $(date)" >> "$LOG_FILE"
else
    echo "Database backup failed with status $EXIT_STATUS at $(date)" >> "$LOG_FILE"
fi

# Deactivate virtual environment
deactivate

exit $EXIT_STATUS
```

Now, let's add it to the crontab configuration:

<augment_code_snippet path="dotfiles/cron/crontab.txt" mode="EDIT">
```
# Format: <schedule> <command> # <description>

# Reading Tracker Reports
0 9 * * * /home/brandon/projects/reading_tracker/scripts/automation/daily_report.sh # Daily reading progress report
0 8 * * * /home/brandon/projects/reading_tracker/scripts/automation/daily_chain_report.sh # Daily chain report
15 8 * * * /home/brandon/projects/reading_tracker/scripts/automation/daily_owned_report.sh # Daily owned books report

# Reading Tracker Database
0 2 * * * /home/brandon/projects/reading_tracker/scripts/automation/daily_db_backup.sh # Daily database backup

# System Maintenance
0 3 * * 0 /home/brandon/projects/dotfiles/scripts/maintenance/weekly_cleanup.sh # Weekly system cleanup
0 4 * * * /home/brandon/projects/dotfiles/scripts/maintenance/daily_backup.sh # Daily backup