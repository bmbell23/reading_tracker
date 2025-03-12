#!/bin/bash

# Set up environment
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# Use absolute paths
PROJECT_DIR="/home/brandon/projects/reading_tracker"
VENV_DIR="$PROJECT_DIR/venv"
LOG_FILE="$PROJECT_DIR/logs/cron_goals_report.log"
REPORTS_DIR="$PROJECT_DIR/reports/yearly"

# Ensure log and reports directories exist
mkdir -p "$(dirname "$LOG_FILE")"
mkdir -p "$REPORTS_DIR"

# Set appropriate permissions for reports directory
chmod 755 "$REPORTS_DIR"

# Log start time
echo "Starting goals report at $(date)" >> "$LOG_FILE"

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

# Get current year and calculate next 5 years
CURRENT_YEAR=$(date +%Y)
YEARS=("$CURRENT_YEAR")
for i in {1..5}; do
    YEARS+=("$((CURRENT_YEAR + i))")
done

# Clean up old reports
echo "Cleaning up old reports..." >> "$LOG_FILE"
find "$REPORTS_DIR" -type f -name "*_reading_goals.html" | while read -r file; do
    year=$(echo "$file" | grep -o '[0-9]\{4\}')
    if [ -n "$year" ] && [ "$year" -lt "$CURRENT_YEAR" ]; then
        echo "Removing old report: $file" >> "$LOG_FILE"
        rm "$file"
    fi
done

# Generate reports for current and future years
echo "Generating reports for years: ${YEARS[*]}" >> "$LOG_FILE"
reading-list yearly "${YEARS[@]}" >> "$LOG_FILE" 2>&1

# Capture the exit status
EXIT_STATUS=$?

# Log completion status
if [ $EXIT_STATUS -eq 0 ]; then
    echo "Goals reports completed successfully at $(date)" >> "$LOG_FILE"
else
    echo "Goals reports failed with status $EXIT_STATUS at $(date)" >> "$LOG_FILE"
fi

# Deactivate virtual environment
deactivate

exit $EXIT_STATUS