from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from .models import Script
from .forms import ScriptForm, ScriptUploadForm
import os
import logging

logger = logging.getLogger(__name__)


@login_required
def script_list(request):
    """List all scripts"""
    scripts = Script.objects.all().order_by('os_family', 'target_type', 'name')
    
    # Group scripts by OS family and target type
    grouped_scripts = {}
    for script in scripts:
        os_key = script.get_os_family_display()
        if os_key not in grouped_scripts:
            grouped_scripts[os_key] = {'host': [], 'group': []}
        grouped_scripts[os_key][script.target_type].append(script)
    
    context = {
        'scripts': scripts,
        'grouped_scripts': grouped_scripts,
    }
    return render(request, 'scripts/script_list.html', context)


@login_required
def script_create(request):
    """Create a new script"""
    if request.method == 'POST':
        form = ScriptForm(request.POST)
        if form.is_valid():
            try:
                script = form.save()
                messages.success(request, f'Script "{script.name}" created successfully!')
                logger.info(f"Script created: {script.name} ({script.os_family}/{script.target_type})")
                return redirect('script_list')
            except Exception as e:
                messages.error(request, f'Error creating script: {str(e)}')
                logger.error(f"Error creating script: {str(e)}")
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ScriptForm()
    
    context = {
        'form': form,
        'action': 'Create',
    }
    return render(request, 'scripts/script_form.html', context)


@login_required
def script_upload(request):
    """Upload a script file"""
    if request.method == 'POST':
        form = ScriptUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                script = form.save()
                messages.success(request, f'Script "{script.name}" uploaded successfully!')
                logger.info(f"Script uploaded: {script.name} ({script.os_family}/{script.target_type})")
                return redirect('script_list')
            except Exception as e:
                messages.error(request, f'Error uploading script: {str(e)}')
                logger.error(f"Error uploading script: {str(e)}")
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ScriptUploadForm()
    
    context = {
        'form': form,
        'action': 'Upload',
    }
    return render(request, 'scripts/script_upload_form.html', context)


@login_required
def script_edit(request, pk):
    """Edit an existing script"""
    script = get_object_or_404(Script, pk=pk)
    
    if request.method == 'POST':
        form = ScriptForm(request.POST, instance=script)
        if form.is_valid():
            try:
                script = form.save()
                messages.success(request, f'Script "{script.name}" updated successfully!')
                logger.info(f"Script updated: {script.name} ({script.os_family}/{script.target_type})")
                return redirect('script_list')
            except Exception as e:
                messages.error(request, f'Error updating script: {str(e)}')
                logger.error(f"Error updating script: {str(e)}")
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ScriptForm(instance=script)
    
    context = {
        'form': form,
        'script': script,
        'action': 'Edit',
    }
    return render(request, 'scripts/script_form.html', context)


@login_required
def script_view(request, pk):
    """View script details and content"""
    script = get_object_or_404(Script, pk=pk)
    
    # Read script content
    script_content = ''
    if os.path.exists(script.file_path):
        with open(script.file_path, 'r') as f:
            script_content = f.read()
    else:
        messages.warning(request, f'Script file not found: {script.file_path}')
    
    context = {
        'script': script,
        'script_content': script_content,
    }
    return render(request, 'scripts/script_view.html', context)


@login_required
def script_download(request, pk):
    """Download script file"""
    script = get_object_or_404(Script, pk=pk)
    
    if not os.path.exists(script.file_path):
        messages.error(request, f'Script file not found: {script.file_path}')
        return redirect('script_list')
    
    with open(script.file_path, 'rb') as f:
        response = HttpResponse(f.read(), content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{script.get_full_filename()}"'
        return response


@login_required
def script_delete(request, pk):
    """Delete a script"""
    script = get_object_or_404(Script, pk=pk)
    
    if request.method == 'POST':
        script_name = script.name
        try:
            script.delete()
            messages.success(request, f'Script "{script_name}" deleted successfully!')
            logger.info(f"Script deleted: {script_name}")
            return JsonResponse({'success': True})
        except Exception as e:
            messages.error(request, f'Error deleting script: {str(e)}')
            logger.error(f"Error deleting script: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)})
    
    context = {
        'script': script,
    }
    return render(request, 'scripts/script_confirm_delete.html', context)


@login_required
def script_toggle_active(request, pk):
    """Toggle script active status"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    script = get_object_or_404(Script, pk=pk)
    script.active = not script.active
    script.save()
    
    status = 'activated' if script.active else 'deactivated'
    messages.success(request, f'Script "{script.name}" {status}!')
    logger.info(f"Script {status}: {script.name}")
    
    return JsonResponse({'success': True, 'active': script.active})


@login_required
def get_scripts_ajax(request):
    """Get scripts filtered by target type and OS family (AJAX)"""
    target_type = request.GET.get('target_type')
    os_family = request.GET.get('os_family')
    
    if not target_type or not os_family:
        return JsonResponse({'scripts': []})
    
    scripts = Script.objects.filter(
        target_type=target_type,
        os_family=os_family,
        active=True
    ).order_by('name')
    
    scripts_data = [
        {
            'id': script.id,
            'name': script.name,
            'description': script.description,
            'filename': script.get_full_filename(),
        }
        for script in scripts
    ]
    
    return JsonResponse({'scripts': scripts_data})
