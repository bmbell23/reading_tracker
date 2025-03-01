# Nginx Server Setup Guide

## Core Concepts

### FastAPI
FastAPI is a modern, fast web framework for building APIs with Python. It's used in this project to:
- Create a web server that handles HTTP requests
- Serve our application's endpoints
- Handle API routing and request processing
- Provide automatic API documentation
- Manage data validation and serialization

### Systemd
Systemd is Linux's system and service manager. We use it to:
- Manage our application as a system service
- Automatically start our application on system boot
- Restart the service if it crashes
- Handle service dependencies
- Provide logging and status monitoring

### ExecStart
ExecStart is a systemd directive that specifies the exact command to run when starting a service. In our configuration:
- It defines how to launch our FastAPI application
- Specifies the Python interpreter path
- Sets the application host and port
- Configures any necessary environment variables

### Firewall (UFW)
A firewall controls incoming and outgoing network traffic. We use Ubuntu's UFW (Uncomplicated Firewall) to:
- Block unauthorized access attempts
- Allow only specific ports (80 for HTTP, 443 for HTTPS)
- Protect against network-based attacks
- Control which services are accessible from the internet

### Security Headers
Security headers are HTTP response headers that protect against common web vulnerabilities:
- `X-Frame-Options`: Prevents clickjacking attacks
- `X-XSS-Protection`: Blocks cross-site scripting (XSS) attacks
- `X-Content-Type-Options`: Prevents MIME-type sniffing
- `Referrer-Policy`: Controls how much referrer information to share

### Rate Limiting
Rate limiting restricts how many requests a client can make in a given timeframe:
- Prevents abuse and DoS attacks
- Ensures fair resource usage
- Protects server resources
- Blocks brute force attempts

Example in our config:
```nginx
# Allows 1 request per second with a burst of 5 requests
limit_req_zone $binary_remote_addr zone=one:10m rate=1r/s;
```

### Domain Names and DNS
Domain names are human-readable addresses for websites. Common components include:

#### @ and WWW Records
- `@` record: Represents the root domain (example.com)
- `www` record: Subdomain for web traffic (www.example.com)
- Both typically point to the same server but serve different purposes:
  ```
  @ (root)  → example.com
  www       → www.example.com
  ```

### HTTP vs HTTPS
- **HTTP** (Hypertext Transfer Protocol):
  - Basic protocol for web communication
  - Data sent in plain text
  - Vulnerable to interception
  - Uses port 80

- **HTTPS** (HTTP Secure):
  - Encrypted version of HTTP
  - Uses SSL/TLS for security
  - Protects sensitive data
  - Uses port 443
  - Required for modern web applications

### SSL Certificates
SSL (Secure Sockets Layer) certificates provide:
- Encrypted connections between server and clients
- Website identity verification
- Trust indicators in browsers (padlock icon)

#### Installation Options

1. **Let's Encrypt (Recommended for Production)**:
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com
```

2. **Self-Signed (Development Only)**:
```bash
# Generate certificate
sudo openssl req -x509 -nodes -days 365 \
    -newkey rsa:2048 \
    -keyout /etc/ssl/private/nginx-selfsigned.key \
    -out /etc/ssl/certs/nginx-selfsigned.crt
```

### Nginx Configuration Structure

#### /etc/nginx Directory
The Nginx configuration hierarchy:

```
/etc/nginx/
├── nginx.conf           # Main configuration file
├── sites-available/     # Available site configurations
│   └── reading-tracker.conf
└── sites-enabled/       # Enabled site configurations
    └── reading-tracker.conf -> ../sites-available/reading-tracker.conf
```

- **sites-available/**: Stores all site configurations
- **sites-enabled/**: Contains symbolic links to active configurations
- Only configurations linked in sites-enabled are active
- Use symbolic links to enable/disable sites without deleting configs

#### Configuration Files

1. **reading-tracker.conf**:
```nginx
# /etc/nginx/sites-available/reading-tracker.conf
server {
    listen 80;
    server_name yourdomain.com;
    
    # Site-specific settings
    location / {
        proxy_pass http://localhost:8001;
        # ... other proxy settings
    }
}
```

### Systemd Configuration

#### Service Files Location
```
/etc/systemd/system/
└── reading-tracker.service
```

#### Service File Anatomy
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

Key sections:
- **[Unit]**: Dependencies and description
- **[Service]**: How to run the service
- **[Install]**: When to start the service

#### Service Management
```bash
# Reload systemd after changes
sudo systemctl daemon-reload

