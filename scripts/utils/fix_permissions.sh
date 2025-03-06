#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate virtual environment
source "${SCRIPT_DIR}/../../venv/bin/activate"

# Run the Python script with sudo, preserving the PYTHONPATH
sudo PYTHONPATH="${PYTHONPATH}" "${SCRIPT_DIR}/fix_report_permissions.py"
