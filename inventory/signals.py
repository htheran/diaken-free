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
    """
    action = "created" if created else "updated"
    logger.info(f'Signal: Host {instance.name} {action}, dispatching Celery task to update /etc/hosts...')
    
    try:
        from inventory.tasks import update_etc_hosts_task
        task = update_etc_hosts_task.delay()
        logger.info(f'✅ Signal: Celery task {task.id} dispatched after {action} {instance.name}')
    except Exception as e:
        logger.error(f'💥 Signal: Exception dispatching Celery task: {e}', exc_info=True)


@receiver(pre_delete, sender=Host)
def update_hosts_before_delete(sender, instance, **kwargs):
    """
    Signal handler that updates /etc/hosts BEFORE a Host is deleted.
    This runs synchronously before the delete operation so the host is still in DB.
    We mark it as inactive first, then update /etc/hosts, then delete.
    """
    logger.info(f'Signal: Host {instance.name} will be deleted, marking as inactive and dispatching Celery task...')
    
    try:
        # Mark as inactive first (without triggering save signal)
        Host.objects.filter(pk=instance.pk).update(active=False)
        
        # Dispatch Celery task to update /etc/hosts (will exclude this host since it's inactive)
        from inventory.tasks import update_etc_hosts_task
        task = update_etc_hosts_task.delay()
        logger.info(f'✅ Signal: Celery task {task.id} dispatched before deleting {instance.name}')
    except Exception as e:
        logger.error(f'💥 Signal: Exception dispatching Celery task: {e}', exc_info=True)
