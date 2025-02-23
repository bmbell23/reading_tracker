#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"

# Change to project root directory
cd "$PROJECT_ROOT"

# Activate virtual environment
source "$PROJECT_ROOT/venv/bin/activate"

# Set additional environment variables
export PYTHONPATH="$PROJECT_ROOT"
export PROJECT_ROOT="$PROJECT_ROOT"

# Run the report script
python "$PROJECT_ROOT/scripts/email/reading_report.py"

# Deactivate virtual environment
deactivate
