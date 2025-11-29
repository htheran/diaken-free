from django.db import models
from django.core.exceptions import ValidationError
import os
from django.conf import settings


class Script(models.Model):
    """Model to store scripts for execution on hosts or groups"""
    
    TARGET_TYPE_CHOICES = [
        ('host', 'Host'),
        ('group', 'Group'),
    ]
    
    OS_FAMILY_CHOICES = [
        ('redhat', 'RedHat/CentOS/Oracle Linux'),
        ('debian', 'Debian/Ubuntu'),
        ('windows', 'Windows'),
    ]
    
    name = models.CharField(max_length=255, help_text="Script name (without extension)")
    description = models.TextField(blank=True, help_text="Description of what the script does")
    target_type = models.CharField(max_length=10, choices=TARGET_TYPE_CHOICES, help_text="Execute on single host or group")
    os_family = models.CharField(max_length=20, choices=OS_FAMILY_CHOICES, help_text="Operating system family")
    file_path = models.CharField(max_length=500, help_text="Path to script file")
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['os_family', 'target_type', 'name']
        unique_together = ['name', 'target_type', 'os_family']
    
    def __str__(self):
        return f"{self.name} ({self.get_os_family_display()} - {self.get_target_type_display()})"
    
    def get_extension(self):
        """Get the appropriate file extension based on OS family"""
        if self.os_family == 'windows':
            return '.ps1'
        else:  # redhat or debian
            return '.sh'
    
    def get_full_filename(self):
        """Get the full filename with extension"""
        return f"{self.name}{self.get_extension()}"
    
    def get_directory_path(self):
        """Get the directory path based on os_family and target_type"""
        base_path = settings.SCRIPTS_ROOT
        
        
        if self.os_family == 'windows':
            os_dir = 'powershell'
        else:
            os_dir = self.os_family        
        
        return os.path.join(str(base_path), os_dir, self.target_type)
    
    def get_full_path(self):
        """Get the complete file path"""
        return os.path.join(self.get_directory_path(), self.get_full_filename())
    
    def save(self, *args, **kwargs):
        """Override save to set file_path automatically"""
        self.file_path = self.get_full_path()
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Override delete to also remove the file"""
        if os.path.exists(self.file_path):
            os.remove(self.file_path)
        super().delete(*args, **kwargs)
    
    def clean(self):
        """Validate the model"""
        # Ensure name doesn't contain invalid characters
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in invalid_chars:
            if char in self.name:
                raise ValidationError(f"Script name cannot contain '{char}'")
