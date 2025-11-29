from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from django.http import JsonResponse
from inventory.models import Environment, Group, Host
from playbooks.models import Playbook
from .models import ScheduledTask, ScheduledTaskHistory
from datetime import datetime, timedelta
import pytz
import logging

logger = logging.getLogger(__name__)


@login_required
def scheduled_tasks_list(request):
    """List all scheduled tasks"""
    # Order by: pending first, then by scheduled_datetime descending (most recent first)
    tasks = ScheduledTask.objects.all().order_by('-created_at')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        tasks = tasks.filter(status=status_filter)
    
    context = {
        'tasks': tasks,
        'status_filter': status_filter,
    }
    return render(request, 'scheduler/scheduled_tasks_list.html', context)


@login_required
def cancel_scheduled_task(request, task_id):
    """Cancel a scheduled task"""
    try:
        task = ScheduledTask.objects.get(pk=task_id)
        
        if task.status == 'pending':
            task.status = 'cancelled'
            task.save()
            messages.success(request, f'Task "{task.name}" cancelled successfully')
        else:
            messages.warning(request, f'Cannot cancel task with status: {task.status}')
            
    except ScheduledTask.DoesNotExist:
        messages.error(request, 'Task not found')
    
    return redirect('scheduled_tasks_list')


@login_required
def scheduled_task_history(request):
    """View history of scheduled task executions"""
    history = ScheduledTaskHistory.objects.all()
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        history = history.filter(status=status_filter)
    
    # Filter by task type if provided
    task_type_filter = request.GET.get('task_type')
    if task_type_filter:
        history = history.filter(task_type=task_type_filter)
    
    # Filter by date range
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if date_from:
        history = history.filter(executed_at__date__gte=date_from)
    
    if date_to:
        history = history.filter(executed_at__date__lte=date_to)
    
    # Add information about tasks that have been running for too long
    now = timezone.now()
    stuck_threshold = timedelta(hours=6)  # Consider stuck after 6 hours
    
    for task in history:
        if task.status == 'running':
            running_time = now - task.executed_at
            task.is_stuck = running_time > stuck_threshold
            task.running_hours = running_time.total_seconds() / 3600
        else:
            task.is_stuck = False
            task.running_hours = 0
    
    context = {
        'history': history,
        'status_filter': status_filter,
        'task_type_filter': task_type_filter,
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'scheduler/scheduled_task_history.html', context)


@login_required
def scheduled_task_history_detail(request, history_id):
    """View detailed output of a scheduled task execution"""
    try:
        history = ScheduledTaskHistory.objects.get(pk=history_id)
        context = {'history': history}
        return render(request, 'scheduler/scheduled_task_history_detail.html', context)
    except ScheduledTaskHistory.DoesNotExist:
        messages.error(request, 'History record not found')
        return redirect('scheduled_task_history')


@login_required
def get_task_status(request, task_id):
    """AJAX endpoint to get task status"""
    try:
        task = ScheduledTask.objects.get(pk=task_id)
        
        # Get history ID if task is completed or failed
        history_id = None
        if task.scheduled_task_history_id:
            history_id = task.scheduled_task_history_id
        
        return JsonResponse({
            'status': task.status,
            'history_id': history_id
        })
    except ScheduledTask.DoesNotExist:
        return JsonResponse({'error': 'Task not found'}, status=404)


@login_required
def get_history_status(request, history_id):
    """AJAX endpoint to get scheduled task history status"""
    try:
        history = ScheduledTaskHistory.objects.get(pk=history_id)
        
        return JsonResponse({
            'status': history.status,
            'execution_duration': history.execution_duration,
            'completed_at': history.completed_at.isoformat() if history.completed_at else None
        })
    except ScheduledTaskHistory.DoesNotExist:
        return JsonResponse({'error': 'History not found'}, status=404)
