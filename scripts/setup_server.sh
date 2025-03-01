#!/bin/bash

# =============================================
# Reading Tracker Server Setup Script
# This script automates the setup of a FastAPI application with Nginx reverse proxy
# Includes SSL configuration, monitoring, and maintenance tasks
# =============================================

# Color definitions for pretty output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Global variables
declare -A CONFIG
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# =============================================
# Utility Functions
# =============================================

log() { echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"; }
error() { echo -e "${RED}[ERROR] $1${NC}" >&2; }
warn() { echo -e "${YELLOW}[WARNING] $1${NC}"; }

check_success() {
    if [ $? -ne 0 ]; then
        error "$1 failed"
        error "Please check the error message above and try to resolve the issue"
        error "If you need help, consult the troubleshooting section in the documentation"
        return 1
    fi
    return 0
}

check_service() {
    if systemctl is-active --quiet $1; then
        log "$1 is running correctly"
        return 0
    else
        error "$1 failed to start"
        error "Checking service logs..."
        journalctl -u $1 --no-pager | tail -n 10
        return 1
    fi
}

prompt() {
    local prompt_msg=$1
    local default_value=$2
    local response

    if [ -n "$default_value" ]; then
        read -p "$(echo -e "${YELLOW}${prompt_msg} [${default_value}]: ${NC}")" response
        echo ${response:-$default_value}
    else
        read -p "$(echo -e "${YELLOW}${prompt_msg}: ${NC}")" response
        echo $response
    fi
}

confirm_step() {
    local step_name=$1
    echo -e "\n${YELLOW}Ready to execute: ${step_name}${NC}"
    read -p "Continue? (y/n): " response
    [[ "$response" =~ ^[Yy]$ ]]
}

# =============================================
# Test Functions
# =============================================

test_system_packages() {
    local packages=("nginx" "python3" "python3-pip" "python3-venv" "ufw" "certbot")
    local failed=0
    
    log "Testing system packages..."
    for pkg in "${packages[@]}"; do
        if ! dpkg -l | grep -q "^ii.*$pkg"; then
            error "Package $pkg is not installed"
            failed=1
        fi
    done
    
    return $failed
}

test_python_environment() {
    log "Testing Python environment..."
    if [ ! -d "${CONFIG[PROJECT_DIR]}/venv" ]; then
        error "Virtual environment not found"
        return 1
    fi
    if ! "${CONFIG[PROJECT_DIR]}/venv/bin/python" --version >/dev/null 2>&1; then
        error "Python interpreter not working in virtual environment"
        return 1
    fi
    return 0
}

test_nginx_config() {
    log "Testing Nginx configuration..."
    if ! nginx -t; then
        error "Nginx configuration test failed"
        return 1
    fi
    return 0
}

# =============================================
# Setup Functions
# =============================================

setup_preflight_checks() {
    # Description: Performs initial system checks and validates prerequisites
    # - Verifies root privileges
    # - Checks system resources
    # - Validates basic system requirements
    # Why: Ensures the system meets minimum requirements before proceeding
    
    log "Performing pre-flight checks..."
    
    if [ "$EUID" -ne 0 ]; then 
        error "This script must be run as root"
        echo "Please run with: sudo $0"
        return 1
    fi
    
    # Check system resources
    local min_memory=1024  # 1GB in MB
    local available_memory=$(free -m | awk '/^Mem:/{print $2}')
    if [ $available_memory -lt $min_memory ]; then
        error "Insufficient memory. Minimum required: ${min_memory}MB"
        return 1
    fi
    
    # Check disk space
    local min_space=5  # 5GB
    local available_space=$(df -BG / | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ $available_space -lt $min_space ]; then
        error "Insufficient disk space. Minimum required: ${min_space}GB"
        return 1
    fi
    
    return 0
}

setup_system_packages() {
    # Description: Updates system and installs required packages
    # - Updates package lists
    # - Upgrades existing packages
    # - Installs necessary software
    # Why: Ensures all required software is available and up to date
    
    log "Updating system packages..."
    apt update && apt upgrade -y
    check_success "System update" || return 1
    
    log "Installing required packages..."
    apt install nginx python3-pip python3-venv ufw certbot python3-certbot-nginx -y
    check_success "Package installation" || return 1
    
    test_system_packages
    return $?
}

collect_configuration() {
    # Description: Collects necessary configuration from user
    # - Project directory location
    # - Domain name or IP address
    # - Application port
    # - FastAPI application module path
    # Why: Gathers required information for setup process
    
    echo -e "\n${GREEN}=== Project Configuration ===${NC}"
    echo "Please provide the following information:"
    
    CONFIG[PROJECT_DIR]=$(prompt "Enter project directory" "/root/reading_tracker")
    CONFIG[DOMAIN]=$(prompt "Enter domain name (or IP address)")
    CONFIG[PORT]=$(prompt "Enter FastAPI port" "8001")
    CONFIG[APP_MODULE]=$(prompt "Enter FastAPI app module" "reading_list.api.app:app")
    
    # Validate inputs
    if [[ -z "${CONFIG[DOMAIN]}" ]]; then
        error "Domain name cannot be empty"
        return 1
    fi
    
    if ! [[ "${CONFIG[PORT]}" =~ ^[0-9]+$ ]]; then
        error "Port must be a number"
        return 1
    fi
    
    return 0
}

setup_python_environment() {
    # Description: Sets up Python virtual environment and installs dependencies
    # - Creates virtual environment
    # - Installs pip requirements
    # - Validates Python installation
    # Why: Isolates Python dependencies and ensures correct versions
    
    log "Setting up Python environment..."
    
    if [ ! -d "${CONFIG[PROJECT_DIR]}" ]; then
        error "Project directory ${CONFIG[PROJECT_DIR]} does not exist"
        return 1
    }
    
    cd "${CONFIG[PROJECT_DIR]}"
    
    # Create virtual environment
    log "Creating virtual environment..."
    python3 -m venv venv
    check_success "Virtual environment creation" || return 1
    
    # Activate virtual environment and install requirements
    log "Installing Python dependencies..."
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    check_success "Dependencies installation" || return 1
    
    # Install additional production dependencies
    pip install gunicorn uvicorn
    check_success "Production dependencies installation" || return 1
    
    deactivate
    return 0
}

