#!/bin/bash
# Script to run scheduled tasks
# Get script directory and navigate to project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

cd "$PROJECT_DIR"
source venv/bin/activate
python manage.py run_scheduled_tasks --settings=diaken.settings_production
