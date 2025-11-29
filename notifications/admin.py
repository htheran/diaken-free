from django.contrib import admin
from .models import MicrosoftTeamsWebhook, NotificationLog


@admin.register(MicrosoftTeamsWebhook)
class MicrosoftTeamsWebhookAdmin(admin.ModelAdmin):
    list_display = ['name', 'active', 'notify_deployments', 'notify_playbook_executions', 
                    'notification_count', 'last_notification_at', 'created_at']
    list_filter = ['active', 'notify_deployments', 'notify_playbook_executions', 'notify_scheduled_tasks']
    search_fields = ['name', 'webhook_url']
    readonly_fields = ['created_at', 'updated_at', 'last_notification_at', 'notification_count']


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ['webhook', 'notification_type', 'title', 'status', 'created_at']
    list_filter = ['notification_type', 'status', 'created_at']
    search_fields = ['title', 'message']
    readonly_fields = ['created_at']
