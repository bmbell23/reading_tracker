#!/bin/bash

# Get project root using the .project-root marker file
PROJECT_ROOT="/home/brandon/projects/reading_tracker"

# Change to project root directory
cd "$PROJECT_ROOT"

# Activate virtual environment
source "$PROJECT_ROOT/venv/bin/activate"

# Set environment variable
export PYTHONPATH="$PROJECT_ROOT"

# Ensure the project root marker exists
touch "$PROJECT_ROOT/.project-root"

# Run the command using the CLI interface
reading-list email-report

# Deactivate virtual environment
deactivate