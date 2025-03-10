#!/bin/bash

# Create symbolic link for systemd service
sudo ln -sf "$(pwd)/config/systemd/reading-tracker.service" /etc/systemd/system/reading-tracker.service

# Reload systemd to recognize changes
sudo systemctl daemon-reload

echo "Systemd service configured. Use 'sudo systemctl start reading-tracker' to start the service."