# Nginx Server Setup Guide

## Overview
This document details the Nginx server configuration for the Reading Tracker application.

## Architecture
```
Client Request → Nginx (Port 80) → FastAPI (Port 8001)
```

## Current Configuration
The server currently runs on IP 5.78.41.92 and proxies requests to a FastAPI application running on port 8001.

## Domain Name Options

### Free Domain Options
1. **Cloudflare Tunnel**:
   - Free
   - Includes SSL
   - Setup:
     ```bash
     # Install cloudflared
     curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -o cloudflared.deb
     sudo dpkg -i cloudflared.deb
     
     # Login and create tunnel
     cloudflared tunnel login
     cloudflared tunnel create reading-tracker
     ```

2. **No-IP**:
   - Free subdomain (e.g., yourapp.noip.com)
   - Requires renewal every 30 days
   - Setup at: https://www.noip.com/

3. **Freenom**:
   - Free TLD domains (.tk, .ml, etc.)
   - Renewal required yearly
   - Less reliable than other options

## SSL Certificate Setup

### Option 1: Let's Encrypt (Recommended)
```bash
# Install certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal cron job (adds automatically)
# Runs twice daily
# 0 */12 * * * /usr/bin/certbot renew --quiet
```

### Option 2: Self-Signed (Development Only)
```bash
# Generate self-signed certificate
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/private/nginx-selfsigned.key \
    -out /etc/ssl/certs/nginx-selfsigned.crt
```

## DNS Configuration

### Using Cloudflare
1. Sign up for free Cloudflare account
2. Add your domain
3. Update nameservers at your registrar
4. Add DNS records:
   ```
   Type  Name     Content          TTL
   A     @        5.78.41.92      Auto
   CNAME www      yourdomain.com   Auto
   ```

### Using No-IP
1. Create free account
2. Choose subdomain
3. Point to your IP
4. Install DUC (Dynamic Update Client):
   ```bash
   # Install No-IP DUC
   cd /usr/local/src/
   wget http://www.noip.com/client/linux/noip-duc-linux.tar.gz
   tar xf noip-duc-linux.tar.gz
   cd noip-2.1.9-1/
   make install
   ```

## Server Management

### Keep Server Running

#### Option 1: Using Systemd (Recommended)

1. **Create the service file**:
```bash
sudo nano /etc/systemd/system/reading-tracker.service
```

2. **Add this configuration**:
```ini
[Unit]
Description=Reading Tracker FastAPI Server
After=network.target

[Service]
User=root
WorkingDirectory=/root/reading_tracker
Environment="PATH=/root/reading_tracker/venv/bin"
ExecStart=/root/reading_tracker/venv/bin/uvicorn reading_list.api.app:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

3. **Setup and control commands**:
```bash
# Reload systemd to recognize new service
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable reading-tracker

# Start the service
sudo systemctl start reading-tracker

# Check status
sudo systemctl status reading-tracker

# Other useful commands:
sudo systemctl stop reading-tracker      # Stop the service
sudo systemctl restart reading-tracker   # Restart the service
sudo journalctl -u reading-tracker -f    # View logs in real-time
```

4. **Making changes to the service**:
```bash
# Edit the service file
sudo nano /etc/systemd/system/reading-tracker.service

# Reload systemd
sudo systemctl daemon-reload

# Restart the service
sudo systemctl restart reading-tracker
```

#### Option 2: Using Screen
```bash
screen -S reading-tracker
python -m scripts.server.run_reports_server
# Press Ctrl+A, then D to detach
```

### Maintenance Cron Jobs

Add these to your crontab (`crontab -e`):

```bash
# Check Nginx status daily
0 0 * * * systemctl status nginx >/dev/null 2>&1 || systemctl restart nginx

# Rotate Nginx logs weekly
0 0 * * 0 /usr/sbin/logrotate /etc/logrotate.d/nginx

# Monitor disk space
0 */6 * * * df -h | grep '/dev/sda1' | awk '{print $5}' | grep -q '^9[0-9]' && systemctl restart nginx

# Backup Nginx config weekly
0 0 * * 0 cp /etc/nginx/sites-available/reading-tracker.conf /path/to/backups/nginx-$(date +\%Y\%m\%d).conf
```

### Monitoring

1. **Basic Status Check**:
   ```bash
   # Add to nginx.conf
   location /nginx_status {
       stub_status on;
       allow 127.0.0.1;
       deny all;
   }
   ```

2. **Log Monitoring**:
   ```bash
   # Watch access log
   tail -f /var/log/nginx/reading-tracker-access.log

   # Watch error log
   tail -f /var/log/nginx/reading-tracker-error.log
   ```

## Security Recommendations

1. **Firewall Setup**:
   ```bash
   sudo ufw allow 80
   sudo ufw allow 443
   sudo ufw enable
   ```

2. **Security Headers**:
   ```nginx
   # Add to server block
   add_header X-Frame-Options "SAMEORIGIN";
   add_header X-XSS-Protection "1; mode=block";
   add_header X-Content-Type-Options "nosniff";
   add_header Referrer-Policy "strict-origin-source";
   ```

3. **Rate Limiting**:
   ```nginx
   # Add to http block
   limit_req_zone $binary_remote_addr zone=one:10m rate=1r/s;

   # Add to location block
   limit_req zone=one burst=5;
   ```

## Troubleshooting

1. **Check Nginx Status**:
   ```bash
   sudo systemctl status nginx
   ```

2. **Test Configuration**:
   ```bash
   sudo nginx -t
   ```

3. **Check Logs**:
   ```bash
   sudo tail -f /var/log/nginx/error.log
   ```

4. **Common Issues**:
   - Port 80 already in use: `sudo lsof -i :80`
   - Permission denied: Check file permissions
   - 502 Bad Gateway: FastAPI server not running
