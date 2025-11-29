from django.db import models
from django.contrib.auth.models import User
from inventory.models import Host, Group
from playbooks.models import Playbook
from django.utils import timezone
from datetime import timedelta


class SnapshotHistory(models.Model):
    """Track all snapshots created by the system"""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('deleted', 'Deleted'),
        ('failed', 'Failed'),
    ]
    
    # Snapshot identification
    snapshot_name = models.CharField(max_length=255)
    vcenter_snapshot_id = models.CharField(max_length=100, blank=True, null=True)
    
    # Related objects
    host = models.ForeignKey(Host, on_delete=models.CASCADE, related_name='snapshots')
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True, related_name='snapshots')
    playbook = models.ForeignKey(Playbook, on_delete=models.SET_NULL, null=True, blank=True)
    script_name = models.CharField(max_length=255, blank=True, null=True, help_text='Name of script if executed via script')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Snapshot details
    description = models.TextField(blank=True)
    size_mb = models.IntegerField(default=0, help_text='Snapshot size in MB')
    
    # Timing information
    created_at = models.DateTimeField(auto_now_add=True)
    retention_hours = models.IntegerField(default=24, help_text='Hours to keep snapshot before auto-deletion')
    expires_at = models.DateTimeField(help_text='When snapshot will be auto-deleted')
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Snapshot History'
        verbose_name_plural = 'Snapshot Histories'
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['host']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"{self.snapshot_name} - {self.host.name}"
    
    def save(self, *args, **kwargs):
        # Calculate expiration time if not set
        if not self.expires_at:
            # If this is a new object, created_at will be set by auto_now_add
            # So we calculate expires_at based on current time
            if not self.pk:  # New object
                self.expires_at = timezone.now() + timedelta(hours=self.retention_hours)
            elif self.created_at:  # Existing object
                self.expires_at = self.created_at + timedelta(hours=self.retention_hours)
        super().save(*args, **kwargs)
    
    def is_expired(self):
        """Check if snapshot has expired"""
        return timezone.now() >= self.expires_at
    
    def time_until_deletion(self):
        """Get time remaining until deletion"""
        if self.status != 'active':
            return None
        delta = self.expires_at - timezone.now()
        if delta.total_seconds() < 0:
            return "Expired"
        hours = int(delta.total_seconds() / 3600)
        minutes = int((delta.total_seconds() % 3600) / 60)
        return f"{hours}h {minutes}m"
    
    def mark_as_deleted(self):
        """Mark snapshot as deleted"""
        self.status = 'deleted'
        self.deleted_at = timezone.now()
        self.save()
