# Notifications Integration Examples

This document provides practical examples for integrating notifications into existing Diaken code.

---

## 📋 Integration Points

### 1. VM Deployment Notifications

**File**: `/opt/www/app/deploy/views.py`

**Location**: After successful VM deployment

**Example**:
```python
# At the top of the file, add import
from notifications.utils import send_deployment_notification

# In deploy_vm_linux() or deploy_vm_windows() function
# After: deployment.save()
# Add:

# Send notification
try:
    send_deployment_notification(deployment, request.user)
except Exception as e:
    # Log error but don't fail deployment
    print(f"Failed to send notification: {e}")
```

**Complete Example**:
```python
def deploy_vm_linux(request):
    # ... existing code ...
    
    # Save deployment
    deployment.status = 'success'
    deployment.end_time = timezone.now()
    deployment.save()
    
    # Send notification (NEW)
    try:
        from notifications.utils import send_deployment_notification
        send_deployment_notification(deployment, request.user)
    except Exception as e:
        print(f"Notification error: {e}")
    
    # ... rest of code ...
```

---

### 2. Playbook Execution Notifications

**File**: `/opt/www/app/deploy/views.py` or playbook execution views

**Location**: After playbook execution completes

**Example**:
```python
# At the top of the file, add import
from notifications.utils import send_playbook_notification

# After playbook execution
# After: history.save()
# Add:

# Prepare target info
target_info = {
    'type': 'host',  # or 'group'
    'name': host.hostname  # or group.name
}

# Send notification
try:
    send_playbook_notification(history, request.user, target_info)
except Exception as e:
    print(f"Failed to send notification: {e}")
```

**Complete Example (Host)**:
```python
def execute_playbook_on_host(request):
    # ... existing code ...
    
    # Save history
    history.status = 'success'
    history.end_time = timezone.now()
    history.save()
    
    # Send notification (NEW)
    try:
        from notifications.utils import send_playbook_notification
        target_info = {
            'type': 'host',
            'name': host.hostname
        }
        send_playbook_notification(history, request.user, target_info)
    except Exception as e:
        print(f"Notification error: {e}")
    
    # ... rest of code ...
```

**Complete Example (Group)**:
```python
def execute_playbook_on_group(request):
    # ... existing code ...
    
    # Save history
    history.status = 'success'
    history.end_time = timezone.now()
    history.save()
    
    # Send notification (NEW)
    try:
        from notifications.utils import send_playbook_notification
        target_info = {
            'type': 'group',
            'name': group.name
        }
        send_playbook_notification(history, request.user, target_info)
    except Exception as e:
        print(f"Notification error: {e}")
    
    # ... rest of code ...
```

---

### 3. Scheduled Task Notifications

**File**: `/opt/www/app/scheduler/management/commands/run_scheduler.py`

**Location**: After scheduled task execution completes

**Example**:
```python
# At the top of the file, add import
from notifications.utils import send_scheduled_task_notification

# After task execution
# After: task_history.save()
# Add:

# Send notification
try:
    send_scheduled_task_notification(task_history, task)
except Exception as e:
    print(f"Failed to send notification: {e}")
```

**Complete Example**:
```python
def handle(self, *args, **options):
    # ... existing code ...
    
    # Execute task
    # ... execution code ...
    
    # Save task history
    task_history.status = 'success'
    task_history.end_time = timezone.now()
    task_history.save()
    
    # Send notification (NEW)
    try:
        from notifications.utils import send_scheduled_task_notification
        send_scheduled_task_notification(task_history, task)
    except Exception as e:
        print(f"Notification error: {e}")
    
    # ... rest of code ...
```

---

## 🎯 Best Practices

### 1. Always Use Try-Except

Never let notification failures break your main functionality:

```python
try:
    send_deployment_notification(deployment, request.user)
except Exception as e:
    # Log but don't fail
    print(f"Notification error: {e}")
```

### 2. Send After Success

Only send notifications after the operation completes successfully:

```python
# ✅ GOOD
deployment.status = 'success'
deployment.save()
send_deployment_notification(deployment, request.user)

# ❌ BAD
send_deployment_notification(deployment, request.user)
deployment.status = 'success'
deployment.save()
```

### 3. Include All Required Data

Make sure the object has all required fields before sending:

```python
# ✅ GOOD
deployment.vm_name = "web-01"
deployment.vm_ip = "10.100.5.89"
deployment.status = "success"
deployment.end_time = timezone.now()
deployment.save()
send_deployment_notification(deployment, request.user)

# ❌ BAD
deployment.vm_name = "web-01"
deployment.save()
send_deployment_notification(deployment, request.user)  # Missing data!
```

### 4. Use Proper Target Info

For playbook notifications, provide complete target information:

```python
# ✅ GOOD
target_info = {
    'type': 'host',
    'name': host.hostname
}

# ❌ BAD
target_info = {'type': 'host'}  # Missing name!
```

---

## 🔍 Testing Integration

### 1. Create Test Webhook

1. Go to **Notifications** → **Microsoft Teams**
2. Click **Add Webhook**
3. Use a test webhook URL
4. Enable all notification types
5. Save

