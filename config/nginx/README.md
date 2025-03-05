# NGINX Configuration

This directory contains all NGINX configurations for the Reading Tracker project.

## Files
- `nginx.conf` - Main NGINX configuration
- `reading-tracker.conf` - Site-specific configuration

## Setup
Run the following commands to set up symbolic links:

```bash
# Main config
sudo ln -sf ~/projects/reading_tracker/config/nginx/nginx.conf /etc/nginx/nginx.conf

# Site config
sudo ln -sf ~/projects/reading_tracker/config/nginx/reading-tracker.conf /etc/nginx/sites-available/reading-tracker.conf
sudo ln -sf /etc/nginx/sites-available/reading-tracker.conf /etc/nginx/sites-enabled/reading-tracker.conf
```