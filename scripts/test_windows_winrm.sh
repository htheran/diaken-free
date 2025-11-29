#!/bin/bash
# ================================================================
# Test WinRM Connectivity to Windows Host
# ================================================================
# Usage: ./test_windows_winrm.sh <host_ip> <username> <password>
# Example: ./test_windows_winrm.sh 10.100.5.89 Administrator MyPassword123
# ================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Check arguments
if [ $# -lt 3 ]; then
    echo -e "${RED}Error: Missing arguments${NC}"
    echo "Usage: $0 <host_ip> <username> <password> [auth_type] [port]"
    echo "Example: $0 10.100.5.89 Administrator MyPassword123 ntlm 5985"
    exit 1
fi

HOST_IP=$1
USERNAME=$2
PASSWORD=$3
AUTH_TYPE=${4:-ntlm}
PORT=${5:-5985}

echo -e "${CYAN}=======================================${NC}"
echo -e "${CYAN}WinRM Connection Test${NC}"
echo -e "${CYAN}=======================================${NC}"
echo ""
echo -e "${YELLOW}Target Configuration:${NC}"
echo "  Host IP:    $HOST_IP"
echo "  Username:   $USERNAME"
echo "  Auth Type:  $AUTH_TYPE"
echo "  Port:       $PORT"
echo ""

# Create temporary inventory file
TEMP_INV=$(mktemp)
cat > $TEMP_INV << EOF
[windows_hosts]
$HOST_IP

[windows_hosts:vars]
ansible_user=$USERNAME
ansible_password=$PASSWORD
ansible_connection=winrm
ansible_winrm_transport=$AUTH_TYPE
ansible_winrm_server_cert_validation=ignore
ansible_port=$PORT
ansible_winrm_read_timeout_sec=60
ansible_winrm_operation_timeout_sec=50
EOF

echo -e "${YELLOW}[1/4] Testing network connectivity...${NC}"
if ping -c 2 -W 2 $HOST_IP > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Network ping successful${NC}"
else
    echo -e "${RED}✗ Network ping failed${NC}"
    echo -e "${YELLOW}Note: Ping may be disabled on Windows, continuing...${NC}"
fi
echo ""

echo -e "${YELLOW}[2/4] Testing WinRM port connectivity...${NC}"
if timeout 5 bash -c "cat < /dev/null > /dev/tcp/$HOST_IP/$PORT" 2>/dev/null; then
    echo -e "${GREEN}✓ Port $PORT is open${NC}"
else
    echo -e "${RED}✗ Port $PORT is closed or unreachable${NC}"
    echo -e "${RED}Make sure WinRM is enabled and firewall allows port $PORT${NC}"
    rm -f $TEMP_INV
    exit 1
fi
echo ""

echo -e "${YELLOW}[3/4] Testing WinRM authentication (win_ping)...${NC}"
if ansible windows_hosts -i $TEMP_INV -m win_ping 2>&1 | grep -q "SUCCESS"; then
    echo -e "${GREEN}✓ WinRM authentication successful${NC}"
    echo -e "${GREEN}✓ win_ping module returned 'pong'${NC}"
else
    echo -e "${RED}✗ WinRM authentication failed${NC}"
    echo ""
    echo -e "${YELLOW}Running detailed test...${NC}"
    ansible windows_hosts -i $TEMP_INV -m win_ping -vvv
    rm -f $TEMP_INV
    exit 1
fi
echo ""

echo -e "${YELLOW}[4/4] Gathering Windows system information...${NC}"
ansible windows_hosts -i $TEMP_INV -m win_shell -a "hostname; ipconfig | findstr IPv4" 2>&1 | grep -A 10 "SUCCESS" || true
echo ""

# Cleanup
rm -f $TEMP_INV

echo -e "${CYAN}=======================================${NC}"
echo -e "${GREEN}✓ WinRM Connection Test PASSED${NC}"
echo -e "${CYAN}=======================================${NC}"
echo ""
echo -e "${GREEN}This Windows host is ready for Ansible automation!${NC}"
echo ""
echo "You can now:"
echo "  • Deploy playbooks to this host"
echo "  • Schedule tasks for this host"
echo "  • Execute updates and configurations"
echo ""
