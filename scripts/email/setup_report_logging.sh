#!/bin/bash

# Get the project root directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"

# Create logs directory if it doesn't exist
LOGS_DIR="$PROJECT_ROOT/logs"
mkdir -p "$LOGS_DIR"

# Create log file if it doesn't exist
touch "$LOGS_DIR/daily_report.log"

# Set appropriate permissions
chmod 644 "$LOGS_DIR/daily_report.log"

echo "Logging setup complete. Logs will be written to: $LOGS_DIR/daily_report.log"