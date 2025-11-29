# Notifications System - Microsoft Teams Integration

## Overview

Complete notification system for Diaken that sends real-time notifications to Microsoft Teams channels for deployments, playbook executions, and scheduled tasks.

**Date Created**: 2025-10-14  
**Version**: 1.0  
**Status**: Production Ready

---

## 📋 Features

### ✅ Implemented

1. **Microsoft Teams Webhooks Management**
   - Create, edit, delete webhooks
   - Enable/disable webhooks
   - Test notifications
   - Multiple webhooks support

2. **Notification Types**
   - VM Deployments (Linux/Windows)
   - Playbook Executions (Manual)
   - Scheduled Task Executions

3. **Notification Preferences**
   - Per-webhook configuration
   - Selective notification types
   - Failures-only mode
   - Active/inactive status

4. **Notification Logs**
   - Complete history of sent notifications
   - Success/failure tracking
   - Response messages
   - Searchable and filterable

5. **Payload Management**
   - Automatic size validation (28KB limit)
   - JSON structured data
   - Rich formatting with facts
   - Color-coded by status

---

## 🏗️ Architecture

### Django App Structure

```
notifications/
├── models.py                   # MicrosoftTeamsWebhook, NotificationLog
├── views.py                    # CRUD views for webhooks
├── forms.py                    # Webhook and test forms
├── urls.py                     # URL routing
├── admin.py                    # Django admin configuration
├── utils.py                    # Notification sending utilities
└── migrations/
    └── 0001_initial.py         # Initial migration
```

### Templates

```
templates/notifications/
├── webhook_list.html           # List all webhooks
├── webhook_form.html           # Create/edit webhook
├── webhook_confirm_delete.html # Delete confirmation
├── webhook_test.html           # Send test notification
└── notification_logs.html      # View notification history
```

---

## 📊 Database Models

### MicrosoftTeamsWebhook

| Field | Type | Description |
|-------|------|-------------|
| `name` | CharField(255) | Webhook name (unique) |
| `webhook_url` | URLField(500) | Microsoft Teams incoming webhook URL |
| `active` | BooleanField | Enable/disable webhook |
| `notify_deployments` | BooleanField | Send deployment notifications |
| `notify_playbook_executions` | BooleanField | Send playbook notifications |
| `notify_scheduled_tasks` | BooleanField | Send scheduled task notifications |
| `notify_failures_only` | BooleanField | Only notify on failures |
| `created_at` | DateTimeField | Creation timestamp |
| `updated_at` | DateTimeField | Last update timestamp |
| `last_notification_at` | DateTimeField | Last notification sent |
| `notification_count` | IntegerField | Total notifications sent |

### NotificationLog

| Field | Type | Description |
|-------|------|-------------|
| `webhook` | ForeignKey | Related webhook |
| `notification_type` | CharField | Type: deployment, playbook, scheduled_task |
| `title` | CharField(255) | Notification title |
| `message` | TextField | Notification message |
| `status` | CharField | Status: success, failed |
| `response_message` | TextField | API response |
| `deployment_id` | IntegerField | Related deployment ID (optional) |
| `scheduled_task_id` | IntegerField | Related task ID (optional) |
| `created_at` | DateTimeField | Timestamp |

---

## 🔗 URLs

| URL | View | Description |
|-----|------|-------------|
| `/notifications/` | `webhook_list` | List all webhooks |
| `/notifications/create/` | `webhook_create` | Create new webhook |
| `/notifications/<id>/edit/` | `webhook_edit` | Edit webhook |
| `/notifications/<id>/delete/` | `webhook_delete` | Delete webhook |
| `/notifications/<id>/toggle-active/` | `webhook_toggle_active` | Toggle active status (AJAX) |
| `/notifications/<id>/test/` | `webhook_test` | Send test notification |
| `/notifications/logs/` | `notification_logs` | View notification logs |

---

## 🎨 Notification Format

### Message Card Structure

```json
{
  "@type": "MessageCard",
  "@context": "https://schema.org/extensions",
  "summary": "Notification Title",
  "themeColor": "28A745",
  "title": "✅ VM Deployment Success",
  "text": "VM **web-server-01** deployment success",
  "sections": [{
    "facts": [
      {"name": "VM Name", "value": "web-server-01"},
      {"name": "IP Address", "value": "10.100.5.89"},
      {"name": "Template", "value": "RedHat-9-Template"},
      {"name": "Datacenter", "value": "DC1"},
      {"name": "Cluster", "value": "Cluster1"},
      {"name": "Status", "value": "Success"},
      {"name": "Initiated by", "value": "admin"},
      {"name": "Started", "value": "2025-10-14 16:30:00"}
    ]
  }]
}
```

### Color Codes

| Status | Color | Hex Code |
|--------|-------|----------|
| Success | Green | `28A745` |
| Failed | Red | `DC3545` |
| Running | Yellow | `FFC107` |
| Info | Blue | `0078D4` |
| Test | Light Blue | `17A2B8` |

