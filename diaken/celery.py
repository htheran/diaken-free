"""
Celery configuration for Diaken project.
"""
import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'diaken.settings')

app = Celery('diaken')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Explicitly import Windows deployment tasks
try:
    from deploy import tasks_windows
except ImportError as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f'Could not import deploy.tasks_windows: {e}')


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f'Debug task request: {self.request!r}')
