from django.db import models
from django.contrib.auth.models import User

class DeploymentHistory(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    environment = models.CharField(max_length=100)
    target = models.CharField(max_length=200)  # Hostname o nombre del objetivo
    target_type = models.CharField(max_length=50, default='VM')  # VM, Host, Group
    playbook = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='running')
    ansible_output = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Datos adicionales del deploy
    hostname = models.CharField(max_length=100, blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    mac_address = models.CharField(max_length=17, blank=True, null=True)
    datacenter = models.CharField(max_length=100, blank=True, null=True)
    cluster = models.CharField(max_length=100, blank=True, null=True)
    template = models.CharField(max_length=100, blank=True, null=True)
    snapshot_name = models.CharField(max_length=255, blank=True, null=True, help_text='Nombre del snapshot creado antes de ejecutar el playbook')
    celery_task_id = models.CharField(max_length=255, blank=True, null=True, help_text='ID de la tarea Celery para tareas asíncronas')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Deployment History'
        verbose_name_plural = 'Deployment Histories'
    
    def __str__(self):
        return f"{self.user.username if self.user else 'Unknown'} - {self.target} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    def duration(self):
        if self.completed_at:
            delta = self.completed_at - self.created_at
            return str(delta).split('.')[0]  # Remove microseconds
        return 'In progress'
