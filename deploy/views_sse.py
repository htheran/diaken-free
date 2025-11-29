"""
Server-Sent Events (SSE) views for real-time deployment updates
"""
import json
import time
from django.http import StreamingHttpResponse
from django.contrib.auth.decorators import login_required
from history.models import DeploymentHistory
from celery.result import AsyncResult
import logging

logger = logging.getLogger(__name__)


def sse_message(data, event=None):
    """
    Format a message for SSE
    
    Args:
        data: Dictionary with message data
        event: Optional event type
    
    Returns:
        Formatted SSE message string
    """
    message = ""
    if event:
        message += f"event: {event}\n"
    message += f"data: {json.dumps(data)}\n\n"
    return message


@login_required
def deployment_stream(request, history_id):
    """
    SSE endpoint for streaming deployment updates
    
    Args:
        history_id: DeploymentHistory ID
    
    Returns:
        StreamingHttpResponse with SSE updates
    """
    def event_stream():
        """Generator that yields SSE messages"""
        try:
            history = DeploymentHistory.objects.get(pk=history_id)
            
            # Send initial status
            yield sse_message({
                'status': history.status,
                'history_id': history.id,
                'target': history.target,
                'message': 'Connected to deployment stream'
            }, event='connected')
            
            last_output_length = 0
            poll_count = 0
            max_polls = 1200  # 20 minutes (1 second intervals)
            
            while poll_count < max_polls:
                # Refresh from database
                history.refresh_from_db()
                
                # Prepare update data
                update_data = {
                    'status': history.status,
                    'history_id': history.id,
                    'poll_count': poll_count,
                }
                
                # Check if there's new output
                current_output = history.ansible_output or ''
                current_length = len(current_output)
                
                if current_length > last_output_length:
                    # Send only the new output (incremental)
                    new_output = current_output[last_output_length:]
                    update_data['output'] = new_output
                    update_data['output_length'] = current_length
                    last_output_length = current_length
                
                # Check Celery task status
                if history.celery_task_id:
                    task_result = AsyncResult(history.celery_task_id)
                    update_data['task_state'] = task_result.state
                    update_data['task_ready'] = task_result.ready()
                
                # Send update
                yield sse_message(update_data, event='update')
                
                # Check if deployment is complete
                if history.status in ['success', 'failed']:
                    # Send completion message
                    completion_data = {
                        'status': history.status,
                        'history_id': history.id,
                        'message': f'Deployment {history.status}',
                        'completed_at': history.completed_at.isoformat() if history.completed_at else None,
                        'duration': history.duration() if history.completed_at else None,
                    }
                    yield sse_message(completion_data, event='complete')
                    break
                
                poll_count += 1
                time.sleep(1)  # Wait 1 second before next update
            
            # Timeout
            if poll_count >= max_polls:
                yield sse_message({
                    'status': 'timeout',
                    'message': 'Deployment stream timeout (20 minutes)'
                }, event='timeout')
                
        except DeploymentHistory.DoesNotExist:
            yield sse_message({
                'error': 'Deployment not found',
                'history_id': history_id
            }, event='error')
        except Exception as e:
            logger.error(f'SSE stream error for deployment {history_id}: {e}', exc_info=True)
            yield sse_message({
                'error': str(e),
                'history_id': history_id
            }, event='error')
    
    response = StreamingHttpResponse(
        event_stream(),
        content_type='text/event-stream'
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'  # Disable nginx buffering
    return response
