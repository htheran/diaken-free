#!/bin/bash
# Script to cleanup old vCenter snapshots
# Get script directory and navigate to project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

cd "$PROJECT_DIR" || exit 1
source venv/bin/activate || exit 1
python manage.py cleanup_snapshots --settings=diaken.settings_production
