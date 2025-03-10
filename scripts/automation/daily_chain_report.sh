#!/bin/bash

# Set up environment
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# Use absolute paths
PROJECT_DIR="/home/brandon/projects/reading_tracker"
VENV_DIR="$PROJECT_DIR/venv"

# Change to project directory
cd "$PROJECT_DIR"

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Run the chain report command using the reading-list CLI
# Redirect stderr to suppress SQLAlchemy warnings
reading-list chain-report 2>/dev/null

# Deactivate virtual environment
deactivate

# Log completion
echo "Chain report completed at $(date)" >> "$PROJECT_DIR/logs/cron_chain_report.log"
