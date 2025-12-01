#!/bin/bash
#
# Diaken Scheduler Cron Setup
# This script adds the cron job needed for scheduled tasks to work
#

set -e

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║     DIAKEN SCHEDULER - CRON JOB SETUP                       ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
   echo -e "${RED}❌ ERROR: Do not run this script as root${NC}"
   echo "Run as the diaken user instead"
   exit 1
fi

# Detect installation directory
if [ -d "/opt/diaken" ]; then
    DIAKEN_DIR="/opt/diaken"
elif [ -d "/opt/base/app/diaken" ]; then
    DIAKEN_DIR="/opt/base/app/diaken"
else
    echo -e "${RED}❌ ERROR: Diaken installation not found${NC}"
    echo "Expected: /opt/diaken or /opt/base/app/diaken"
    exit 1
fi

echo -e "${GREEN}✓${NC} Found Diaken installation: $DIAKEN_DIR"
echo ""

# Check if venv exists
if [ ! -d "$DIAKEN_DIR/venv" ]; then
    echo -e "${RED}❌ ERROR: Virtual environment not found${NC}"
    echo "Expected: $DIAKEN_DIR/venv"
    exit 1
fi

echo -e "${GREEN}✓${NC} Found virtual environment"
echo ""

# Check if manage.py exists
if [ ! -f "$DIAKEN_DIR/manage.py" ]; then
    echo -e "${RED}❌ ERROR: manage.py not found${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Found manage.py"
echo ""

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "run_scheduled_tasks"; then
    echo -e "${YELLOW}⚠${NC}  Cron job already exists"
    echo ""
    echo "Current crontab:"
    crontab -l | grep "run_scheduled_tasks"
    echo ""
    read -p "Do you want to update it? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted"
        exit 0
    fi
    # Remove old cron job
    crontab -l | grep -v "run_scheduled_tasks" | crontab -
    echo -e "${GREEN}✓${NC} Removed old cron job"
fi

# Create log directory if it doesn't exist
LOG_DIR="/var/log/diaken"
if [ ! -d "$LOG_DIR" ]; then
    echo "Creating log directory: $LOG_DIR"
    sudo mkdir -p "$LOG_DIR"
    sudo chown $(whoami):$(whoami) "$LOG_DIR"
    echo -e "${GREEN}✓${NC} Created log directory"
fi

# Add cron job
echo "Adding cron job..."
(crontab -l 2>/dev/null; echo "# Diaken Scheduled Tasks - Run every minute") | crontab -
(crontab -l 2>/dev/null; echo "* * * * * cd $DIAKEN_DIR && $DIAKEN_DIR/venv/bin/python manage.py run_scheduled_tasks >> $LOG_DIR/scheduler.log 2>&1") | crontab -

echo -e "${GREEN}✓${NC} Cron job added successfully"
echo ""

# Verify cron job
echo "═══════════════════════════════════════════════════════════════"
echo "Current crontab:"
echo "═══════════════════════════════════════════════════════════════"
crontab -l | grep -A1 "Diaken Scheduled Tasks"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Test the command manually
echo "Testing scheduler command..."
cd "$DIAKEN_DIR"
source venv/bin/activate
python manage.py run_scheduled_tasks
echo ""

echo -e "${GREEN}✓${NC} Setup complete!"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "NEXT STEPS"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "1. The scheduler will now run every minute automatically"
echo "2. View logs: tail -f $LOG_DIR/scheduler.log"
echo "3. Test by scheduling a task in Diaken UI"
echo "4. Check task execution in: History → Scheduled Task History"
echo ""
echo "═══════════════════════════════════════════════════════════════"
