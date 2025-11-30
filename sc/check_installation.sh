#!/bin/bash
################################################################################
# Script: check_installation.sh
# Description: Verifica que todos los servicios estén corriendo y lista logs
# Usage: ./check_installation.sh
################################################################################

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Installation directory
INSTALL_DIR="/opt/diaken"
LOG_DIR="/var/log/diaken"

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     DIAKEN - Installation Verification Report                ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to check service status
check_service() {
    local service_name=$1
    local display_name=$2
    
    if systemctl is-active --quiet "$service_name"; then
        echo -e "${GREEN}✓${NC} $display_name: ${GREEN}Running${NC}"
        systemctl status "$service_name" --no-pager | grep "Active:" | sed 's/^/  /'
        return 0
    else
        echo -e "${RED}✗${NC} $display_name: ${RED}Not Running${NC}"
        return 1
    fi
}

# Function to check if service exists
service_exists() {
    systemctl list-unit-files | grep -q "^$1"
}

# Function to list log files
list_logs() {
    local log_subdir=$1
    local display_name=$2
    
    if [ -d "$LOG_DIR/$log_subdir" ]; then
        echo -e "\n${YELLOW}$display_name Logs:${NC}"
        find "$LOG_DIR/$log_subdir" -type f -name "*.log" -o -name "*.log.*" 2>/dev/null | while read -r logfile; do
            size=$(du -h "$logfile" | cut -f1)
            modified=$(stat -c %y "$logfile" | cut -d' ' -f1,2 | cut -d'.' -f1)
            echo -e "  ${BLUE}•${NC} $logfile (${size}, modified: $modified)"
        done
    else
        echo -e "\n${YELLOW}$display_name Logs:${NC} ${RED}Directory not found${NC}"
    fi
}

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}SERVICES STATUS${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Check Django service
check_service "diaken" "Django (Diaken)"

# Check Nginx
if service_exists "nginx"; then
    check_service "nginx" "Nginx"
fi

# Check Redis
if service_exists "redis"; then
    check_service "redis" "Redis"
fi

# Check Celery Worker
if service_exists "celery-worker"; then
    check_service "celery-worker" "Celery Worker"
fi

# Check Celery Beat
if service_exists "celery-beat"; then
    check_service "celery-beat" "Celery Beat"
fi

# Check MariaDB
if service_exists "mariadb"; then
    check_service "mariadb" "MariaDB"
fi

# Check PostgreSQL
if service_exists "postgresql"; then
    check_service "postgresql" "PostgreSQL"
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}LOG FILES${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"

# List Django logs
if [ -d "$LOG_DIR" ]; then
    echo -e "\n${YELLOW}Django Logs:${NC}"
    find "$LOG_DIR" -maxdepth 1 -type f \( -name "*.log" -o -name "*.log.*" \) 2>/dev/null | while read -r logfile; do
        size=$(du -h "$logfile" | cut -f1)
        modified=$(stat -c %y "$logfile" | cut -d' ' -f1,2 | cut -d'.' -f1)
        echo -e "  ${BLUE}•${NC} $logfile (${size}, modified: $modified)"
    done
fi

# List Ansible logs
list_logs "ansible" "Ansible"

# List Celery logs
list_logs "celery" "Celery"

# List Redis logs
if [ -d "/var/log/redis" ]; then
    echo -e "\n${YELLOW}Redis Logs:${NC}"
    find /var/log/redis -type f -name "*.log" 2>/dev/null | while read -r logfile; do
        size=$(du -h "$logfile" | cut -f1)
        modified=$(stat -c %y "$logfile" | cut -d' ' -f1,2 | cut -d'.' -f1)
        echo -e "  ${BLUE}•${NC} $logfile (${size}, modified: $modified)"
    done
fi

# List Nginx logs
if [ -d "/var/log/nginx" ]; then
    echo -e "\n${YELLOW}Nginx Logs:${NC}"
    find /var/log/nginx -type f \( -name "*diaken*" -o -name "access.log" -o -name "error.log" \) 2>/dev/null | while read -r logfile; do
        size=$(du -h "$logfile" | cut -f1)
        modified=$(stat -c %y "$logfile" | cut -d' ' -f1,2 | cut -d'.' -f1)
        echo -e "  ${BLUE}•${NC} $logfile (${size}, modified: $modified)"
    done
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}CRONTAB TASKS${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

if sudo crontab -l 2>/dev/null | grep -q "diaken"; then
    echo -e "${GREEN}Crontab tasks configured:${NC}"
    sudo crontab -l 2>/dev/null | grep "diaken" | while read -r line; do
        echo -e "  ${BLUE}•${NC} $line"
    done
else
    echo -e "${RED}No crontab tasks found for Diaken${NC}"
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}DISK USAGE${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

echo -e "${YELLOW}Installation Directory:${NC}"
du -sh "$INSTALL_DIR" 2>/dev/null || echo -e "${RED}Not found${NC}"

echo -e "\n${YELLOW}Log Directory:${NC}"
du -sh "$LOG_DIR" 2>/dev/null || echo -e "${RED}Not found${NC}"

echo -e "\n${YELLOW}Database:${NC}"
if [ -f "$INSTALL_DIR/db.sqlite3" ]; then
    du -sh "$INSTALL_DIR/db.sqlite3"
else
    echo -e "${YELLOW}Using external database (MariaDB/PostgreSQL)${NC}"
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}RECENT LOG ENTRIES${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Show last 5 lines of Django log
if [ -f "$LOG_DIR/django.log" ]; then
    echo -e "${YELLOW}Last 5 lines of Django log:${NC}"
    tail -5 "$LOG_DIR/django.log" 2>/dev/null | sed 's/^/  /'
fi

# Show last 5 lines of scheduler log
if [ -f "$LOG_DIR/scheduler.log" ]; then
    echo -e "\n${YELLOW}Last 5 lines of Scheduler log:${NC}"
    tail -5 "$LOG_DIR/scheduler.log" 2>/dev/null | sed 's/^/  /'
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Verification complete${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
