#!/bin/bash

# ==============================================================================
# A-OS (Africa Offline OS) - One-Command Installer
# Target: Raspberry Pi / Debian-based OS
# ==============================================================================

# Exit on any error
set -e

# Configuration
APP_DIR="/app"
REPO_URL="https://github.com/peteroluoch/africa-offline-os.git"
AOS_USER="aos-user"
VENV_NAME="aos_venv"

# Text Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== A-OS (Africa Offline OS) Installation Started ===${NC}"

# 1. Check for root/sudo
if [ "$EUID" -ne 0 ]; then
  echo -e "${YELLOW}Please run as root or with sudo${NC}"
  exit 1
fi

# 2. Install System Dependencies
echo -e "${GREEN}[1/6] Installing system dependencies...${NC}"
apt-get update
apt-get install -y python3-venv python3-pip sqlite3 git curl

# 3. Setup Restricted User
echo -e "${GREEN}[2/6] Setting up restricted system user: ${AOS_USER}...${NC}"
if ! id "$AOS_USER" &>/dev/null; then
    useradd -r -s /bin/false "$AOS_USER"
fi

# 4. Prepare App Directory
echo -e "${GREEN}[3/6] Preparing application directory...${NC}"
mkdir -p "$APP_DIR"
chown "$AOS_USER":"$AOS_USER" "$APP_DIR"

# 5. Initialize/Update Application
echo -e "${GREEN}[4/6] Initializing application code...${NC}"
if [ ! -d "$APP_DIR/.git" ]; then
    git clone "$REPO_URL" "$APP_DIR"
else
    echo "A-OS already exists, pulling latest updates..."
    cd "$APP_DIR"
    git pull
fi

# Set ownership of the app directory to the restricted user
chown -R "$AOS_USER":"$AOS_USER" "$APP_DIR"
# Lockdown permissions: Owner only access
chmod -R 700 "$APP_DIR"

# 5. Setup Virtual Environment
echo -e "${GREEN}[5/6] Setting up virtual environment...${NC}"
cd "$APP_DIR"
if [ ! -d "$VENV_NAME" ]; then
    sudo -u "$AOS_USER" python3 -m venv "$VENV_NAME"
fi

echo "Installing requirements..."
sudo -u "$AOS_USER" ./"$VENV_NAME"/bin/pip install --upgrade pip
sudo -u "$AOS_USER" ./"$VENV_NAME"/bin/pip install -r requirements.txt

# 6. Setup Systemd Service
echo -e "${GREEN}[6/6] Registering systemd service...${NC}"
cat <<EOF > /etc/systemd/system/aos.service
[Unit]
Description=A-OS (Africa Offline OS) Kernel
After=network.target

[Service]
User=$AOS_USER
Group=$AOS_USER
WorkingDirectory=$APP_DIR
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/$VENV_NAME/bin/python main.py
Restart=always
RestartSec=5
# Security: Restricted access to /tmp, /home, etc.
PrivateTmp=true
ProtectSystem=full
ProtectHome=true

StandardOutput=append:$APP_DIR/data/logs/aos.log
StandardError=append:$APP_DIR/data/logs/aos.log

[Install]
WantedBy=multi-user.target
EOF

# Ensure logs directory exists with correct permissions
sudo -u "$AOS_USER" mkdir -p "$APP_DIR/data/logs"

systemctl daemon-reload
systemctl enable aos.service

# Final Check
echo -e "${BLUE}=== Installation Complete! ===${NC}"
echo -e "Systemd service 'aos' is registered and enabled."
echo -e "To start the service: ${YELLOW}sudo systemctl start aos${NC}"
echo -e "To check status: ${YELLOW}sudo systemctl status aos${NC}"

# Security Notes
echo -e "\n${YELLOW}SECURITY NOTES:${NC}"
echo -e "1. A-OS is running as the restricted user: ${AOS_USER}"
echo -e "2. The directory ${APP_DIR} is only accessible by ${AOS_USER}"
echo -e "3. Please ensure ${APP_DIR}/.env contains your secrets (TELEGRAM_BOT_TOKEN, etc.)"

# Check if .env exists, if not warn
if [ ! -f "$APP_DIR/.env" ]; then
    echo -e "${YELLOW}WARNING: .env file missing in ${APP_DIR}.${NC}"
    echo -e "Copy .env.example to .env and fill in your details."
fi
