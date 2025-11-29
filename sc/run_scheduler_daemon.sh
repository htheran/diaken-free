#!/bin/bash
# Script to run scheduled tasks in daemon mode
# This runs continuously and checks for tasks every 10 seconds
# Get script directory and navigate to project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

cd "$PROJECT_DIR"
source venv/bin/activate
python manage.py run_scheduled_tasks --daemon --interval 10 --settings=diaken.settings_production
