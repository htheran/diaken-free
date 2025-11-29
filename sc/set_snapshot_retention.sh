#!/bin/bash
# Script to set snapshot retention hours
# Usage: ./set_snapshot_retention.sh [hours]
# Example: ./set_snapshot_retention.sh 72

if [ -z "$1" ]; then
    echo "Usage: $0 <hours>"
    echo "Range: 1-99 hours"
    echo ""
    echo "Current value:"
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
    cd "$PROJECT_DIR"
    source venv/bin/activate
    python manage.py shell -c "from settings.models import GlobalSetting; s = GlobalSetting.objects.get(key='snapshot_retention_hours'); print(f'  {s.value} hours')" --settings=diaken.settings_production
    exit 1
fi

HOURS=$1

if [ "$HOURS" -lt 1 ] || [ "$HOURS" -gt 99 ]; then
    echo "Error: Hours must be between 1 and 99"
    exit 1
fi

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
cd "$PROJECT_DIR"
source venv/bin/activate

python manage.py shell -c " --settings=diaken.settings_production
from settings.models import GlobalSetting
s = GlobalSetting.objects.get(key='snapshot_retention_hours')
old_value = s.value
s.value = '$HOURS'
s.save()
print(f'✓ Snapshot retention changed from {old_value} to {s.value} hours')
"

echo "✓ Done!"
