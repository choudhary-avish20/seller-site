#!/usr/bin/env bash
# ==============================================================================
# deploy.sh — Production Deployment Script for OVH / Linux VPS
#
# Usage:
#   sudo ./deploy.sh setup    # One-time initial setup on a fresh VPS
#   sudo ./deploy.sh update   # Deploy updates after pulling new code
#   sudo ./deploy.sh status   # Check server & service status
#   sudo ./deploy.sh logs     # Tail application logs
#   sudo ./deploy.sh domain <yourdomain.com>  # Add custom domain + free SSL
# ==============================================================================

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
SERVICE_NAME="seller-site"
NGINX_CONF_PATH="/etc/nginx/sites-available/$SERVICE_NAME"
SYSTEMD_SERVICE_PATH="/etc/systemd/system/$SERVICE_NAME.service"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root or with sudo:"
        echo "  sudo ./deploy.sh $1"
        exit 1
    fi
}

get_public_ip() {
    local ip
    ip=$(curl -s -4 ifconfig.me 2>/dev/null || curl -s -4 icanhazip.com 2>/dev/null || hostname -I | awk '{print $1}')
    echo "$ip"
}

# ==============================================================================
# Setup command: Fresh VPS installation
# ==============================================================================
cmd_setup() {
    check_root "setup"
    log_info "Starting initial setup for Seller Site..."

    # 1. Detect public IP
    PUBLIC_IP=$(get_public_ip)
    if [[ -z "$PUBLIC_IP" ]]; then
        log_warn "Could not auto-detect public IP. Falling back to localhost."
        PUBLIC_IP="127.0.0.1"
    else
        log_info "Detected server public IP: $PUBLIC_IP"
    fi

    # 2. System updates & package installation
    log_info "Updating system packages & installing dependencies..."
    apt-get update -y
    apt-get install -y python3 python3-venv python3-pip nginx ufw curl git

    # 3. Setup Python virtual environment
    log_info "Setting up Python virtual environment in $BACKEND_DIR/venv..."
    if [[ ! -d "$BACKEND_DIR/venv" ]]; then
        python3 -m venv "$BACKEND_DIR/venv"
    fi
    "$BACKEND_DIR/venv/bin/pip" install --upgrade pip
    log_info "Installing Python backend requirements..."
    "$BACKEND_DIR/venv/bin/pip" install -r "$BACKEND_DIR/requirements.txt"

    # 4. Create .env if not present
    if [[ ! -f "$BACKEND_DIR/.env" ]]; then
        log_info "Generating $BACKEND_DIR/.env configuration..."
        SECRET_KEY=$("$BACKEND_DIR/venv/bin/python" -c "import secrets; print(secrets.token_hex(32))")
        
        cat <<EOF > "$BACKEND_DIR/.env"
ENV=production
DEBUG=false
SECRET_KEY=$SECRET_KEY
DATABASE_URL=sqlite:///./wholesale.db

# Access URLs (Serving via IP by default)
BACKEND_BASE_URL=http://$PUBLIC_IP
FRONTEND_BASE_URL=http://$PUBLIC_IP
CORS_ORIGINS=["http://$PUBLIC_IP"]

ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
EOF
        log_success "Created backend/.env with production defaults."
    else
        log_info "Existing backend/.env found. Keeping current settings."
    fi

    # 5. Run Alembic database migrations
    log_info "Running database migrations..."
    (cd "$BACKEND_DIR" && "$BACKEND_DIR/venv/bin/alembic" upgrade head)

    # 6. Seed Admin Account if not exists
    log_info "Ensuring admin account exists..."
    (cd "$BACKEND_DIR" && "$BACKEND_DIR/venv/bin/python" seed_admin.py)

    # 7. Configure systemd service
    log_info "Configuring systemd service ($SERVICE_NAME)..."
    cat <<EOF > "$SYSTEMD_SERVICE_PATH"
[Unit]
Description=Seller Site FastAPI Backend & Frontend
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$BACKEND_DIR
Environment="PATH=$BACKEND_DIR/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=$BACKEND_DIR/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable "$SERVICE_NAME"
    systemctl restart "$SERVICE_NAME"
    log_success "systemd service $SERVICE_NAME is active and enabled."

    # 8. Configure Nginx
    log_info "Configuring Nginx reverse proxy..."
    cat <<EOF > "$NGINX_CONF_PATH"
server {
    listen 80;
    server_name _ $PUBLIC_IP;

    client_max_body_size 25M;

    # Gzip Compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 60s;
        proxy_connect_timeout 60s;
    }
}
EOF

    # Link and reload Nginx
    ln -sf "$NGINX_CONF_PATH" /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    nginx -t
    systemctl restart nginx
    log_success "Nginx configured and restarted."

    # 9. Configure UFW Firewall
    log_info "Configuring UFW firewall rules..."
    ufw allow OpenSSH || ufw allow 22/tcp
    ufw allow 'Nginx HTTP' || ufw allow 80/tcp
    ufw allow 'Nginx HTTPS' || ufw allow 443/tcp
    # Enable UFW non-interactively
    echo "y" | ufw enable || true
    log_success "Firewall configured (SSH, Port 80, Port 443 allowed)."

    # 10. Health check
    log_info "Verifying deployment..."
    sleep 2
    local HEALTH
    HEALTH=$(curl -s http://127.0.0.1:8000/api/v1/health 2>/dev/null || echo "FAILED")
    
    echo ""
    echo "=================================================================="
    if [[ "$HEALTH" =~ "ok" ]]; then
        log_success "DEPLOYMENT SUCCESSFUL!"
    else
        log_warn "Service started but health check returned: $HEALTH"
        echo "Check logs with: sudo ./deploy.sh logs"
    fi
    echo "=================================================================="
    echo -e "Storefront URL:      ${GREEN}http://$PUBLIC_IP${NC}"
    echo -e "Admin Login:         ${GREEN}http://$PUBLIC_IP/admin-login.html${NC}"
    echo -e "API Docs:            ${GREEN}http://$PUBLIC_IP/docs${NC}"
    echo ""
    echo "Default Admin Credentials:"
    echo "  Email:    seller@example.com"
    echo "  Password: seller123"
    echo "  (Please log in and change your password in Settings!)"
    echo "=================================================================="
}

