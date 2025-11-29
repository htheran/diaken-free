"""
Utility functions for sending notifications
"""
from .models import MicrosoftTeamsWebhook, NotificationLog
from django.utils import timezone


def send_deployment_notification(deployment, user, os_type='linux'):
    """Send notification for VM deployment
    
    Args:
        deployment: DeploymentHistory instance
        user: User who initiated the deployment
        os_type: 'linux' or 'windows' (default: 'linux')
    """
    # Get active webhooks that should receive deployment notifications
    webhooks = MicrosoftTeamsWebhook.objects.filter(
        active=True,
        notify_deployments=True
    )
    
    # Skip if failures_only and deployment succeeded
    for webhook in webhooks:
        if webhook.notify_failures_only and deployment.status == 'success':
            continue
        
        # Check OS-specific settings
        if os_type == 'linux' and not webhook.notify_linux_deployments:
            continue
        if os_type == 'windows' and not webhook.notify_windows_deployments:
            continue
        
        # Determine color based on status
        color_map = {
            'success': '28A745',  # Green
            'failed': 'DC3545',   # Red
            'running': 'FFC107',  # Yellow
        }
        color = color_map.get(deployment.status, '0078D4')  # Default blue
        
        # Build title
        status_emoji = {
            'success': '✅',
            'failed': '❌',
            'running': '⏳',
        }
        emoji = status_emoji.get(deployment.status, '📋')
        title = f"{emoji} VM Deployment {deployment.status.title()}"
        
        # Build message
        vm_name = deployment.hostname or deployment.target
        message = f"VM **{vm_name}** deployment {deployment.status}"
        
        # Build facts
        facts = [
            {'name': 'VM Name', 'value': vm_name},
            {'name': 'IP Address', 'value': deployment.ip_address or 'N/A'},
            {'name': 'Template', 'value': deployment.template or 'N/A'},
            {'name': 'Datacenter', 'value': deployment.datacenter or 'N/A'},
            {'name': 'Cluster', 'value': deployment.cluster or 'N/A'},
            {'name': 'Environment', 'value': deployment.environment or 'N/A'},
            {'name': 'Status', 'value': deployment.status.title()},
            {'name': 'Initiated by', 'value': user.username if user else 'Unknown'},
            {'name': 'Started', 'value': deployment.created_at.strftime('%Y-%m-%d %H:%M:%S')},
        ]
        
        if deployment.completed_at:
            facts.append({
                'name': 'Completed',
                'value': deployment.completed_at.strftime('%Y-%m-%d %H:%M:%S')
            })
            # Add duration
            duration = deployment.duration()
            if duration != 'In progress':
                facts.append({'name': 'Duration', 'value': duration})
        
        # Send notification
        success, response = webhook.send_notification(
            title=title,
            message=message,
            color=color,
            facts=facts
        )
        
        # Log the notification
        NotificationLog.objects.create(
            webhook=webhook,
            notification_type='deployment',
            title=title,
            message=message,
            status='success' if success else 'failed',
            response_message=response,
            deployment_id=deployment.id
        )


