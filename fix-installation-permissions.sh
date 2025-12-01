#!/bin/bash
#
# Fix Installation Permissions for Diaken
# This script fixes common permission issues in new installations
#

set -e

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║     DIAKEN INSTALLATION PERMISSIONS FIX                     ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Detect installation directory
if [ -d "/opt/diaken" ]; then
    INSTALL_DIR="/opt/diaken"
elif [ -d "/opt/base/app/diaken" ]; then
    INSTALL_DIR="/opt/base/app/diaken"
else
    echo -e "${RED}❌ ERROR: Diaken installation not found${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Found Diaken installation: $INSTALL_DIR"
echo ""

DIAKEN_USER="diaken"
LOG_DIR="/var/log/diaken"

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}DIAGNOSTIC${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Check if user exists
if ! id "$DIAKEN_USER" &>/dev/null; then
    echo -e "${RED}❌ ERROR: User '$DIAKEN_USER' does not exist${NC}"
    exit 1
fi
echo -e "${GREEN}✓${NC} User '$DIAKEN_USER' exists"

# Check .env file
ENV_FILE="$INSTALL_DIR/.env"
if [ -f "$ENV_FILE" ]; then
    echo -e "${GREEN}✓${NC} .env file exists"
    ENV_OWNER=$(stat -c '%U:%G' "$ENV_FILE")
    ENV_PERMS=$(stat -c '%a' "$ENV_FILE")
    echo "  Owner: $ENV_OWNER"
    echo "  Permissions: $ENV_PERMS"
else
    echo -e "${RED}❌${NC} .env file does NOT exist"
fi

# Check log directory
if [ -d "$LOG_DIR" ]; then
    echo -e "${GREEN}✓${NC} Log directory exists: $LOG_DIR"
    LOG_OWNER=$(stat -c '%U:%G' "$LOG_DIR")
    LOG_PERMS=$(stat -c '%a' "$LOG_DIR")
    echo "  Owner: $LOG_OWNER"
    echo "  Permissions: $LOG_PERMS"
else
    echo -e "${YELLOW}⚠${NC}  Log directory does NOT exist: $LOG_DIR"
fi

# Check installation directory ownership
INSTALL_OWNER=$(stat -c '%U:%G' "$INSTALL_DIR")
echo -e "${GREEN}✓${NC} Installation directory owner: $INSTALL_OWNER"

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}FIX${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Fix .env permissions
if [ -f "$ENV_FILE" ]; then
    CURRENT_OWNER=$(stat -c '%U' "$ENV_FILE")
    if [ "$CURRENT_OWNER" != "$DIAKEN_USER" ]; then
        echo "Fixing .env ownership..."
        sudo chown "$DIAKEN_USER":"$DIAKEN_USER" "$ENV_FILE"
        echo -e "${GREEN}✓${NC} .env ownership fixed"
    else
        echo -e "${GREEN}✓${NC} .env ownership is correct"
    fi
    
    CURRENT_PERMS=$(stat -c '%a' "$ENV_FILE")
    if [ "$CURRENT_PERMS" != "640" ]; then
        echo "Fixing .env permissions..."
        sudo chmod 640 "$ENV_FILE"
        echo -e "${GREEN}✓${NC} .env permissions fixed (640)"
    else
        echo -e "${GREEN}✓${NC} .env permissions are correct"
    fi
fi

# Create and fix log directory
if [ ! -d "$LOG_DIR" ]; then
    echo "Creating log directory: $LOG_DIR"
    sudo mkdir -p "$LOG_DIR"
    sudo chown "$DIAKEN_USER":"$DIAKEN_USER" "$LOG_DIR"
    sudo chmod 755 "$LOG_DIR"
    echo -e "${GREEN}✓${NC} Log directory created"
else
    echo -e "${GREEN}✓${NC} Log directory already exists"
    # Fix ownership if needed
    CURRENT_OWNER=$(stat -c '%U' "$LOG_DIR")
    if [ "$CURRENT_OWNER" != "$DIAKEN_USER" ]; then
        echo "Fixing log directory ownership..."
        sudo chown -R "$DIAKEN_USER":"$DIAKEN_USER" "$LOG_DIR"
        echo -e "${GREEN}✓${NC} Log directory ownership fixed"
    fi
fi

# Fix installation directory ownership
echo "Fixing installation directory ownership..."
sudo chown -R "$DIAKEN_USER":"$DIAKEN_USER" "$INSTALL_DIR"
echo -e "${GREEN}✓${NC} Installation directory ownership fixed"

# Fix specific directories
echo "Fixing media directory permissions..."
sudo chown -R "$DIAKEN_USER":"$DIAKEN_USER" "$INSTALL_DIR/media"
sudo chmod -R 755 "$INSTALL_DIR/media"
echo -e "${GREEN}✓${NC} Media directory permissions fixed"

echo "Fixing static directory permissions..."
sudo chown -R "$DIAKEN_USER":"$DIAKEN_USER" "$INSTALL_DIR/static"
sudo chmod -R 755 "$INSTALL_DIR/static"
echo -e "${GREEN}✓${NC} Static directory permissions fixed"

# Fix database permissions
if [ -f "$INSTALL_DIR/db.sqlite3" ]; then
    echo "Fixing database permissions..."
    sudo chown "$DIAKEN_USER":"$DIAKEN_USER" "$INSTALL_DIR/db.sqlite3"
    sudo chmod 664 "$INSTALL_DIR/db.sqlite3"
    echo -e "${GREEN}✓${NC} Database permissions fixed"
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}VERIFICATION${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

echo "Installation directory:"
ls -ld "$INSTALL_DIR"

if [ -f "$ENV_FILE" ]; then
    echo ""
    echo ".env file:"
    ls -l "$ENV_FILE"
fi

if [ -d "$LOG_DIR" ]; then
    echo ""
    echo "Log directory:"
    ls -ld "$LOG_DIR"
fi

echo ""
echo -e "${GREEN}✓${NC} Fix completed successfully!"
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}NEXT STEPS${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo "1. Restart Django:"
echo "   sudo systemctl restart diaken"
echo ""
echo "2. Test scheduler command:"
echo "   cd $INSTALL_DIR"
echo "   source venv/bin/activate"
echo "   python manage.py run_scheduled_tasks"
echo ""
echo "3. Verify logs are created:"
echo "   ls -l $LOG_DIR/"
echo ""
