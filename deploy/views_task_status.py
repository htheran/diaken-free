"""
API views for checking Celery task status
"""
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from celery.result import AsyncResult
from history.models import DeploymentHistory
import logging

logger = logging.getLogger(__name__)


@login_required
def task_status(request, task_id):
    """
    Check the status of a Celery task
    
    Args:
        task_id: Celery task ID
    
    Returns:
        JSON with task status and result
    """
    try:
        # Get task result from Celery
        task_result = AsyncResult(task_id)
        
        # Get history record if available
        history = DeploymentHistory.objects.filter(celery_task_id=task_id).first()
        
        response = {
            'task_id': task_id,
            'state': task_result.state,  # PENDING, STARTED, SUCCESS, FAILURE, RETRY
            'ready': task_result.ready(),  # True if task has finished
        }
        
        # Add history information if available
        if history:
            response['history_id'] = history.id
            response['status'] = history.status
            response['target'] = history.target
            response['playbook'] = history.playbook
            response['created_at'] = history.created_at.isoformat()
            
            if history.completed_at:
                response['completed_at'] = history.completed_at.isoformat()
                response['duration'] = history.duration()
            
            # Use ansible_output field (works for both playbooks and deployments)
            if history.ansible_output:
                response['output'] = history.ansible_output
        
        # Add task result if available
        if task_result.ready():
            if task_result.successful():
                response['result'] = task_result.result
            else:
                response['error'] = str(task_result.result)
        
        return JsonResponse(response)
        
    except Exception as e:
        logger.error(f'Error checking task status for {task_id}: {e}', exc_info=True)
        return JsonResponse({
            'error': str(e),
            'task_id': task_id
        }, status=500)


@login_required
def history_status(request, history_id):
    """
    Check the status of a deployment by history ID
    
    Args:
        history_id: DeploymentHistory ID
    
    Returns:
        JSON with deployment status
    """
    try:
        history = DeploymentHistory.objects.get(pk=history_id)
        
        response = {
            'history_id': history.id,
            'status': history.status,
            'target': history.target,
            'target_type': history.target_type,
            'playbook': history.playbook,
            'created_at': history.created_at.isoformat(),
            'user': history.user.username if history.user else None,
        }
        
        if history.celery_task_id:
            response['task_id'] = history.celery_task_id
            
            # Check Celery task status
            task_result = AsyncResult(history.celery_task_id)
            response['task_state'] = task_result.state
            response['task_ready'] = task_result.ready()
        
        if history.completed_at:
            response['completed_at'] = history.completed_at.isoformat()
            response['duration'] = history.duration()
        
        # Use ansible_output field (works for both playbooks and deployments)
        if history.ansible_output:
            response['output'] = history.ansible_output
        
        return JsonResponse(response)
        
    except DeploymentHistory.DoesNotExist:
        return JsonResponse({
            'error': 'History record not found',
            'history_id': history_id
        }, status=404)
    except Exception as e:
        logger.error(f'Error checking history status for {history_id}: {e}', exc_info=True)
        return JsonResponse({
            'error': str(e),
            'history_id': history_id
        }, status=500)
