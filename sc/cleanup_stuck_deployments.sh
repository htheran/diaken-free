#!/bin/bash
# Script to clean up stuck deployments
# Get script directory and navigate to project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

cd "$PROJECT_DIR"
source venv/bin/activate
python manage.py cleanup_stuck_deployments --timeout-hours 6 --settings=diaken.settings_production