### 2. Test Each Integration

**Test Deployment Notification**:
```bash
# Deploy a test VM
# Check Teams channel for notification
# Check Notification Logs
```

**Test Playbook Notification**:
```bash
# Execute a playbook on a host
# Check Teams channel for notification
# Check Notification Logs
```

**Test Scheduled Task Notification**:
```bash
# Create a scheduled task
# Wait for execution
# Check Teams channel for notification
# Check Notification Logs
```

### 3. Verify Logs

After each test:
1. Go to **Notifications** → **Notification Logs**
2. Verify notification was sent
3. Check status (success/failed)
4. Review response message

---

## 🐛 Troubleshooting

### Notification Not Sent

**Check 1**: Webhook is active
```python
from notifications.models import MicrosoftTeamsWebhook
webhooks = MicrosoftTeamsWebhook.objects.filter(active=True)
print(f"Active webhooks: {webhooks.count()}")
```

**Check 2**: Notification type is enabled
```python
webhook = MicrosoftTeamsWebhook.objects.first()
print(f"Deployments: {webhook.notify_deployments}")
print(f"Playbooks: {webhook.notify_playbook_executions}")
print(f"Scheduled: {webhook.notify_scheduled_tasks}")
```

**Check 3**: Not in failures-only mode
```python
webhook = MicrosoftTeamsWebhook.objects.first()
print(f"Failures only: {webhook.notify_failures_only}")
# If True, only failures will be notified
```

### Import Errors

If you get import errors:
```python
# Make sure notifications app is in INSTALLED_APPS
# Check diaken/settings.py
INSTALLED_APPS = [
    # ...
    'notifications',  # Should be here
]
```

### Missing Data Errors

If notification fails due to missing data:
```python
# Check the object has all required fields
print(f"VM Name: {deployment.vm_name}")
print(f"VM IP: {deployment.vm_ip}")
print(f"Status: {deployment.status}")
print(f"Start Time: {deployment.start_time}")
print(f"End Time: {deployment.end_time}")
```

---

## 📊 Example Notification Output

### Deployment Notification

```
✅ VM Deployment Success

VM web-server-01 deployment success

VM Name: web-server-01
IP Address: 10.100.5.89
Template: RedHat-9-Template
Datacenter: DC1
Cluster: Cluster1
Status: Success
Initiated by: admin
Started: 2025-10-14 16:30:00
Completed: 2025-10-14 16:35:00
```

### Playbook Notification

```
✅ Playbook Execution Success

Playbook(s) Update-Redhat-Host, Install-Httpd-Host executed on host

Playbook(s): Update-Redhat-Host, Install-Httpd-Host
Target Type: Host
Target: web-server-01
Status: Success
Initiated by: admin
Started: 2025-10-14 16:40:00
Completed: 2025-10-14 16:42:00
```

### Scheduled Task Notification

```
✅ Scheduled Task Success

Scheduled task Daily Updates executed

Task Name: Daily Updates
Playbook(s): Update-Redhat-Host
Target Type: Group
Group: Production Servers
Status: Success
Started: 2025-10-14 02:00:00
Completed: 2025-10-14 02:15:00
```

---

## 🚀 Quick Integration Checklist

- [ ] Import notification utility function
- [ ] Add try-except block
- [ ] Call notification function after save()
- [ ] Test with active webhook
- [ ] Verify in Teams channel
- [ ] Check notification logs
- [ ] Test failure scenario
- [ ] Test failures-only mode
- [ ] Document integration point
- [ ] Commit changes

---

## 📝 Integration Template

Use this template for any integration:

```python
# 1. Import at top of file
from notifications.utils import send_NOTIFICATION_TYPE_notification

# 2. After operation completes successfully
def your_function(request):
    # ... your code ...
    
    # Save the object
    obj.status = 'success'
    obj.end_time = timezone.now()
    obj.save()
    
    # Send notification (NEW)
    try:
        # Prepare any required data
        # target_info = {...}  # If needed
        
        # Send notification
        send_NOTIFICATION_TYPE_notification(obj, request.user)
        # or with target_info:
        # send_NOTIFICATION_TYPE_notification(obj, request.user, target_info)
    except Exception as e:
        # Log error but don't fail
        print(f"Notification error: {e}")
    
    # ... rest of code ...
```

---

## 🎓 Learning Resources

### Documentation
- `/docs/NOTIFICATIONS_SYSTEM.md` - Complete system documentation
- `/docs/NOTIFICATIONS_IMPLEMENTATION_SUMMARY.md` - Implementation summary
- `/notifications/README.md` - Quick start guide

### Code Examples
- `/notifications/utils.py` - Notification utility functions
- `/notifications/models.py` - Model definitions
- `/notifications/views.py` - View examples

### Testing
- Use webhook.site for testing without Teams
- Check notification logs for debugging
- Test with failures-only mode

---

## ✅ Summary

Integration is simple:
1. Import the utility function
2. Call it after successful operation
3. Wrap in try-except
4. Test and verify

The notification system handles:
- Finding active webhooks
- Checking preferences
- Formatting messages
- Sending to Teams
- Logging results

You just need to call the function! 🎉