setup_systemd_service() {
    # Description: Creates and enables systemd service for the FastAPI application
    # - Creates service file
    # - Sets up environment variables
    # - Enables and starts the service
    # Why: Ensures application runs as a system service with proper restart policies
    
    log "Setting up systemd service..."
    
    local service_name="reading-tracker"
    local service_file="/etc/systemd/system/${service_name}.service"
    
    # Create service file
    cat > "$service_file" << EOF
[Unit]
Description=Reading Tracker FastAPI Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=${CONFIG[PROJECT_DIR]}
Environment="PATH=${CONFIG[PROJECT_DIR]}/venv/bin"
EnvironmentFile=${CONFIG[PROJECT_DIR]}/config/.env
ExecStart=${CONFIG[PROJECT_DIR]}/venv/bin/gunicorn \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:${CONFIG[PORT]} \
    ${CONFIG[APP_MODULE]}
Restart=always

[Install]
WantedBy=multi-user.target
EOF
    
    # Set proper permissions
    chmod 644 "$service_file"
    
    # Reload systemd and enable service
    systemctl daemon-reload
    systemctl enable "$service_name"
    systemctl start "$service_name"
    
    # Check if service is running
    check_service "$service_name"
    return $?
}

setup_nginx() {
    # Description: Configures Nginx as reverse proxy
    # - Creates Nginx configuration
    # - Sets up SSL with Let's Encrypt
    # - Configures security headers
    # Why: Provides secure access to the application with proper SSL termination
    
    log "Setting up Nginx configuration..."
    
    local nginx_conf="/etc/nginx/sites-available/${CONFIG[DOMAIN]}"
    local nginx_enabled="/etc/nginx/sites-enabled/${CONFIG[DOMAIN]}"
    
    # Create Nginx configuration
    cat > "$nginx_conf" << EOF
server {
    listen 80;
    server_name ${CONFIG[DOMAIN]};

    location / {
        proxy_pass http://127.0.0.1:${CONFIG[PORT]};
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header Referrer-Policy "no-referrer-when-downgrade" always;
        add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    }

    # Additional security
    location ~ /\. {
        deny all;
    }
}
EOF
    
    # Enable site
    ln -sf "$nginx_conf" "$nginx_enabled"
    
    # Test and reload Nginx
    nginx -t && systemctl reload nginx
    return $?
}

