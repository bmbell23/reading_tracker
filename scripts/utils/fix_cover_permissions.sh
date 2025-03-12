#!/bin/bash

COVERS_DIR="assets/book_covers"

# Ensure the covers directory exists and has correct permissions
sudo chmod 755 "$COVERS_DIR"
sudo chown -R $USER:www-data "$COVERS_DIR"

# Fix permissions for all cover images
find "$COVERS_DIR" -type f -name "*.jpg" -exec sudo chmod 644 {} \;
find "$COVERS_DIR" -type f -name "*.jpeg" -exec sudo chmod 644 {} \;
find "$COVERS_DIR" -type f -name "*.png" -exec sudo chmod 644 {} \;
find "$COVERS_DIR" -type f -name "*.webp" -exec sudo chmod 644 {} \;

echo "Cover image permissions fixed"