#!/bin/bash

# Get the absolute path to the project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create necessary directories
echo "Creating project directories..."
mkdir -p "$PROJECT_ROOT/src/reading_list/templates/"{email,excel,reports,tbr,styles}
mkdir -p "$PROJECT_ROOT/src/reading_list/templates/reports/"{chain,projected,yearly}
mkdir -p "$PROJECT_ROOT/config/"
mkdir -p "$PROJECT_ROOT/data/db/"
mkdir -p "$PROJECT_ROOT/data/csv/"
mkdir -p "$PROJECT_ROOT/data/backups/"
mkdir -p "$PROJECT_ROOT/data/examples/"
mkdir -p "$PROJECT_ROOT/logs/"
mkdir -p "$PROJECT_ROOT/src/migrations/"

# Create .gitkeep files
touch "$PROJECT_ROOT/data/db/.gitkeep"
touch "$PROJECT_ROOT/data/csv/.gitkeep"
touch "$PROJECT_ROOT/data/backups/.gitkeep"
touch "$PROJECT_ROOT/logs/.gitkeep"

# Run tests with -B flag to prevent bytecode
echo "Running test suite..."
python -B -m pytest tests/

echo "Setup complete!"
echo "To activate the virtual environment:"
echo "  source venv/bin/activate"