setup_ssl() {
    # Description: Configures SSL using Let's Encrypt
    # - Obtains SSL certificate
    # - Configures automatic renewal
    # - Updates Nginx configuration
    # Why: Ensures secure HTTPS access to the application
    
    log "Setting up SSL with Let's Encrypt..."
    
    # Check if domain is reachable
    if ! ping -c 1 "${CONFIG[DOMAIN]}" &> /dev/null; then
        warn "Domain ${CONFIG[DOMAIN]} is not reachable"
        if ! confirm_step "Continue with SSL setup anyway?"; then
            return 1
        fi
    fi
    
    # Obtain SSL certificate
    certbot --nginx -d "${CONFIG[DOMAIN]}" --non-interactive --agree-tos --email "${CONFIG[EMAIL]}" --redirect
    check_success "SSL certificate acquisition" || return 1
    
    # Test automatic renewal
    certbot renew --dry-run
    check_success "SSL renewal test" || return 1
    
    return 0
}

setup_firewall() {
    # Description: Configures UFW firewall rules
    # - Allows HTTP/HTTPS traffic
    # - Allows SSH access
    # - Enables firewall
    # Why: Provides basic security by controlling incoming traffic
    
    log "Configuring firewall..."
    
    # Allow SSH (port 22)
    ufw allow ssh
    
    # Allow HTTP (port 80)
    ufw allow http
    
    # Allow HTTPS (port 443)
    ufw allow https
    
    # Enable firewall
    ufw --force enable
    
    # Check firewall status
    ufw status
    return $?
}

setup_monitoring() {
    # Description: Sets up basic system monitoring
    # - Configures log rotation
    # - Sets up application logging
    # - Creates monitoring scripts
    # Why: Ensures system health can be monitored and maintained
    
    log "Setting up monitoring..."
    
    # Create log directory
    mkdir -p "${CONFIG[PROJECT_DIR]}/logs"
    chown www-data:www-data "${CONFIG[PROJECT_DIR]}/logs"
    
    # Set up log rotation
    cat > "/etc/logrotate.d/reading-tracker" << EOF
${CONFIG[PROJECT_DIR]}/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload reading-tracker.service
    endscript
}
EOF
    
    # Create monitoring script
    cat > "${CONFIG[PROJECT_DIR]}/scripts/monitor.sh" << EOF
#!/bin/bash
# System monitoring script
systemctl status reading-tracker.service
journalctl -u reading-tracker.service --since "1 hour ago"
df -h
free -m
EOF
    
    chmod +x "${CONFIG[PROJECT_DIR]}/scripts/monitor.sh"
    return 0
}

main() {
    local step_functions=(
        "setup_preflight_checks"
        "setup_system_packages"
        "collect_configuration"
        "setup_python_environment"
        "setup_systemd_service"
        "setup_nginx"
        "setup_ssl"
        "setup_firewall"
        "setup_monitoring"
    )
    
    echo -e "\n${GREEN}=== Reading Tracker Server Setup ===${NC}"
    echo "This script will perform a complete server setup in multiple steps."
    echo "Each step can be confirmed before execution."
    
    for func in "${step_functions[@]}"; do
        echo -e "\n${GREEN}=== Executing: $func ===${NC}"
        
        if ! confirm_step "$func"; then
            warn "Skipping step: $func"
            continue
        fi
        
        if ! $func; then
            error "Step failed: $func"
            if ! confirm_step "Continue despite failure?"; then
                error "Setup aborted by user"
                exit 1
            fi
        fi
        
        # Run relevant tests after each step
        case $func in
            setup_system_packages)
                test_system_packages || warn "System package tests failed"
                ;;
            setup_python_environment)
                test_python_environment || warn "Python environment tests failed"
                ;;
            setup_nginx)
                test_nginx_config || warn "Nginx configuration tests failed"
                ;;
            setup_systemd_service)
                check_service "reading-tracker" || warn "Service check failed"
                ;;
        esac
    done
    
    log "Setup completed successfully!"
    log "Please check the following:"
    echo "1. Visit https://${CONFIG[DOMAIN]} to verify the application is running"
    echo "2. Check logs at ${CONFIG[PROJECT_DIR]}/logs/"
    echo "3. Monitor the service with: systemctl status reading-tracker"
    
    return 0
}

# Only run main if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
