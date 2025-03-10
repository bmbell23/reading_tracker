#!/bin/bash

# Set up environment
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
cd /home/brandon/projects/reading_tracker

# Activate virtual environment (adjust path if needed)
source .venv/bin/activate

# Run the chain report command
python src/reading_list/cli/generate_reports.py chain

# Deactivate virtual environment
deactivate
