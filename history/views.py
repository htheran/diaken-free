from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import DeploymentHistory
from .forms import CleanupStuckDeploymentsForm
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

@login_required
def history_list(request):
    from django.utils import timezone
    from datetime import timedelta
    
    # Filtros
    status_filter = request.GET.get('status', '')
    type_filter = request.GET.get('type', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Ordenar por fecha descendente (más recientes primero)
    deployments = DeploymentHistory.objects.all().order_by('-created_at')
    
    # Aplicar filtros
    if status_filter:
        deployments = deployments.filter(status=status_filter)
    if type_filter:
        deployments = deployments.filter(target_type=type_filter)
    if date_from:
        deployments = deployments.filter(created_at__gte=date_from)
    if date_to:
        deployments = deployments.filter(created_at__lte=date_to)
    
    # Agregar información sobre deployments que llevan mucho tiempo corriendo
    now = timezone.now()
    stuck_threshold = timedelta(hours=6)  # Considerar stuck después de 6 horas
    
    for deployment in deployments:
        if deployment.status == 'running':
            running_time = now - deployment.created_at
            deployment.is_stuck = running_time > stuck_threshold
            deployment.running_hours = running_time.total_seconds() / 3600
        else:
            deployment.is_stuck = False
            deployment.running_hours = 0
    
    context = {
        'deployments': deployments,
        'status_filter': status_filter,
        'type_filter': type_filter,
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'history/history_list.html', context)

@login_required
def history_detail(request, pk):
    deployment = get_object_or_404(DeploymentHistory, pk=pk)
    return render(request, 'history/history_detail.html', {'deployment': deployment})


@login_required
def cleanup_stuck_deployments_view(request):
    """Web interface to manage stuck deployments cleanup"""
    from scheduler.models import ScheduledTaskHistory
    
    results = None
    
    if request.method == 'POST':
        form = CleanupStuckDeploymentsForm(request.POST)
        if form.is_valid():
            timeout_hours = form.cleaned_data['timeout_hours']
            dry_run = form.cleaned_data['dry_run']
            
            # Calculate cutoff time
            cutoff_time = timezone.now() - timedelta(hours=timeout_hours)
            
            # Find stuck deployments
            stuck_deployments = DeploymentHistory.objects.filter(
                status='running',
                created_at__lt=cutoff_time
            ).order_by('created_at')
            
            # Find stuck scheduled tasks
            stuck_tasks = ScheduledTaskHistory.objects.filter(
                status='running',
                executed_at__lt=cutoff_time
            ).order_by('executed_at')
            
            deployment_list = []
            task_list = []
            
            # Process deployments
            for dep in stuck_deployments:
                running_time = timezone.now() - dep.created_at
                hours = running_time.total_seconds() / 3600
                
                deployment_list.append({
                    'id': dep.id,
                    'target': dep.target,
                    'playbook': dep.playbook,
                    'started': dep.created_at,
                    'hours': hours
                })
                
                if not dry_run:
                    dep.status = 'failed'
                    dep.completed_at = timezone.now()
                    if not dep.ansible_output:
                        dep.ansible_output = f'Deployment automatically marked as failed after running for {hours:.1f} hours (timeout: {timeout_hours}h)'
                    else:
                        dep.ansible_output += f'\n\n[SYSTEM] Deployment automatically marked as failed after running for {hours:.1f} hours (timeout: {timeout_hours}h)'
                    dep.save()
            
            # Process scheduled tasks
            for task in stuck_tasks:
                running_time = timezone.now() - task.executed_at
                hours = running_time.total_seconds() / 3600
                
                task_list.append({
                    'id': task.id,
                    'target': task.target_name,
                    'playbook': task.playbook_name,
                    'started': task.executed_at,
                    'hours': hours
                })
                
                if not dry_run:
                    task.status = 'failed'
                    task.completed_at = timezone.now()
                    if not task.ansible_output:
                        task.ansible_output = f'Task automatically marked as failed after running for {hours:.1f} hours (timeout: {timeout_hours}h)'
                    else:
                        task.ansible_output += f'\n\n[SYSTEM] Task automatically marked as failed after running for {hours:.1f} hours (timeout: {timeout_hours}h)'
                    task.save()
            
            results = {
                'dry_run': dry_run,
                'timeout_hours': timeout_hours,
                'deployments': deployment_list,
                'tasks': task_list,
                'total': len(deployment_list) + len(task_list)
            }
            
            if not dry_run:
                if results['total'] > 0:
                    messages.success(request, f'Successfully cleaned up {results["total"]} stuck item(s)')
                else:
                    messages.info(request, 'No stuck deployments or tasks found')
            else:
                if results['total'] > 0:
                    messages.warning(request, f'DRY RUN: Found {results["total"]} stuck item(s) that would be cleaned up')
                else:
                    messages.info(request, 'No stuck deployments or tasks found')
    else:
        form = CleanupStuckDeploymentsForm()
    
    # Get current running deployments for display
    running_deployments = DeploymentHistory.objects.filter(status='running').order_by('-created_at')
    now = timezone.now()
    
    for dep in running_deployments:
        running_time = now - dep.created_at
        dep.running_hours = running_time.total_seconds() / 3600
    
    context = {
        'form': form,
        'results': results,
        'running_deployments': running_deployments,
    }
    return render(request, 'history/cleanup_stuck_deployments.html', context)


@login_required
def check_task_status(request, pk):
    """
    Vista AJAX para verificar el estado de una tarea Celery.
    Retorna JSON con el estado actual del deployment.
    """
    from django.http import JsonResponse
    from celery.result import AsyncResult
    
    deployment = get_object_or_404(DeploymentHistory, pk=pk)
    
    response_data = {
        'status': deployment.status,
        'created_at': deployment.created_at.isoformat(),
        'completed_at': deployment.completed_at.isoformat() if deployment.completed_at else None,
        'duration': deployment.duration(),
        'output': deployment.provision_output or '',  # Output en tiempo real
    }
    
    # Si hay un celery_task_id, verificar el estado de la tarea
    if deployment.celery_task_id:
        task = AsyncResult(deployment.celery_task_id)
        response_data['celery_status'] = task.state
        response_data['celery_info'] = str(task.info) if task.info else None
    
    return JsonResponse(response_data)
