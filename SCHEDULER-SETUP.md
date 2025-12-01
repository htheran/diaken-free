# Scheduler Setup Guide

## Overview

Diaken includes a powerful task scheduler that can execute playbooks and scripts on hosts at specified times.

## How It Works

The scheduler uses a cron job that runs every minute to check for pending tasks and execute them.

## Setup

### Automatic Setup (via installer)

If you used `install-diaken-nginx.sh`, the scheduler is already configured.

### Manual Setup

If you installed manually, add this cron job:

```bash
# Add to crontab
crontab -e

# Add this line:
* * * * * cd /opt/diaken && /opt/diaken/venv/bin/python manage.py run_scheduled_tasks >> /var/log/diaken/scheduler.log 2>&1
```

### Verify Setup

```bash
# Check crontab
crontab -l | grep run_scheduled_tasks

# Check logs
tail -f /var/log/diaken/scheduler.log

# Test manually
cd /opt/diaken
source venv/bin/activate
python manage.py run_scheduled_tasks
```

## Usage

### 1. Schedule a Task

Go to: **Deploy → Schedule Task**

Options:
- **Execution Type**: Playbook or Script
- **Target**: Select host or group
- **Playbook/Script**: Choose what to execute
- **Scheduled Time**: When to run
- **Create Snapshot**: Optional VM snapshot before execution

### 2. View Scheduled Tasks

Go to: **Scheduled Tasks** (sidebar menu)

You'll see:
- Task name
- Type (Host/Group)
- Target
- Playbook/Script
- Scheduled time
- Status (Pending/In Progress/Completed/Failed/Cancelled)
- Actions (Cancel)

### 3. View Task History

Go to: **History → Scheduled Task History**

Shows:
- All executed tasks
- Execution time
- Duration
- Status
- Output
- Errors (if any)

## Task Statuses

| Status | Description |
|--------|-------------|
| **Pending** | Waiting for scheduled time |
| **In Progress** | Currently executing |
| **Completed** | Finished successfully |
| **Failed** | Execution failed |
| **Cancelled** | Manually cancelled |

## Troubleshooting

### Tasks Not Executing

**Problem:** Tasks stay in "Pending" status past their scheduled time.

**Solution:**
```bash
# 1. Check if cron job exists
crontab -l | grep run_scheduled_tasks

# 2. If missing, add it
crontab -e
# Add: * * * * * cd /opt/diaken && /opt/diaken/venv/bin/python manage.py run_scheduled_tasks >> /var/log/diaken/scheduler.log 2>&1

# 3. Check logs
tail -f /var/log/diaken/scheduler.log

# 4. Test manually
cd /opt/diaken
source venv/bin/activate
python manage.py run_scheduled_tasks
```

### Scheduler Menu Not Working

**Problem:** Clicking "Scheduled Tasks" in sidebar does nothing.

**Solution:**
1. Clear browser cache (Ctrl+Shift+Delete)
2. Hard refresh (Ctrl+F5)
3. Check browser console for JavaScript errors (F12)

### Tasks Fail Immediately

**Problem:** Tasks go to "Failed" status right away.

**Possible causes:**
1. **SSH key not configured** - Check SSH credentials
2. **Host unreachable** - Verify network connectivity
3. **Playbook/script not found** - Check file exists
4. **Permissions** - Ensure diaken user has access

**Debug:**
```bash
# View task output
# Go to: History → Scheduled Task History → Click on task → View Output

# Check logs
tail -100 /var/log/diaken/scheduler.log
tail -100 /var/log/diaken/ansible/scheduler-*.log
```

## Advanced Configuration

### Change Execution Frequency

By default, the scheduler checks every minute. To change:

```bash
# Edit crontab
crontab -e

# Examples:
# Every 5 minutes:
*/5 * * * * cd /opt/diaken && /opt/diaken/venv/bin/python manage.py run_scheduled_tasks >> /var/log/diaken/scheduler.log 2>&1

# Every 30 seconds (requires two entries):
* * * * * cd /opt/diaken && /opt/diaken/venv/bin/python manage.py run_scheduled_tasks >> /var/log/diaken/scheduler.log 2>&1
* * * * * sleep 30 && cd /opt/diaken && /opt/diaken/venv/bin/python manage.py run_scheduled_tasks >> /var/log/diaken/scheduler.log 2>&1
```

### Cleanup Old Task History

```bash
# Via Django shell
cd /opt/diaken
source venv/bin/activate
python manage.py shell

# Delete history older than 30 days
from scheduler.models import ScheduledTaskHistory
from django.utils import timezone
from datetime import timedelta

cutoff_date = timezone.now() - timedelta(days=30)
old_tasks = ScheduledTaskHistory.objects.filter(created_at__lt=cutoff_date)
count = old_tasks.count()
old_tasks.delete()
print(f"Deleted {count} old task history records")
```

## Best Practices

1. **Test playbooks manually first** before scheduling
2. **Use descriptive task names** for easy identification
3. **Enable snapshots** for critical operations
4. **Monitor logs** regularly
5. **Clean up old history** periodically
6. **Set realistic timeouts** based on task complexity
7. **Use groups** for bulk operations
8. **Schedule during maintenance windows** for disruptive tasks

## Examples

### Example 1: Daily System Updates

```
Task Name: Daily Update - Production Servers
Type: Playbook
Target: Group "Production"
Playbook: Update-Redhat-Host
Schedule: Daily at 2:00 AM
Snapshot: Yes
```

### Example 2: Weekly Backup

```
Task Name: Weekly Backup - Database Server
Type: Script
Target: Host "db01"
Script: backup_database.sh
Schedule: Every Sunday at 3:00 AM
Snapshot: Yes
```

### Example 3: Hourly Health Check

```
Task Name: Health Check - Web Servers
Type: Playbook
Target: Group "Web Servers"
Playbook: health_check
Schedule: Every hour
Snapshot: No
```

## Logs

| Log File | Purpose |
|----------|---------|
| `/var/log/diaken/scheduler.log` | Main scheduler log |
| `/var/log/diaken/ansible/scheduler-*.log` | Ansible execution logs |
| `/var/log/diaken/error.log` | Django errors |

## Support

- **Documentation**: https://github.com/htheran/diaken-free
- **Issues**: https://github.com/htheran/diaken-free/issues