# ==============================================================================
# Update command: Pull git updates, migrate, and restart
# ==============================================================================
cmd_update() {
    check_root "update"
    log_info "Updating Seller Site application..."

    # 1. Pull latest code if in a git repository
    if [[ -d "$SCRIPT_DIR/.git" ]]; then
        log_info "Pulling latest changes from git repository..."
        cd "$SCRIPT_DIR"
        git pull || log_warn "git pull encountered a conflict or warning. Continuing..."
    fi

    # 2. Update Python dependencies
    log_info "Checking & updating Python packages..."
    "$BACKEND_DIR/venv/bin/pip" install -r "$BACKEND_DIR/requirements.txt"

    # 3. Run database migrations
    log_info "Applying database migrations..."
    (cd "$BACKEND_DIR" && "$BACKEND_DIR/venv/bin/alembic" upgrade head)

    # 4. Restart services
    log_info "Restarting $SERVICE_NAME and Nginx..."
    systemctl restart "$SERVICE_NAME"
    systemctl restart nginx

    # 5. Check health
    sleep 2
    local HEALTH
    HEALTH=$(curl -s http://127.0.0.1:8000/api/v1/health 2>/dev/null || echo "FAILED")
    if [[ "$HEALTH" =~ "ok" ]]; then
        log_success "Update complete! Health check: $HEALTH"
    else
        log_warn "Update finished, but health check returned: $HEALTH"
        echo "Run: sudo ./deploy.sh logs"
    fi
}

# ==============================================================================
# Status command: Check services status
# ==============================================================================
cmd_status() {
    echo "── Systemd Service Status ─────────────────────────────"
    systemctl status "$SERVICE_NAME" --no-pager || true
    echo ""
    echo "── Nginx Status ──────────────────────────────────────"
    systemctl status nginx --no-pager || true
    echo ""
    echo "── Health Endpoint Check ─────────────────────────────"
    curl -i http://127.0.0.1:8000/api/v1/health 2>/dev/null || echo "Unable to connect to local port 8000"
    echo ""
}

# ==============================================================================
# Logs command: Tail systemd logs
# ==============================================================================
cmd_logs() {
    journalctl -u "$SERVICE_NAME" -f -n 50
}

# ==============================================================================
# Domain & SSL command: Attach custom domain + Let's Encrypt SSL
# ==============================================================================
cmd_domain() {
    check_root "domain"
    local DOMAIN="$1"

    if [[ -z "$DOMAIN" ]]; then
        log_error "Please specify a domain name. Example:"
        echo "  sudo ./deploy.sh domain yourdomain.com"
        exit 1
    fi

    log_info "Setting up custom domain: $DOMAIN and SSL via Let's Encrypt..."

    # Install certbot if missing
    apt-get update -y
    apt-get install -y certbot python3-certbot-nginx

    # Update Nginx server_name
    cat <<EOF > "$NGINX_CONF_PATH"
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

    client_max_body_size 25M;

    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 60s;
        proxy_connect_timeout 60s;
    }
}
EOF

    nginx -t
    systemctl restart nginx

    # Obtain Let's Encrypt Certificate
    log_info "Requesting SSL certificate from Let's Encrypt..."
    certbot --nginx -d "$DOMAIN" -d "www.$DOMAIN" --non-interactive --agree-tos --register-unsafely-without-email --redirect || {
        log_warn "Certbot with www failed or was rejected. Trying domain without www..."
        certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --register-unsafely-without-email --redirect
    }

    # Update backend/.env URLs to HTTPS
    if [[ -f "$BACKEND_DIR/.env" ]]; then
        log_info "Updating backend/.env URLs with HTTPS domain..."
        sed -i "s|BACKEND_BASE_URL=.*|BACKEND_BASE_URL=https://$DOMAIN|g" "$BACKEND_DIR/.env"
        sed -i "s|FRONTEND_BASE_URL=.*|FRONTEND_BASE_URL=https://$DOMAIN|g" "$BACKEND_DIR/.env"
        sed -i "s|CORS_ORIGINS=.*|CORS_ORIGINS=[\"https://$DOMAIN\"]|g" "$BACKEND_DIR/.env"
        systemctl restart "$SERVICE_NAME"
    fi

    log_success "Domain and SSL setup complete! Visit: https://$DOMAIN"
}

# ==============================================================================
# Main router
# ==============================================================================
case "${1:-}" in
    setup)
        cmd_setup
        ;;
    update)
        cmd_update
        ;;
    status)
        cmd_status
        ;;
    logs)
        cmd_logs
        ;;
    domain)
        cmd_domain "${2:-}"
        ;;
    *)
        echo "Seller Site Deployment Tool"
        echo ""
        echo "Usage:"
        echo "  sudo ./deploy.sh setup              Initial setup on a fresh VPS (installs Nginx, Python, systemd, firewall)"
        echo "  sudo ./deploy.sh update             Apply code/migration updates and restart"
        echo "  sudo ./deploy.sh status             Check systemd service and Nginx status"
        echo "  sudo ./deploy.sh logs               Follow application live logs"
        echo "  sudo ./deploy.sh domain <domain>    Set up a custom domain with Let's Encrypt HTTPS"
        echo ""
        exit 1
        ;;
esac
