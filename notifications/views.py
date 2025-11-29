from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import MicrosoftTeamsWebhook, NotificationLog
from .forms import MicrosoftTeamsWebhookForm, TestNotificationForm


@login_required
def webhook_list(request):
    """List all Microsoft Teams webhooks"""
    webhooks = MicrosoftTeamsWebhook.objects.all()
    context = {
        'webhooks': webhooks,
        'active_menu': 'notifications',
    }
    return render(request, 'notifications/webhook_list.html', context)


@login_required
def webhook_create(request):
    """Create a new Microsoft Teams webhook"""
    if request.method == 'POST':
        form = MicrosoftTeamsWebhookForm(request.POST)
        if form.is_valid():
            webhook = form.save()
            messages.success(request, f'Webhook "{webhook.name}" created successfully!')
            return redirect('notifications:webhook_list')
    else:
        form = MicrosoftTeamsWebhookForm()
    
    context = {
        'form': form,
        'action': 'Create',
        'active_menu': 'notifications',
    }
    return render(request, 'notifications/webhook_form.html', context)


@login_required
def webhook_edit(request, pk):
    """Edit an existing Microsoft Teams webhook"""
    webhook = get_object_or_404(MicrosoftTeamsWebhook, pk=pk)
    
    if request.method == 'POST':
        form = MicrosoftTeamsWebhookForm(request.POST, instance=webhook)
        if form.is_valid():
            webhook = form.save()
            messages.success(request, f'Webhook "{webhook.name}" updated successfully!')
            return redirect('notifications:webhook_list')
    else:
        form = MicrosoftTeamsWebhookForm(instance=webhook)
    
    context = {
        'form': form,
        'webhook': webhook,
        'action': 'Edit',
        'active_menu': 'notifications',
    }
    return render(request, 'notifications/webhook_form.html', context)


@login_required
def webhook_delete(request, pk):
    """Delete a Microsoft Teams webhook"""
    webhook = get_object_or_404(MicrosoftTeamsWebhook, pk=pk)
    
    if request.method == 'POST':
        webhook_name = webhook.name
        webhook.delete()
        messages.success(request, f'Webhook "{webhook_name}" deleted successfully!')
        return redirect('notifications:webhook_list')
    
    context = {
        'webhook': webhook,
        'active_menu': 'notifications',
    }
    return render(request, 'notifications/webhook_confirm_delete.html', context)


@login_required
def webhook_toggle_active(request, pk):
    """Toggle webhook active status (AJAX)"""
    if request.method == 'POST':
        webhook = get_object_or_404(MicrosoftTeamsWebhook, pk=pk)
        webhook.active = not webhook.active
        webhook.save()
        return JsonResponse({
            'success': True,
            'active': webhook.active,
            'message': f'Webhook {"activated" if webhook.active else "deactivated"}'
        })
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)


@login_required
def webhook_test(request, pk):
    """Send a test notification"""
    webhook = get_object_or_404(MicrosoftTeamsWebhook, pk=pk)
    
    if request.method == 'POST':
        form = TestNotificationForm(request.POST)
        if form.is_valid():
            title = form.cleaned_data['title']
            message = form.cleaned_data['message']
            
            facts = [
                {'name': 'Type', 'value': 'Test Notification'},
                {'name': 'Sent by', 'value': request.user.username},
                {'name': 'Webhook', 'value': webhook.name},
            ]
            
            success, response = webhook.send_notification(
                title=title,
                message=message,
                color="17A2B8",  # Info blue
                facts=facts
            )
            
            if success:
                messages.success(request, 'Test notification sent successfully!')
            else:
                messages.error(request, f'Failed to send notification: {response}')
            
            return redirect('notifications:webhook_list')
    else:
        form = TestNotificationForm()
    
    context = {
        'form': form,
        'webhook': webhook,
        'active_menu': 'notifications',
    }
    return render(request, 'notifications/webhook_test.html', context)


@login_required
def webhook_configure(request, pk):
    """Configure notification preferences for a webhook"""
    webhook = get_object_or_404(MicrosoftTeamsWebhook, pk=pk)
    
    if request.method == 'POST':
        # Update notification preferences
        webhook.notify_failures_only = request.POST.get('notify_failures_only') == 'on'
        
        # VM Deployments
        webhook.notify_deployments = request.POST.get('notify_deployments') == 'on'
        webhook.notify_linux_deployments = request.POST.get('notify_linux_deployments') == 'on'
        webhook.notify_windows_deployments = request.POST.get('notify_windows_deployments') == 'on'
        
        # Playbook Executions
        webhook.notify_playbook_executions = request.POST.get('notify_playbook_executions') == 'on'
        webhook.notify_linux_playbooks = request.POST.get('notify_linux_playbooks') == 'on'
        webhook.notify_windows_playbooks = request.POST.get('notify_windows_playbooks') == 'on'
        
        # Scheduled Tasks
        webhook.notify_scheduled_tasks = request.POST.get('notify_scheduled_tasks') == 'on'
        
        webhook.save()
        messages.success(request, f'Notification preferences for "{webhook.name}" updated successfully!')
        return redirect('notifications:webhook_list')
    
    context = {
        'webhook': webhook,
        'active_menu': 'notifications',
    }
    return render(request, 'notifications/webhook_configure.html', context)


@login_required
def notification_logs(request):
    """View notification logs"""
    logs = NotificationLog.objects.select_related('webhook').all()[:100]
    
    context = {
        'logs': logs,
        'active_menu': 'notifications',
    }
    return render(request, 'notifications/notification_logs.html', context)