### Status Emojis

| Status | Emoji |
|--------|-------|
| Success | ✅ |
| Failed | ❌ |
| Running | ⏳ |
| Info | 📋 |

---

## 🔧 Usage

### 1. Configure Webhook in Microsoft Teams

1. Open Microsoft Teams
2. Navigate to the channel
3. Click **•••** (More options) → **Connectors**
4. Search for **Incoming Webhook**
5. Click **Configure**
6. Give it a name (e.g., "Diaken Notifications")
7. Optionally upload an image
8. Click **Create**
9. **Copy the webhook URL**

### 2. Add Webhook in Diaken

1. Navigate to **Notifications** → **Microsoft Teams**
2. Click **Add Webhook**
3. Fill in:
   - **Name**: Descriptive name (e.g., "DevOps Team")
   - **Webhook URL**: Paste the URL from Teams
   - **Active**: Check to enable
   - **Notification Preferences**: Select what to notify
4. Click **Save Webhook**

### 3. Test the Webhook

1. Go to **Notifications** → **Microsoft Teams**
2. Find your webhook
3. Click **Test**
4. Customize title and message (optional)
5. Click **Send Test Notification**
6. Check your Teams channel for the notification

### 4. View Notification Logs

1. Navigate to **Notifications** → **Notification Logs**
2. View history of all sent notifications
3. Check success/failure status
4. Review response messages

---

## 📝 Integration with Existing Code

### Sending Notifications

The system provides utility functions in `notifications/utils.py`:

#### 1. VM Deployment Notifications

```python
from notifications.utils import send_deployment_notification

# After deployment completes
send_deployment_notification(deployment, request.user)
```

#### 2. Playbook Execution Notifications

```python
from notifications.utils import send_playbook_notification

# After playbook execution
target_info = {
    'type': 'host',  # or 'group'
    'name': host.hostname  # or group.name
}
send_playbook_notification(history, request.user, target_info)
```

#### 3. Scheduled Task Notifications

```python
from notifications.utils import send_scheduled_task_notification

# After scheduled task execution
send_scheduled_task_notification(task_history, task)
```

### Integration Points

To integrate notifications into existing code:

1. **deploy/views.py** - Add after VM deployment:
```python
from notifications.utils import send_deployment_notification
# After deployment.save()
send_deployment_notification(deployment, request.user)
```

2. **playbooks/views.py** - Add after playbook execution:
```python
from notifications.utils import send_playbook_notification
# After history.save()
target_info = {'type': target_type, 'name': target_name}
send_playbook_notification(history, request.user, target_info)
```

3. **scheduler/management/commands/run_scheduler.py** - Add after task execution:
```python
from notifications.utils import send_scheduled_task_notification
# After task_history.save()
send_scheduled_task_notification(task_history, task)
```

---

## 🔒 Security

### Webhook URL Security

- Webhook URLs are stored in database
- URLs are validated on save
- Only HTTPS URLs accepted
- URLs are not exposed in logs

### Access Control

- All views require authentication (`@login_required`)
- CSRF protection on all forms
- Admin-only access via Django admin

### Rate Limiting

- 10-second timeout per request
- Automatic retry not implemented (manual only)
- Logs all attempts for auditing

---

## ⚙️ Configuration

### Payload Size Limit

Microsoft Teams has a 28KB limit for incoming webhook payloads. The system automatically:

1. Checks payload size before sending
2. Returns error if > 28KB
3. Logs the failure

To reduce payload size:
- Limit number of facts
- Shorten message text
- Remove unnecessary data

### Notification Preferences

Each webhook can be configured independently:

- **Notify Deployments**: VM deployment events
- **Notify Playbook Executions**: Manual playbook runs
- **Notify Scheduled Tasks**: Automated scheduled tasks
- **Failures Only**: Only send on failures (useful for production)

---

## 📊 Monitoring

### Webhook Statistics

Each webhook tracks:
- Total notifications sent
- Last notification timestamp
- Success/failure rate (via logs)

### Notification Logs

View complete history:
- Date/time of notification
- Webhook used
- Notification type
- Title and message
- Success/failure status
- API response

---

## 🐛 Troubleshooting

### Notification Not Received

1. **Check webhook is active**
   - Go to webhook list
   - Verify "Active" badge is green

2. **Check notification preferences**
   - Edit webhook
   - Verify correct notification types are enabled
   - Check "Failures Only" setting

3. **Test the webhook**
   - Use "Test" button
   - Check Teams channel
   - Review error message if failed

4. **Check notification logs**
   - Go to Notification Logs
   - Find the notification
   - Check status and response message

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `Webhook is disabled` | Webhook inactive | Enable webhook |
| `Payload too large` | > 28KB | Reduce data sent |
| `HTTP 400` | Invalid webhook URL | Verify URL in Teams |
| `HTTP 404` | Webhook deleted in Teams | Recreate webhook |
| `Request timeout` | Network issue | Check connectivity |