def send_playbook_notification(history, user, target_info, os_type='linux'):
    """Send notification for playbook execution
    
    Args:
        history: DeploymentHistory instance
        user: User who initiated the execution
        target_info: Dict with target information (type, name, etc.)
        os_type: 'linux' or 'windows' (default: 'linux')
    """
    # Get active webhooks that should receive playbook notifications
    webhooks = MicrosoftTeamsWebhook.objects.filter(
        active=True,
        notify_playbook_executions=True
    )
    
    for webhook in webhooks:
        if webhook.notify_failures_only and history.status == 'success':
            continue
        
        # Check OS-specific settings
        if os_type == 'linux' and not webhook.notify_linux_playbooks:
            continue
        if os_type == 'windows' and not webhook.notify_windows_playbooks:
            continue
        
        # Determine color based on status
        color_map = {
            'success': '28A745',  # Green
            'failed': 'DC3545',   # Red
            'running': 'FFC107',  # Yellow
        }
        color = color_map.get(history.status, '0078D4')
        
        # Build title
        status_emoji = {
            'success': '✅',
            'failed': '❌',
            'running': '⏳',
        }
        emoji = status_emoji.get(history.status, '📋')
        title = f"{emoji} Playbook Execution {history.status.title()}"
        
        # Build message
        playbook_names = history.playbook  # DeploymentHistory uses CharField 'playbook'
        message = f"Playbook(s) **{playbook_names}** executed on {target_info.get('type', 'target')}"
        
        # Build facts
        facts = [
            {'name': 'Playbook(s)', 'value': playbook_names},
            {'name': 'Target Type', 'value': target_info.get('type', 'N/A').title()},
            {'name': 'Target', 'value': target_info.get('name', 'N/A')},
            {'name': 'Status', 'value': history.status.title()},
            {'name': 'Initiated by', 'value': user.username},
            {'name': 'Started', 'value': history.created_at.strftime('%Y-%m-%d %H:%M:%S')},
        ]
        
        if history.completed_at:
            facts.append({
                'name': 'Completed',
                'value': history.completed_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        # Send notification
        success, response = webhook.send_notification(
            title=title,
            message=message,
            color=color,
            facts=facts
        )
        
        # Log the notification
        NotificationLog.objects.create(
            webhook=webhook,
            notification_type='playbook',
            title=title,
            message=message,
            status='success' if success else 'failed',
            response_message=response,
            deployment_id=history.id
        )


def send_scheduled_task_notification(task_history, task):
    """Send notification for scheduled task execution
    
    Args:
        task_history: ScheduledTaskHistory instance
        task: ScheduledTask instance
    """
    # Get active webhooks that should receive scheduled task notifications
    webhooks = MicrosoftTeamsWebhook.objects.filter(
        active=True,
        notify_scheduled_tasks=True
    )
    
    for webhook in webhooks:
        if webhook.notify_failures_only and task_history.status == 'success':
            continue
        
        # Determine color based on status
        color_map = {
            'success': '28A745',  # Green
            'failed': 'DC3545',   # Red
            'running': 'FFC107',  # Yellow
        }
        color = color_map.get(task_history.status, '0078D4')
        
        # Build title
        status_emoji = {
            'success': '✅',
            'failed': '❌',
            'running': '⏳',
        }
        emoji = status_emoji.get(task_history.status, '📋')
        title = f"{emoji} Scheduled Task {task_history.status.title()}"
        
        # Build message
        playbook_name = task_history.playbook_name  # ScheduledTaskHistory stores playbook name
        message = f"Scheduled task **{task.name}** executed"
        
        # Build facts
        facts = [
            {'name': 'Task Name', 'value': task.name},
            {'name': 'Playbook/Script', 'value': playbook_name},
            {'name': 'Target Type', 'value': task_history.task_type.title()},
            {'name': 'Target', 'value': task_history.target_name},
            {'name': 'Status', 'value': task_history.status.title()},
            {'name': 'Scheduled For', 'value': task_history.scheduled_for.strftime('%Y-%m-%d %H:%M:%S')},
            {'name': 'Executed At', 'value': task_history.executed_at.strftime('%Y-%m-%d %H:%M:%S')},
        ]
        
        if task_history.execution_duration:
            facts.append({
                'name': 'Duration',
                'value': f'{task_history.execution_duration} seconds'
            })
        
        if task_history.environment_name:
            facts.append({'name': 'Environment', 'value': task_history.environment_name})
        
        # Send notification
        success, response = webhook.send_notification(
            title=title,
            message=message,
            color=color,
            facts=facts
        )
        
        # Log the notification
        NotificationLog.objects.create(
            webhook=webhook,
            notification_type='scheduled_task',
            title=title,
            message=message,
            status='success' if success else 'failed',
            response_message=response,
            scheduled_task_id=task_history.id
        )
