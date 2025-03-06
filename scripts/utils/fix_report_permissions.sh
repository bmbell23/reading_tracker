#!/bin/bash

# Get the project root directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"
REPORTS_DIR="$PROJECT_ROOT/reports"

# Ensure reports directory exists
mkdir -p "$REPORTS_DIR"

# Set ownership and permissions
sudo chown -R $USER:www-data "$REPORTS_DIR"
sudo chmod -R 755 "$REPORTS_DIR"
sudo find "$REPORTS_DIR" -type f -exec chmod 644 {} +
sudo chmod g+s "$REPORTS_DIR"

echo "Permissions fixed for: $REPORTS_DIR"