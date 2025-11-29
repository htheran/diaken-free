from django.db import models
from django.core.validators import URLValidator
from django.utils import timezone
import requests
import json


class MicrosoftTeamsWebhook(models.Model):
    """Microsoft Teams Incoming Webhook configuration"""
    
    name = models.CharField(
        max_length=255,
        unique=True,
        help_text="Descriptive name for this webhook (e.g., 'DevOps Team', 'Production Alerts')"
    )
    
    webhook_url = models.URLField(
        max_length=500,
        validators=[URLValidator()],
        help_text="Microsoft Teams Incoming Webhook URL"
    )
    
    active = models.BooleanField(
        default=True,
        help_text="Enable/disable this webhook"
    )
    
    # Notification preferences - General
    notify_failures_only = models.BooleanField(
        default=False,
        help_text="Only send notifications for failed executions (applies to all types)"
    )
    
    # VM Deployments
    notify_deployments = models.BooleanField(
        default=True,
        help_text="Send notifications for VM deployments"
    )
    notify_linux_deployments = models.BooleanField(
        default=True,
        help_text="Send notifications for Linux VM deployments"
    )
    notify_windows_deployments = models.BooleanField(
        default=True,
        help_text="Send notifications for Windows VM deployments"
    )
    
    # Playbook Executions
    notify_playbook_executions = models.BooleanField(
        default=True,
        help_text="Send notifications for playbook executions"
    )
    notify_linux_playbooks = models.BooleanField(
        default=True,
        help_text="Send notifications for Linux playbook executions"
    )
    notify_windows_playbooks = models.BooleanField(
        default=True,
        help_text="Send notifications for Windows playbook executions"
    )
    
    # Scheduled Tasks
    notify_scheduled_tasks = models.BooleanField(
        default=True,
        help_text="Send notifications for scheduled task executions"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_notification_at = models.DateTimeField(null=True, blank=True)
    notification_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Microsoft Teams Webhook"
        verbose_name_plural = "Microsoft Teams Webhooks"
    
    def __str__(self):
        return f"{self.name} ({'Active' if self.active else 'Inactive'})"
    
    def send_notification(self, title, message, color="0078D4", facts=None):
        """Send a notification to Microsoft Teams
        
        Args:
            title: Notification title
            message: Main message text
            color: Hex color code (without #)
            facts: List of dicts with 'name' and 'value' keys
        
        Returns:
            tuple: (success: bool, response_text: str)
        """
        if not self.active:
            return False, "Webhook is disabled"
        
        # Build the adaptive card payload
        payload = {
            "@type": "MessageCard",
            "@context": "https://schema.org/extensions",
            "summary": title,
            "themeColor": color,
            "title": title,
            "text": message,
            "activityTitle": "Diaken Automation Platform",
            "activitySubtitle": "Automated Notification",
            "activityImage": "https://raw.githubusercontent.com/ansible/logos/main/vscode-ansible-logo.png"
        }
        
        # Add facts if provided
        if facts:
            payload["sections"] = [{
                "facts": facts
            }]
        
        # Check payload size (Microsoft Teams limit is 28KB)
        payload_json = json.dumps(payload)
        payload_size = len(payload_json.encode('utf-8'))
        
        if payload_size > 28000:  # 28KB limit
            return False, f"Payload too large: {payload_size} bytes (max 28000)"
        
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            # Update metadata
            self.last_notification_at = timezone.now()
            self.notification_count += 1
            self.save(update_fields=['last_notification_at', 'notification_count'])
            
            if response.status_code == 200:
                return True, "Notification sent successfully"
            else:
                return False, f"HTTP {response.status_code}: {response.text}"
                
        except requests.exceptions.Timeout:
            return False, "Request timeout"
        except requests.exceptions.RequestException as e:
            return False, f"Request error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"


class NotificationLog(models.Model):
    """Log of sent notifications"""
    
    NOTIFICATION_TYPES = [
        ('deployment', 'VM Deployment'),
        ('playbook', 'Playbook Execution'),
        ('scheduled_task', 'Scheduled Task'),
    ]
    
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]
    
    webhook = models.ForeignKey(
        MicrosoftTeamsWebhook,
        on_delete=models.CASCADE,
        related_name='logs'
    )
    
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES
    )
    
    title = models.CharField(max_length=255)
    message = models.TextField()
    
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES
    )
    
    response_message = models.TextField(blank=True)
    
    # Reference to the related object
    deployment_id = models.IntegerField(null=True, blank=True)
    scheduled_task_id = models.IntegerField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Notification Log"
        verbose_name_plural = "Notification Logs"
    
    def __str__(self):
        return f"{self.notification_type} - {self.title} ({self.status})"
