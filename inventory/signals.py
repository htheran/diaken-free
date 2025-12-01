"""
Django signals for automatic /etc/hosts management
"""
from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver
from .models import Host
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Host)
def update_hosts_after_save(sender, instance, created, **kwargs):
    """
    Signal handler that updates /etc/hosts after a Host is saved.
    This runs synchronously after the save operation.
    Updates /etc/hosts directly without Celery dependency.
    """
    action = "created" if created else "updated"
    logger.info(f'Signal: Host {instance.name} {action}, updating /etc/hosts...')
    
    try:
        from inventory.hosts_manager import update_hosts_file
        success, message = update_hosts_file()
        if success:
            logger.info(f'✅ Signal: /etc/hosts updated after {action} {instance.name}')
        else:
            logger.error(f'❌ Signal: Failed to update /etc/hosts: {message}')
    except Exception as e:
        logger.error(f'💥 Signal: Exception updating /etc/hosts: {e}', exc_info=True)


@receiver(pre_delete, sender=Host)
def update_hosts_before_delete(sender, instance, **kwargs):
    """
    Signal handler that updates /etc/hosts BEFORE a Host is deleted.
    This runs synchronously before the delete operation so the host is still in DB.
    We mark it as inactive first, then update /etc/hosts, then delete.
    Updates /etc/hosts directly without Celery dependency.
    """
    logger.info(f'Signal: Host {instance.name} will be deleted, marking as inactive and updating /etc/hosts...')
    
    try:
        # Mark as inactive first (without triggering save signal)
        Host.objects.filter(pk=instance.pk).update(active=False)
        
        # Update /etc/hosts directly (will exclude this host since it's inactive)
        from inventory.hosts_manager import update_hosts_file
        success, message = update_hosts_file()
        if success:
            logger.info(f'✅ Signal: /etc/hosts updated before deleting {instance.name}')
        else:
            logger.error(f'❌ Signal: Failed to update /etc/hosts: {message}')
    except Exception as e:
        logger.error(f'💥 Signal: Exception updating /etc/hosts: {e}', exc_info=True)
