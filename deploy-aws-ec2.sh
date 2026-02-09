#!/bin/bash
################################################################################
# MSIL MCP Server Complete AWS EC2 Deployment Script
# Deploys: FastAPI Backend + Admin UI + Chat UI + Nginx on t4g.nano
# Target: Amazon Linux 2 on EC2 t4g.nano with EBS volume attached
# Total runtime: ~15-20 minutes (first time)
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_REPO="https://github.com/Tannu-Git/msil_mcp.git"
APP_BRANCH="main"
APP_HOME="/opt/msil_mcp"
DATA_DIR="/data"
DOCKER_COMPOSE_FILE="$APP_HOME/docker-compose-aws.yml"
NGINX_CONF="/etc/nginx/conf.d/msil.conf"
SSL_CERT_DIR="/etc/ssl/certs/msil"

################################################################################
# Logging and Error Handling
################################################################################
log() { echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"; }
success() { echo -e "${GREEN}[✓]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; exit 1; }
warning() { echo -e "${YELLOW}[!]${NC} $1"; }

################################################################################
# 1. SYSTEM SETUP
################################################################################
log "=== Step 1: System Setup ==="

# Update system
log "Updating system packages..."
sudo yum update -y > /dev/null 2>&1 || error "Failed to update packages"
success "System updated"

# Install dependencies
log "Installing dependencies..."
sudo yum install -y \
    git \
    curl \
    wget \
    htop \
    nano \
    jq \
    ca-certificates \
    > /dev/null 2>&1 || error "Failed to install dependencies"
success "Dependencies installed"

# Create app directories
log "Creating directories..."
sudo mkdir -p "$APP_HOME" "$DATA_DIR"/{app,db,logs}
sudo chown -R ec2-user:ec2-user "$APP_HOME" "$DATA_DIR"
success "Directories created"

################################################################################
# 2. DOCKER INSTALLATION
################################################################################
log "=== Step 2: Docker Setup ==="

# Check if Docker is already installed
if command -v docker &> /dev/null; then
    success "Docker already installed"
else
    log "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh > /dev/null 2>&1
    rm get-docker.sh
    
    # Add current user to docker group
    sudo usermod -aG docker ec2-user
    newgrp docker
    success "Docker installed"
fi

# Install Docker Compose
log "Installing Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
    -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
success "Docker Compose installed: $(docker-compose --version)"

# Start Docker daemon
log "Starting Docker daemon..."
sudo systemctl start docker
sudo systemctl enable docker
success "Docker daemon running"

################################################################################
# 3. CLONE AND BUILD APPLICATION
################################################################################
log "=== Step 3: Cloning Application ==="

cd $APP_HOME

if [ -d "$APP_HOME/.git" ]; then
    log "Repository already exists, pulling latest..."
    git fetch origin
    git checkout $APP_BRANCH
    git pull origin $APP_BRANCH
else
    log "Cloning repository..."
    git clone --branch $APP_BRANCH $APP_REPO .
fi

success "Application code ready"

# Build frontend applications (builds static dist folders)
log "Building Admin UI..."
cd $APP_HOME/admin-ui
npm install > /dev/null 2>&1 || error "Failed to install admin-ui dependencies"
npm run build > /dev/null 2>&1 || error "Failed to build admin-ui"
success "Admin UI built"

log "Building Chat UI..."
cd $APP_HOME/chat-ui
npm install > /dev/null 2>&1 || error "Failed to install chat-ui dependencies"
npm run build > /dev/null 2>&1 || error "Failed to build chat-ui"
success "Chat UI built"

################################################################################
# 4. CREATE DOCKER COMPOSE CONFIGURATION
################################################################################
log "=== Step 4: Docker Compose Configuration ==="

cat > "$DOCKER_COMPOSE_FILE" << 'EOF'
version: '3.8'

services:
  # FastAPI Backend Service
  backend:
    build:
      context: ./mcp-server
      dockerfile: Dockerfile
    container_name: msil-backend
    ports:
      - "8000:8000"
    environment:
      # Application
      APP_NAME: "MSIL MCP Server"
      APP_VERSION: "1.0.0"
      DEBUG: "false"
      ENVIRONMENT: "production"
      
      # Server
      HOST: "0.0.0.0"
      PORT: "8000"
      
      # Database - SQLite on persistent EBS volume
      DATABASE_URL: "sqlite+aiosqlite:////data/db/msil_mcp.db"
      
      # API Gateway
      API_GATEWAY_MODE: "mock"
      MOCK_API_BASE_URL: "http://localhost:8080"
      
      # Security
      API_KEY: "msil-mcp-dev-key-2026"
      CORS_ORIGINS: "*"
      
      # OpenAI (set via .env)
      OPENAI_API_KEY: "${OPENAI_API_KEY:-}"
      OPENAI_MODEL: "gpt-4-turbo-preview"
      
      # Auth
      JWT_SECRET: "msil-mcp-jwt-secret-key-change-in-production-2026"
      JWT_ALGORITHM: "HS256"
      JWT_ACCESS_TOKEN_EXPIRE_MINUTES: "60"
      
      # Demo Mode
      DEMO_MODE: "true"
      DEMO_MODE_AUTH_BYPASS: "true"
      
      # Logging
      LOG_LEVEL: "INFO"
    
    volumes:
      - /data/db:/data/db
      - /data/logs:/app/logs
    
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
  
  # Nginx Reverse Proxy & Static File Server
  nginx:
    image: nginx:alpine
    container_name: msil-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /etc/nginx/conf.d/msil.conf:/etc/nginx/conf.d/default.conf:ro
      - /etc/ssl/certs/msil:/etc/ssl/certs/msil:ro
      - ./admin-ui/dist:/usr/share/nginx/html/admin:ro
      - ./chat-ui/dist:/usr/share/nginx/html/chat:ro
      - /data/logs/nginx:/var/log/nginx
    depends_on:
      - backend
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  msil-data:
EOF

success "Docker Compose configuration created"

################################################################################
# 5. NGINX REVERSE PROXY CONFIGURATION
################################################################################
log "=== Step 5: Nginx Configuration ==="

sudo mkdir -p "$SSL_CERT_DIR"

cat > /tmp/msil-nginx.conf << 'EOF'
# Upstream backend
upstream backend {
    server backend:8000;
    keepalive 32;
}

# HTTP to HTTPS redirect (only if SSL cert exists)
server {
    listen 80;
    server_name _;
    
    # Health check endpoint (no redirect)
    location /health {
        access_log off;
        return 200 "OK\n";
    }
    
    # Redirect everything else to HTTPS
    location / {
        return 301 https://$host$request_uri;
    }
}

# HTTPS Server (with self-signed cert initially)
server {
    listen 443 ssl http2 default_server;
    server_name _;
    
    # SSL Configuration (self-signed cert)
    ssl_certificate /etc/ssl/certs/msil/cert.pem;
    ssl_certificate_key /etc/ssl/certs/msil/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Gzip compression
    gzip on;
    gzip_types text/plain text/css text/javascript application/json application/javascript;
    gzip_min_length 1000;
    
    # Admin UI - SPA routing
    location /admin {
        alias /usr/share/nginx/html/admin;
        try_files $uri $uri/ /admin/index.html;
        add_header Cache-Control "public, max-age=3600";
    }
    
    # Chat UI - SPA routing
    location /chat {
        alias /usr/share/nginx/html/chat;
        try_files $uri $uri/ /chat/index.html;
        add_header Cache-Control "public, max-age=3600";
    }
    
    # API proxy to backend
    location /api {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        
        # Headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $server_name;
        proxy_set_header X-API-Key "msil-mcp-dev-key-2026";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Buffering
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://backend/health;
        access_log off;
    }
    
    # Default - Admin UI
    location / {
        alias /usr/share/nginx/html/admin/;
        try_files $uri $uri/ /index.html;
        add_header Cache-Control "public, max-age=3600";
    }
}
EOF

sudo cp /tmp/msil-nginx.conf "$NGINX_CONF"
sudo chown root:root "$NGINX_CONF"
success "Nginx configuration installed"

################################################################################
# 6. GENERATE SELF-SIGNED SSL CERTIFICATE
################################################################################
log "=== Step 6: SSL Certificate Generation ==="

sudo mkdir -p "$SSL_CERT_DIR"

if [ ! -f "$SSL_CERT_DIR/cert.pem" ]; then
    log "Generating self-signed SSL certificate..."
    sudo openssl req -x509 -newkey rsa:2048 -keyout "$SSL_CERT_DIR/key.pem" -out "$SSL_CERT_DIR/cert.pem" \
        -days 365 -nodes -subj "/CN=localhost" > /dev/null 2>&1
    success "Self-signed certificate created (valid for 1 year)"
    warning "For production: Replace with ACM certificate"
else
    success "SSL certificate already exists"
fi

################################################################################
# 7. CREATE SYSTEMD SERVICE
################################################################################
log "=== Step 7: Systemd Service Setup ==="

cat > /tmp/msil-mcp.service << EOF
[Unit]
Description=MSIL MCP Server
After=docker.service
Requires=docker.service

[Service]
Type=simple
User=ec2-user
WorkingDirectory=$APP_HOME
ExecStart=/usr/local/bin/docker-compose -f $DOCKER_COMPOSE_FILE up
ExecStop=/usr/local/bin/docker-compose -f $DOCKER_COMPOSE_FILE down
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo cp /tmp/msil-mcp.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable msil-mcp.service
success "Systemd service created"

################################################################################
# 8. START SERVICES
################################################################################
log "=== Step 8: Starting Services ==="

cd "$APP_HOME"

log "Building Docker images (this may take 5-10 minutes on t4g.nano)..."
docker-compose -f "$DOCKER_COMPOSE_FILE" build 2>&1 | tail -20 || error "Docker build failed"
success "Docker images built"

log "Starting services via docker-compose..."
docker-compose -f "$DOCKER_COMPOSE_FILE" up -d || error "Failed to start services"
success "Services started"

# Wait for services to be healthy
log "Waiting for services to become healthy (max 60 seconds)..."
for i in {1..30}; do
    if curl -sk https://localhost/health > /dev/null 2>&1; then
        success "Services are healthy"
        break
    fi
    if [ $i -eq 30 ]; then
        error "Services did not become healthy in time"
    fi
    sleep 2
done

################################################################################
# 9. DISPLAY INFORMATION
################################################################################
log "=== Step 9: Summary ==="

INSTANCE_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
EC2_INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)

echo ""
echo -e "${GREEN}=== DEPLOYMENT COMPLETE ===${NC}"
echo ""
echo -e "📍 ${BLUE}Instance Details${NC}"
echo "   Instance ID: $EC2_INSTANCE_ID"
echo "   Public IP: $INSTANCE_IP"
echo "   Region: $(curl -s http://169.254.169.254/latest/meta-data/placement/region)"
echo ""
echo -e "🌐 ${BLUE}Access URLs${NC}"
echo "   Admin UI: https://$INSTANCE_IP/admin"
echo "   Chat UI: https://$INSTANCE_IP/chat"
echo "   Backend API: https://$INSTANCE_IP/api"
echo "   Health Check: https://$INSTANCE_IP/health"
echo ""
echo -e "🔑 ${BLUE}Demo Credentials${NC}"
echo "   Email: admin@msil.com"
echo "   Password: admin123"
echo ""
echo -e "📦 ${BLUE}Data Locations${NC}"
echo "   Database: /data/db/msil_mcp.db"
echo "   Logs: /data/logs/"
echo ""
echo -e "⚙️  ${BLUE}Useful Commands${NC}"
echo "   View logs: docker-compose -f $DOCKER_COMPOSE_FILE logs -f backend"
echo "   Stop services: docker-compose -f $DOCKER_COMPOSE_FILE down"
echo "   Start services: systemctl start msil-mcp"
echo "   Service status: systemctl status msil-mcp"
echo ""
echo -e "⚠️  ${YELLOW}Important Notes${NC}"
echo "   • Using self-signed SSL cert (browser warning is normal)"
echo "   • For production: Update to ACM certificate"
echo "   • Database: SQLite on EBS volume (persistent)"
echo "   • CORS: Currently set to '*' (restrict for production)"
echo ""

################################################################################
# 10. HEALTH CHECK
################################################################################
log "=== Step 10: Health Verification ==="

sleep 5

if curl -sk https://localhost/health > /dev/null 2>&1; then
    success "Backend is responding"
else
    warning "Backend health check failed - may still be initializing"
fi

if docker-compose -f "$DOCKER_COMPOSE_FILE" ps | grep -q "msil-backend.*Up"; then
    success "Backend container is running"
else
    error "Backend container not running"
fi

if docker-compose -f "$DOCKER_COMPOSE_FILE" ps | grep -q "msil-nginx.*Up"; then
    success "Nginx container is running"
else
    error "Nginx container not running"
fi

echo ""
echo -e "${GREEN}✓ Deployment Complete! System is ready to use.${NC}"
echo ""
