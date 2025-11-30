#!/bin/bash
# Script to cleanup old vCenter snapshots
# This script automatically removes expired snapshots from vCenter

# Get script directory and navigate to project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

# Change to project directory
cd "$PROJECT_DIR" || exit 1

# Activate virtual environment
source venv/bin/activate || exit 1

# Run cleanup command
# Use --settings=diaken.settings_production for production or omit for default settings.py
python manage.py cleanup_snapshots
