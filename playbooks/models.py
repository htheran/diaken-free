from django.db import models
from django.conf import settings
import os

def playbook_upload_path(instance, filename):
    """Determine upload path based on OS family and playbook type"""
    # Structure: playbooks/{os_family}/{target_type}/{filename}
    return f'playbooks/{instance.os_family}/{instance.playbook_type}/{filename}'

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
    
    def get_directory_path(self):
        """Get the absolute directory path for this playbook"""
        return os.path.join(
            str(settings.MEDIA_ROOT),
            'playbooks',
            self.os_family,
            self.playbook_type
        )
    
    def get_absolute_path(self):
        """Get the absolute file path for this playbook"""
        if self.file:
            return os.path.join(str(settings.MEDIA_ROOT), str(self.file))
        return None
    
    def save(self, *args, **kwargs):
        # Ensure directory exists before saving
        if self.file:
            directory = self.get_directory_path()
            os.makedirs(directory, exist_ok=True)
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
