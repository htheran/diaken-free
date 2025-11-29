from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from .models import Playbook
from .forms import PlaybookForm, PlaybookContentForm
import os
import logging

logger = logging.getLogger(__name__)

@login_required
def playbook_list(request):
    """List all playbooks"""
    playbooks = Playbook.objects.all().order_by('os_family', 'playbook_type', 'name')
    
    # Group playbooks by OS family and type
    grouped_playbooks = {}
    for playbook in playbooks:
        os_key = playbook.get_os_family_display()
        if os_key not in grouped_playbooks:
            grouped_playbooks[os_key] = {'host': [], 'group': []}
        grouped_playbooks[os_key][playbook.playbook_type].append(playbook)
    
    context = {
        'playbooks': playbooks,
        'grouped_playbooks': grouped_playbooks,
    }
    return render(request, 'playbooks/playbook_list.html', context)

@login_required
def playbook_list_host(request):
    playbooks = Playbook.objects.filter(playbook_type='host')
    return render(request, 'playbooks/playbook_list.html', {'playbooks': playbooks, 'filter_type': 'host'})

@login_required
def playbook_list_group(request):
    playbooks = Playbook.objects.filter(playbook_type='group')
    return render(request, 'playbooks/playbook_list.html', {'playbooks': playbooks, 'filter_type': 'group'})

@login_required
def playbook_create(request):
    """Create a new playbook with inline content editing"""
    if request.method == 'POST':
        form = PlaybookContentForm(request.POST)
        if form.is_valid():
            try:
                playbook = form.save()
                messages.success(request, f'Playbook "{playbook.name}" created successfully!')
                logger.info(f"Playbook created: {playbook.name} ({playbook.os_family}/{playbook.playbook_type})")
                return redirect('playbook_list')
            except Exception as e:
                messages.error(request, f'Error creating playbook: {str(e)}')
                logger.error(f"Error creating playbook: {str(e)}")
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PlaybookContentForm()
    
    context = {
        'form': form,
        'action': 'Create',
    }
    return render(request, 'playbooks/playbook_form.html', context)


@login_required
def playbook_upload(request):
    """Upload a playbook file"""
    if request.method == 'POST':
        form = PlaybookForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                playbook = form.save()
                messages.success(request, f'Playbook "{playbook.name}" uploaded successfully!')
                logger.info(f"Playbook uploaded: {playbook.name} ({playbook.os_family}/{playbook.playbook_type})")
                return redirect('playbook_list')
            except Exception as e:
                messages.error(request, f'Error uploading playbook: {str(e)}')
                logger.error(f"Error uploading playbook: {str(e)}")
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PlaybookForm()
    
    context = {
        'form': form,
        'action': 'Upload',
    }
    return render(request, 'playbooks/playbook_upload.html', context)

@login_required
def playbook_edit(request, pk):
    """Edit an existing playbook with inline content editing"""
    playbook = get_object_or_404(Playbook, pk=pk)
    
    if request.method == 'POST':
        form = PlaybookContentForm(request.POST, instance=playbook)
        if form.is_valid():
            try:
                playbook = form.save()
                messages.success(request, f'Playbook "{playbook.name}" updated successfully!')
                logger.info(f"Playbook updated: {playbook.name} ({playbook.os_family}/{playbook.playbook_type})")
                return redirect('playbook_list')
            except Exception as e:
                messages.error(request, f'Error updating playbook: {str(e)}')
                logger.error(f"Error updating playbook: {str(e)}")
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PlaybookContentForm(instance=playbook)
    
    context = {
        'form': form,
        'playbook': playbook,
        'action': 'Edit',
    }
    return render(request, 'playbooks/playbook_form.html', context)

@login_required
def playbook_view(request, pk):
    """View playbook details and content"""
    playbook = get_object_or_404(Playbook, pk=pk)
    
    # Read playbook content
    playbook_content = ''
    if os.path.exists(playbook.file.path):
        with open(playbook.file.path, 'r') as f:
            playbook_content = f.read()
    else:
        messages.warning(request, f'Playbook file not found: {playbook.file.path}')
    
    context = {
        'playbook': playbook,
        'playbook_content': playbook_content,
    }
    return render(request, 'playbooks/playbook_view.html', context)


@login_required
def playbook_download(request, pk):
    """Download playbook file"""
    playbook = get_object_or_404(Playbook, pk=pk)
    
    if not os.path.exists(playbook.file.path):
        messages.error(request, f'Playbook file not found: {playbook.file.path}')
        return redirect('playbook_list')
    
    with open(playbook.file.path, 'rb') as f:
        response = HttpResponse(f.read(), content_type='application/x-yaml')
        response['Content-Disposition'] = f'attachment; filename="{playbook.name}.yml"'
        return response


@login_required
def playbook_delete(request, pk):
    """Delete a playbook"""
    playbook = get_object_or_404(Playbook, pk=pk)
    
    if request.method == 'POST':
        try:
            playbook_name = playbook.name
            playbook.delete()
            messages.success(request, f'Playbook "{playbook_name}" deleted successfully!')
            logger.info(f"Playbook deleted: {playbook_name}")
        except Exception as e:
            messages.error(request, f'Error deleting playbook: {str(e)}')
            logger.error(f"Error deleting playbook: {str(e)}")
        return redirect('playbook_list')
    
    return render(request, 'playbooks/playbook_delete.html', {'playbook': playbook})
