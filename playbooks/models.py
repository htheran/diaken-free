from django.db import models
import os

def playbook_upload_path(instance, filename):
    """Determine upload path based on playbook type"""
    return f'playbooks/{instance.playbook_type}/{filename}'

class Playbook(models.Model):
    PLAYBOOK_TYPE_CHOICES = [
        ('host', 'Host'),
        ('group', 'Group'),
    ]
    
    OS_FAMILY_CHOICES = [
        ('redhat', 'RedHat/CentOS'),
        ('debian', 'Debian/Ubuntu'),
        ('windows', 'Windows'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    playbook_type = models.CharField(max_length=10, choices=PLAYBOOK_TYPE_CHOICES, default='host')
    os_family = models.CharField(max_length=10, choices=OS_FAMILY_CHOICES, default='redhat')
    file = models.FileField(upload_to=playbook_upload_path)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['playbook_type', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.playbook_type})"
    
    def save(self, *args, **kwargs):
        # upload_to ya maneja la ruta correcta automáticamente
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        # Eliminar el archivo físico al borrar el registro
        if self.file:
            try:
                # Intentar eliminar el archivo si existe
                if os.path.isfile(self.file.path):
                    os.remove(self.file.path)
            except Exception as e:
                # Si hay error al eliminar el archivo, continuar con la eliminación del registro
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Could not delete file {self.file.path}: {e}")
        super().delete(*args, **kwargs)
