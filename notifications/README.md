# Notifications App

Django app for managing notifications to external platforms.

## Current Support

- **Microsoft Teams**: Incoming webhooks

## Features

- ✅ CRUD operations for webhooks
- ✅ Test notifications
- ✅ Notification logs
- ✅ Active/inactive toggle
- ✅ Configurable notification types
- ✅ Failures-only mode
- ✅ 28KB payload validation

## Quick Start

### 1. Get Webhook URL from Microsoft Teams

1. Open Teams → Channel → **•••** → **Connectors**
2. Configure **Incoming Webhook**
3. Copy the URL

### 2. Add Webhook in Diaken

Navigate to **Notifications** → **Microsoft Teams** → **Add Webhook**

### 3. Send Notifications

```python
from notifications.utils import send_deployment_notification

# After deployment
send_deployment_notification(deployment, request.user)
```

## Documentation

See `/docs/NOTIFICATIONS_SYSTEM.md` for complete documentation.

## Models

- `MicrosoftTeamsWebhook`: Webhook configuration
- `NotificationLog`: Notification history

## URLs

- `/notifications/` - List webhooks
- `/notifications/create/` - Create webhook
- `/notifications/<id>/edit/` - Edit webhook
- `/notifications/<id>/delete/` - Delete webhook
- `/notifications/<id>/test/` - Test webhook
- `/notifications/logs/` - View logs

## Future Platforms

- Slack
- Telegram
- Email
- SMS