# Enable auto-start
sudo systemctl enable reading-tracker

# Start/stop/restart
sudo systemctl start reading-tracker
sudo systemctl stop reading-tracker
sudo systemctl restart reading-tracker

# Check status and logs
sudo systemctl status reading-tracker
sudo journalctl -u reading-tracker -f
```

## Overview
This document details the Nginx server configuration for the Reading Tracker application.

## Complete Setup Guide

### 1. Initial Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install nginx python3-pip python3-venv -y
```

### 2. Application Setup

```bash
# Create project directory
mkdir -p /root/reading_tracker
cd /root/reading_tracker

# Clone repository (replace with your repo URL)
git clone [your-repository-url] .

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. FastAPI Application Setup

1. **Create systemd service**:
```bash
sudo nano /etc/systemd/system/reading-tracker.service
```

2. **Add service configuration**:
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

3. **Enable and start service**:
```bash
sudo systemctl daemon-reload
sudo systemctl enable reading-tracker
sudo systemctl start reading-tracker
```

### 4. Nginx Configuration

1. **Create Nginx config**:
```bash
sudo nano /etc/nginx/sites-available/reading-tracker.conf
```

2. **Add configuration**:
```nginx
server {
    listen 80;
    server_name 5.78.41.92;  # Replace with your IP or domain
    
    location / {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    error_log /var/log/nginx/reading-tracker-error.log debug;
    access_log /var/log/nginx/reading-tracker-access.log combined;
}
```

3. **Enable the site**:
```bash
sudo ln -s /etc/nginx/sites-available/reading-tracker.conf /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default  # Remove default site
sudo nginx -t  # Test configuration
sudo systemctl restart nginx
```

### 5. Security Setup

```bash
# Configure firewall
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable

# Add security headers to Nginx config
sudo nano /etc/nginx/sites-available/reading-tracker.conf
# Add inside server block:
add_header X-Frame-Options "SAMEORIGIN";
add_header X-XSS-Protection "1; mode=block";
add_header X-Content-Type-Options "nosniff";
add_header Referrer-Policy "strict-origin-source";

# Add rate limiting to http block in nginx.conf
sudo nano /etc/nginx/nginx.conf
# Add:
limit_req_zone $binary_remote_addr zone=one:10m rate=1r/s;
```

### 6. Monitoring Setup

1. **Create log directories**:
```bash
sudo mkdir -p /var/log/nginx
sudo touch /var/log/nginx/reading-tracker-error.log
sudo touch /var/log/nginx/reading-tracker-access.log
```

2. **Add monitoring endpoint**:
```nginx
# Add to nginx.conf
location /nginx_status {
    stub_status on;
    allow 127.0.0.1;
    deny all;
}
```

### 7. Maintenance Setup

1. **Add maintenance cron jobs**:
```bash
crontab -e

# Add:
0 0 * * * systemctl status nginx >/dev/null 2>&1 || systemctl restart nginx
0 0 * * 0 /usr/sbin/logrotate /etc/logrotate.d/nginx
0 */6 * * * df -h | grep '/dev/sda1' | awk '{print $5}' | grep -q '^9[0-9]' && systemctl restart nginx
0 0 * * 0 cp /etc/nginx/sites-available/reading-tracker.conf /root/backups/nginx-$(date +\%Y\%m\%d).conf
```

### 8. Verification Steps

```bash
# Check FastAPI service
sudo systemctl status reading-tracker

# Check Nginx status
sudo systemctl status nginx

# View logs
tail -f /var/log/nginx/reading-tracker-error.log
tail -f /var/log/nginx/reading-tracker-access.log

# Test the application
curl http://localhost:8001
curl http://5.78.41.92  # Replace with your IP
```

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
