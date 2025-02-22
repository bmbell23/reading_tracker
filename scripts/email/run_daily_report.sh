#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"

# Activate virtual environment
source "$PROJECT_ROOT/venv/bin/activate"

# Run the report script
python "$PROJECT_ROOT/scripts/email/reading_report.py"

# Deactivate virtual environment
deactivate