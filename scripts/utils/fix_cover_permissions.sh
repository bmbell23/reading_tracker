#!/bin/bash

# Get the project root directory (where the script is located)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
COVERS_DIR="$PROJECT_ROOT/assets/book_covers"

# Create directory if it doesn't exist
mkdir -p "$COVERS_DIR"

# Ensure the covers directory exists and has correct permissions
sudo chmod 755 "$COVERS_DIR"
sudo chown -R $USER:www-data "$COVERS_DIR"

# Fix permissions for all cover images
find "$COVERS_DIR" -type f -name "*.jpg" -exec sudo chmod 644 {} \;
find "$COVERS_DIR" -type f -name "*.jpeg" -exec sudo chmod 644 {} \;
find "$COVERS_DIR" -type f -name "*.png" -exec sudo chmod 644 {} \;
find "$COVERS_DIR" -type f -name "*.webp" -exec sudo chmod 644 {} \;

echo "Cover image permissions fixed"
