#!/bin/bash

export PYTHONDONTWRITEBYTECODE=1

# Reading List Tracker Setup Script
# This script sets up the development environment for the Reading List project.

# Exit on any error
set -e

# Set workspace
export WORKSPACE=$(dirname "$(readlink -f "$0")")
echo "Setting up Reading List Tracker..."
echo "Workspace: $WORKSPACE"

# Create and update .env file
if [ ! -f "$WORKSPACE/config/.env" ]; then
    cp "$WORKSPACE/config/.env.example" "$WORKSPACE/config/.env"
    # Update workspace in .env
    sed -i "s|WORKSPACE=.*|WORKSPACE=\"$WORKSPACE\"|" "$WORKSPACE/config/.env"
    echo "Created and configured config/.env"
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -e .

# Create necessary directories
echo "Creating project directories..."
mkdir -p "$WORKSPACE/config/"
mkdir -p "$WORKSPACE/templates/excel/"
mkdir -p "$WORKSPACE/templates/email/"
mkdir -p "$WORKSPACE/docs/images/"
mkdir -p "$WORKSPACE/data/db/"
mkdir -p "$WORKSPACE/data/csv/"
mkdir -p "$WORKSPACE/data/backups/"
mkdir -p "$WORKSPACE/data/examples/"
mkdir -p "$WORKSPACE/logs/"
mkdir -p "$WORKSPACE/src/migrations/"

# Create .gitkeep files
touch "$WORKSPACE/data/db/.gitkeep"
touch "$WORKSPACE/data/csv/.gitkeep"
touch "$WORKSPACE/data/backups/.gitkeep"
touch "$WORKSPACE/logs/.gitkeep"

# Run tests with -B flag to prevent bytecode
echo "Running test suite..."
python -B -m pytest tests/

echo "Setup complete!"
echo "To activate the virtual environment:"
echo "  source venv/bin/activate"

