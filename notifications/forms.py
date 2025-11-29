from django import forms
from .models import MicrosoftTeamsWebhook


class MicrosoftTeamsWebhookForm(forms.ModelForm):
    """Form for creating/editing Microsoft Teams webhooks"""
    
    class Meta:
        model = MicrosoftTeamsWebhook
        fields = [
            'name',
            'webhook_url',
            'active',
            'notify_deployments',
            'notify_playbook_executions',
            'notify_scheduled_tasks',
            'notify_failures_only',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., DevOps Team, Production Alerts'
            }),
            'webhook_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://outlook.office.com/webhook/...'
            }),
            'active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'notify_deployments': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'notify_playbook_executions': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'notify_scheduled_tasks': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'notify_failures_only': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'name': 'Webhook Name',
            'webhook_url': 'Incoming Webhook URL',
            'active': 'Active',
            'notify_deployments': 'VM Deployments',
            'notify_playbook_executions': 'Playbook Executions',
            'notify_scheduled_tasks': 'Scheduled Tasks',
            'notify_failures_only': 'Failures Only',
        }
        help_texts = {
            'name': 'A descriptive name to identify this webhook',
            'webhook_url': 'Get this URL from Microsoft Teams channel connectors',
            'active': 'Enable or disable this webhook',
            'notify_deployments': 'Send notifications for VM deployment events',
            'notify_playbook_executions': 'Send notifications for playbook execution events',
            'notify_scheduled_tasks': 'Send notifications for scheduled task events',
            'notify_failures_only': 'Only send notifications when executions fail',
        }
    
    def clean_webhook_url(self):
        """Validate that the webhook URL is a Microsoft Teams URL"""
        url = self.cleaned_data.get('webhook_url')
        if url and 'webhook' not in url.lower():
            raise forms.ValidationError(
                'This does not appear to be a valid webhook URL. '
                'Please check the URL from Microsoft Teams.'
            )
        return url


class TestNotificationForm(forms.Form):
    """Form for sending test notifications"""
    
    title = forms.CharField(
        max_length=255,
        initial='Test Notification',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Test Notification'
        })
    )
    
    message = forms.CharField(
        initial='This is a test notification from Diaken.',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Test message...'
        })
    )
