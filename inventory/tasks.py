"""
Celery tasks for inventory management
"""
from celery import shared_task
import subprocess
import logging

logger = logging.getLogger(__name__)


@shared_task(name='inventory.update_etc_hosts')
def update_etc_hosts_task():
    """
    Celery task to update /etc/hosts file.
    This runs asynchronously and can execute sudo without mod_wsgi restrictions.
    """
    try:
        logger.info('Celery task: Updating /etc/hosts...')
        
        result = subprocess.run(
            ['sudo', '/usr/local/bin/update-diaken-hosts.py'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            logger.info(f'✅ Celery task: Successfully updated /etc/hosts')
            logger.info(f'Output: {result.stdout}')
            return {'status': 'success', 'message': result.stdout}
        else:
            logger.error(f'❌ Celery task: Error updating /etc/hosts (returncode={result.returncode})')
            logger.error(f'Error: {result.stderr}')
            return {'status': 'error', 'message': result.stderr}
            
    except subprocess.TimeoutExpired:
        logger.error('⏱️ Celery task: Timeout updating /etc/hosts')
        return {'status': 'error', 'message': 'Timeout'}
    except Exception as e:
        logger.error(f'💥 Celery task: Exception updating /etc/hosts: {e}', exc_info=True)
        return {'status': 'error', 'message': str(e)}