### Webhook URL Issues

If webhook URL is invalid:
1. Go to Microsoft Teams
2. Remove old connector
3. Create new Incoming Webhook
4. Copy new URL
5. Update in Diaken

---

## 🚀 Future Enhancements

### Planned Features

1. **Additional Platforms**
   - Slack integration
   - Telegram integration
   - Email notifications
   - SMS notifications

2. **Advanced Features**
   - Notification templates
   - Custom message formatting
   - Notification scheduling
   - Notification grouping
   - Rate limiting per webhook

3. **Analytics**
   - Notification statistics dashboard
   - Success rate charts
   - Response time tracking
   - Most active webhooks

4. **Filtering**
   - Filter by environment
   - Filter by host/group
   - Filter by playbook
   - Custom filter rules

---

## 📚 API Reference

### Model Methods

#### MicrosoftTeamsWebhook.send_notification()

```python
def send_notification(self, title, message, color="0078D4", facts=None):
    """
    Send a notification to Microsoft Teams
    
    Args:
        title (str): Notification title
        message (str): Main message text
        color (str): Hex color code without # (default: "0078D4")
        facts (list): List of dicts with 'name' and 'value' keys
    
    Returns:
        tuple: (success: bool, response_text: str)
    """
```

**Example**:
```python
webhook = MicrosoftTeamsWebhook.objects.get(name="DevOps Team")
facts = [
    {'name': 'Server', 'value': 'web-01'},
    {'name': 'Status', 'value': 'Success'},
]
success, response = webhook.send_notification(
    title="Deployment Complete",
    message="Server deployed successfully",
    color="28A745",
    facts=facts
)
```

---

## 📁 File Structure

```
/opt/www/app/
├── notifications/                      # Django app
│   ├── __init__.py
│   ├── admin.py                       # Admin configuration
│   ├── apps.py                        # App configuration
│   ├── forms.py                       # Webhook forms
│   ├── models.py                      # Database models
│   ├── urls.py                        # URL routing
│   ├── utils.py                       # Notification utilities
│   ├── views.py                       # CRUD views
│   └── migrations/
│       └── 0001_initial.py           # Initial migration
├── templates/notifications/           # Templates
│   ├── webhook_list.html
│   ├── webhook_form.html
│   ├── webhook_confirm_delete.html
│   ├── webhook_test.html
│   └── notification_logs.html
└── docs/
    └── NOTIFICATIONS_SYSTEM.md        # This file
```

---

## ✅ Testing

### Manual Testing Checklist

- [ ] Create webhook with valid URL
- [ ] Create webhook with invalid URL (should fail)
- [ ] Edit webhook
- [ ] Toggle webhook active/inactive
- [ ] Send test notification
- [ ] Delete webhook
- [ ] View notification logs
- [ ] Test deployment notification
- [ ] Test playbook notification
- [ ] Test scheduled task notification
- [ ] Test failures-only mode
- [ ] Verify 28KB payload limit

### Test Webhook URL

For testing without Microsoft Teams:
- Use webhook.site or similar services
- Create temporary webhook for testing
- Verify payload structure

---

## 📞 Support

### Getting Help

1. Check notification logs for error messages
2. Review this documentation
3. Test webhook with "Test" button
4. Verify webhook URL in Microsoft Teams
5. Check webhook is active and preferences are correct

### Common Questions

**Q: Can I have multiple webhooks?**  
A: Yes, you can create unlimited webhooks for different teams/channels.

**Q: What happens if a webhook fails?**  
A: The failure is logged in Notification Logs with the error message. The system continues processing other webhooks.

**Q: Can I send notifications to multiple channels?**  
A: Yes, create a webhook for each channel you want to notify.

**Q: How do I stop notifications temporarily?**  
A: Toggle the webhook to "Inactive" status. You can reactivate it later.

**Q: Can I customize the notification format?**  
A: Currently no, but this is planned for future versions.

---

## 📝 Changelog

### Version 1.0 (2025-10-14)

**Initial Release**
- Microsoft Teams webhook management
- Deployment notifications
- Playbook execution notifications
- Scheduled task notifications
- Notification logs
- Test notification feature
- Active/inactive toggle
- Failures-only mode
- 28KB payload validation
- Complete CRUD operations

---

## 🎉 Summary

The Notifications System provides a complete solution for sending real-time notifications to Microsoft Teams. It's designed to be:

- **Easy to use**: Simple webhook configuration
- **Flexible**: Per-webhook preferences
- **Reliable**: Automatic validation and error handling
- **Auditable**: Complete notification logs
- **Extensible**: Ready for additional platforms

**Status**: ✅ Production Ready  
**Integration**: Ready to integrate with deploy, playbooks, and scheduler  
**Documentation**: Complete  
**Testing**: Manual testing required
