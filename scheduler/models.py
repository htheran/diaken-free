from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from inventory.models import Environment, Group, Host
from playbooks.models import Playbook

class ScheduledTask(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    TASK_TYPE_CHOICES = [
        ('host', 'Execute on Host'),
        ('group', 'Execute on Group'),
    ]
    
    # Task information
    task_type = models.CharField(max_length=10, choices=TASK_TYPE_CHOICES)
    name = models.CharField(max_length=200, help_text='Task name/description')
    
    # User who created the task
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='scheduled_tasks')
    
    # Target information
    environment = models.ForeignKey(Environment, on_delete=models.CASCADE, null=True, blank=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True)
    host = models.ForeignKey(Host, on_delete=models.CASCADE, null=True, blank=True)
    
    # Playbook to execute (optional for script execution)
    playbook = models.ForeignKey(Playbook, on_delete=models.CASCADE, null=True, blank=True)
    
    # Script execution support
    script = models.ForeignKey('scripts.Script', on_delete=models.CASCADE, null=True, blank=True, help_text='Script to execute (for script execution)')
    execution_type = models.CharField(max_length=20, default='playbook', help_text='Type of execution: playbook or script')
    os_family = models.CharField(max_length=20, null=True, blank=True, help_text='OS family: redhat, debian, or windows')
    
    # Snapshot option
    create_snapshot = models.BooleanField(default=False, help_text='Create snapshot before execution')
    snapshot_created = models.BooleanField(default=False, help_text='Whether snapshot has been created (for scheduled tasks)')
    snapshot_name = models.CharField(max_length=500, null=True, blank=True, help_text='Name of the created snapshot')
    
    # Scheduling information
    scheduled_datetime = models.DateTimeField(help_text='When to execute this task')
    
    # Status and execution
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    execution_started_at = models.DateTimeField(null=True, blank=True)
    execution_completed_at = models.DateTimeField(null=True, blank=True)
    
    # Results
    deployment_history_id = models.IntegerField(null=True, blank=True, help_text='ID of DeploymentHistory record (deprecated, use scheduled_task_history_id)')
    scheduled_task_history_id = models.IntegerField(null=True, blank=True, help_text='ID of ScheduledTaskHistory record')
    error_message = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-scheduled_datetime']
        indexes = [
            models.Index(fields=['status', 'scheduled_datetime']),
            models.Index(fields=['task_type']),
        ]
    
    def __str__(self):
        target = self.host.name if self.host else (self.group.name if self.group else 'Unknown')
        return f"{self.name} - {target} - {self.scheduled_datetime}"
    
    def get_target_display(self):
        """Return human-readable target"""
        if self.task_type == 'host' and self.host:
            return f"Host: {self.host.name}"
        elif self.task_type == 'group' and self.group:
            return f"Group: {self.group.name}"
        return "Unknown"


class ScheduledTaskHistory(models.Model):
    """History of scheduled task executions"""
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]
    
    # Link to scheduled task
    scheduled_task = models.ForeignKey(ScheduledTask, on_delete=models.CASCADE, related_name='executions')
    
    # Execution information
    scheduled_for = models.DateTimeField(default=timezone.now, help_text='Original scheduled datetime')
    executed_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    
    # Target information (copied from task for historical record)
    task_type = models.CharField(max_length=10)
    target_name = models.CharField(max_length=200, help_text='Host or Group name')
    target_ip = models.CharField(max_length=200, blank=True, help_text='IP address(es)')
    playbook_name = models.CharField(max_length=200)
    environment_name = models.CharField(max_length=100, blank=True)
    
    # Execution output
    ansible_output = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    
    # Execution time
    execution_duration = models.IntegerField(null=True, blank=True, help_text='Duration in seconds')
    
    class Meta:
        ordering = ['-executed_at']
        verbose_name = 'Scheduled Task History'
        verbose_name_plural = 'Scheduled Task Histories'
    
    def __str__(self):
        return f"{self.scheduled_task.name} - {self.target_name} - {self.executed_at}"
    
    def get_status_badge(self):
        """Return HTML badge for status"""
        if self.status == 'success':
            return '<span class="badge badge-success">Success</span>'
        else:
            return '<span class="badge badge-danger">Failed</span>'
