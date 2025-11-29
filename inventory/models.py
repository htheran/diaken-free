from django.db import models
from django.utils.translation import gettext_lazy as _

class Environment(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name=_('Name'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    active = models.BooleanField(default=True, verbose_name=_('Active'))
    def __str__(self):
        return self.name

class Group(models.Model):
    name = models.CharField(max_length=100, verbose_name=_('Name'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    environment = models.ForeignKey(Environment, on_delete=models.CASCADE, related_name='groups', verbose_name=_('Environment'))
    active = models.BooleanField(default=True, verbose_name=_('Active'))
    def __str__(self):
        return self.name

from settings.models import DeploymentCredential, WindowsCredential

class Host(models.Model):
    OPERATING_SYSTEM_CHOICES = [
        ('redhat', _('Redhat')),
        ('debian', _('Debian')),
        ('windows', _('Windows')),
    ]
    name = models.CharField(max_length=100, verbose_name=_('Name'))
    ip = models.GenericIPAddressField(verbose_name=_('IP Address'))
    vcenter_server = models.CharField(max_length=200, blank=True, verbose_name=_('vCenter Server'), help_text=_('vCenter server managing this VM'))
    environment = models.ForeignKey(Environment, on_delete=models.CASCADE, related_name='hosts', verbose_name=_('Environment'))
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True, related_name='hosts', verbose_name=_('Group'))
    operating_system = models.CharField(max_length=30, choices=OPERATING_SYSTEM_CHOICES, default='linux', verbose_name=_('Operating System'))
    ansible_python_interpreter = models.CharField(max_length=200, blank=True, verbose_name=_('Ansible Python Interpreter'))
    deployment_credential = models.ForeignKey(DeploymentCredential, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('Deployment Credential'))
    windows_credential = models.ForeignKey(WindowsCredential, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('Windows Credential'))
    windows_user = models.CharField(max_length=100, blank=True, verbose_name=_('Windows User'), help_text=_('WinRM username for Windows hosts'))
    windows_password = models.CharField(max_length=200, blank=True, verbose_name=_('Windows Password'), help_text=_('WinRM password for Windows hosts'))
    ansible_user = models.CharField(max_length=100, blank=True, verbose_name=_('Ansible User'))
    ansible_password = models.CharField(max_length=100, blank=True, verbose_name=_('Ansible Password'))
    ansible_port = models.PositiveIntegerField(null=True, blank=True, verbose_name=_('Ansible Port'))
    ansible_ssh_private_key_file = models.CharField(max_length=200, blank=True, verbose_name=_('Ansible SSH Private Key File'))
    ansible_ssh_common_args = models.CharField(max_length=200, blank=True, verbose_name=_('Ansible SSH Common Args'))
    status = models.CharField(max_length=50, blank=True, verbose_name=_('Status'))
    tags = models.CharField(max_length=200, blank=True, verbose_name=_('Tags'))
    notes = models.TextField(blank=True, verbose_name=_('Notes'))
    active = models.BooleanField(default=True, verbose_name=_('Active'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    
    def __str__(self):
        return f"{self.name} ({self.ip})"
    
    def get_vcenter_name(self):
        """Get the friendly name of the vCenter server"""
        if not self.vcenter_server:
            return None
        from settings.models import VCenterCredential
        try:
            vcenter = VCenterCredential.objects.get(host=self.vcenter_server)
            return vcenter.name
        except VCenterCredential.DoesNotExist:
            return self.vcenter_server  # Fallback to host if not found
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # /etc/hosts is updated automatically by signals (see inventory/signals.py)
    
    def delete(self, *args, **kwargs):
        # /etc/hosts is updated automatically by signals (see inventory/signals.py)
        super().delete(*args, **kwargs)
    
    def update_etc_hosts(self):
        """Update /etc/hosts with this host's entry using Celery task"""
        import logging
        
        logger = logging.getLogger(__name__)
        logger.info(f'update_etc_hosts() called for {self.name} ({self.ip}), active={self.active}')
        
        try:
            # Use Celery task to update /etc/hosts asynchronously
            # This avoids mod_wsgi restrictions on sudo
            from inventory.tasks import update_etc_hosts_task
            
            logger.info('Dispatching Celery task to update /etc/hosts')
            task = update_etc_hosts_task.delay()
            logger.info(f'Celery task dispatched: {task.id}')
            
        except Exception as e:
            logger.error(f'💥 Exception dispatching Celery task: {e}', exc_info=True)
    
    def remove_from_etc_hosts(self):
        """Remove this host from /etc/hosts using Celery task"""
        # Simply call update_etc_hosts() which will regenerate /etc/hosts
        # without this host (since it will be deleted or inactive)
        import logging
        
        logger = logging.getLogger(__name__)
        logger.info(f'remove_from_etc_hosts() called for {self.name} ({self.ip})')
        
        try:
            # Use Celery task to update /etc/hosts asynchronously
            from inventory.tasks import update_etc_hosts_task
            
            logger.info('Dispatching Celery task to remove from /etc/hosts')
            task = update_etc_hosts_task.delay()
            logger.info(f'Celery task dispatched: {task.id}')
            
        except Exception as e:
            logger.error(f'💥 Exception dispatching Celery task: {e}', exc_info=True)

# Create your models here.
