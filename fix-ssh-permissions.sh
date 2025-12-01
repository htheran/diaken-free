#!/bin/bash
#
# Fix SSH Permissions for Diaken
# This script fixes the home directory and SSH permissions for existing installations
#

set -e

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║     DIAKEN SSH PERMISSIONS FIX                              ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Detect user
DIAKEN_USER="diaken"

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

# Check home directory
HOME_DIR="/home/$DIAKEN_USER"
if [ -d "$HOME_DIR" ]; then
    echo -e "${GREEN}✓${NC} Home directory exists: $HOME_DIR"
    HOME_OWNER=$(stat -c '%U:%G' "$HOME_DIR")
    HOME_PERMS=$(stat -c '%a' "$HOME_DIR")
    echo "  Owner: $HOME_OWNER"
    echo "  Permissions: $HOME_PERMS"
else
    echo -e "${YELLOW}⚠${NC}  Home directory does NOT exist: $HOME_DIR"
fi

# Check .ssh directory
SSH_DIR="$HOME_DIR/.ssh"
if [ -d "$SSH_DIR" ]; then
    echo -e "${GREEN}✓${NC} SSH directory exists: $SSH_DIR"
    SSH_OWNER=$(stat -c '%U:%G' "$SSH_DIR")
    SSH_PERMS=$(stat -c '%a' "$SSH_DIR")
    echo "  Owner: $SSH_OWNER"
    echo "  Permissions: $SSH_PERMS"
else
    echo -e "${YELLOW}⚠${NC}  SSH directory does NOT exist: $SSH_DIR"
fi

# Check known_hosts
KNOWN_HOSTS="$SSH_DIR/known_hosts"
if [ -f "$KNOWN_HOSTS" ]; then
    echo -e "${GREEN}✓${NC} known_hosts exists: $KNOWN_HOSTS"
    KH_OWNER=$(stat -c '%U:%G' "$KNOWN_HOSTS")
    KH_PERMS=$(stat -c '%a' "$KNOWN_HOSTS")
    echo "  Owner: $KH_OWNER"
    echo "  Permissions: $KH_PERMS"
else
    echo -e "${YELLOW}⚠${NC}  known_hosts does NOT exist: $KNOWN_HOSTS"
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}FIX${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Create home directory if it doesn't exist
if [ ! -d "$HOME_DIR" ]; then
    echo "Creating home directory: $HOME_DIR"
    sudo mkdir -p "$HOME_DIR"
    sudo chown "$DIAKEN_USER":"$DIAKEN_USER" "$HOME_DIR"
    sudo chmod 755 "$HOME_DIR"
    echo -e "${GREEN}✓${NC} Home directory created"
else
    echo -e "${GREEN}✓${NC} Home directory already exists"
    # Fix ownership if needed
    CURRENT_OWNER=$(stat -c '%U' "$HOME_DIR")
    if [ "$CURRENT_OWNER" != "$DIAKEN_USER" ]; then
        echo "Fixing ownership of home directory..."
        sudo chown "$DIAKEN_USER":"$DIAKEN_USER" "$HOME_DIR"
        echo -e "${GREEN}✓${NC} Ownership fixed"
    fi
    # Fix permissions if needed
    CURRENT_PERMS=$(stat -c '%a' "$HOME_DIR")
    if [ "$CURRENT_PERMS" != "755" ]; then
        echo "Fixing permissions of home directory..."
        sudo chmod 755 "$HOME_DIR"
        echo -e "${GREEN}✓${NC} Permissions fixed"
    fi
fi

# Create .ssh directory if it doesn't exist
if [ ! -d "$SSH_DIR" ]; then
    echo "Creating .ssh directory: $SSH_DIR"
    sudo mkdir -p "$SSH_DIR"
    sudo chown "$DIAKEN_USER":"$DIAKEN_USER" "$SSH_DIR"
    sudo chmod 700 "$SSH_DIR"
    echo -e "${GREEN}✓${NC} .ssh directory created"
else
    echo -e "${GREEN}✓${NC} .ssh directory already exists"
    # Fix ownership if needed
    CURRENT_OWNER=$(stat -c '%U' "$SSH_DIR")
    if [ "$CURRENT_OWNER" != "$DIAKEN_USER" ]; then
        echo "Fixing ownership of .ssh directory..."
        sudo chown "$DIAKEN_USER":"$DIAKEN_USER" "$SSH_DIR"
        echo -e "${GREEN}✓${NC} Ownership fixed"
    fi
    # Fix permissions if needed
    CURRENT_PERMS=$(stat -c '%a' "$SSH_DIR")
    if [ "$CURRENT_PERMS" != "700" ]; then
        echo "Fixing permissions of .ssh directory..."
        sudo chmod 700 "$SSH_DIR"
        echo -e "${GREEN}✓${NC} Permissions fixed"
    fi
fi

# Create known_hosts if it doesn't exist
if [ ! -f "$KNOWN_HOSTS" ]; then
    echo "Creating known_hosts file: $KNOWN_HOSTS"
    sudo touch "$KNOWN_HOSTS"
    sudo chown "$DIAKEN_USER":"$DIAKEN_USER" "$KNOWN_HOSTS"
    sudo chmod 644 "$KNOWN_HOSTS"
    echo -e "${GREEN}✓${NC} known_hosts file created"
else
    echo -e "${GREEN}✓${NC} known_hosts file already exists"
    # Fix ownership if needed
    CURRENT_OWNER=$(stat -c '%U' "$KNOWN_HOSTS")
    if [ "$CURRENT_OWNER" != "$DIAKEN_USER" ]; then
        echo "Fixing ownership of known_hosts..."
        sudo chown "$DIAKEN_USER":"$DIAKEN_USER" "$KNOWN_HOSTS"
        echo -e "${GREEN}✓${NC} Ownership fixed"
    fi
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}VERIFICATION${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

echo "Final structure:"
ls -la "$HOME_DIR" 2>/dev/null || echo "  (home directory not accessible)"
if [ -d "$SSH_DIR" ]; then
    echo ""
    echo ".ssh directory:"
    ls -la "$SSH_DIR" 2>/dev/null || echo "  (ssh directory not accessible)"
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
echo "2. Test by adding a host:"
echo "   Inventory → Hosts → Create"
echo ""
echo "3. Verify SSH fingerprint is accepted:"
echo "   cat $KNOWN_HOSTS"
echo ""
