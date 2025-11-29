from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db import models
from .models import Environment, Group, Host
from .forms import EnvironmentForm, GroupForm, HostForm
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

# ENVIRONMENTS
@login_required
def environment_list(request):
    environments = Environment.objects.filter(active=True).order_by('name')
    return render(request, 'inventory/environment_list.html', {'environments': environments})

@login_required
def environment_detail(request, pk):
    environment = get_object_or_404(Environment, pk=pk)
    return render(request, 'inventory/environment_detail.html', {'environment': environment})

@login_required
def environment_create(request):
    if request.method == 'POST':
        form = EnvironmentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('environment_list')
    else:
        form = EnvironmentForm()
    return render(request, 'inventory/environment_form.html', {'form': form})

@login_required
def environment_update(request, pk):
    environment = get_object_or_404(Environment, pk=pk)
    if request.method == 'POST':
        form = EnvironmentForm(request.POST, instance=environment)
        if form.is_valid():
            form.save()
            messages.success(request, f'Environment "{environment.name}" updated successfully!')
            return redirect('environment_list')
    else:
        form = EnvironmentForm(instance=environment)
    return render(request, 'inventory/environment_form.html', {'form': form})

@login_required
def environment_delete(request, pk):
    environment = get_object_or_404(Environment, pk=pk)
    if request.method == 'POST':
        environment_name = environment.name
        environment.active = False
        environment.save()
        messages.success(request, f'Environment "{environment_name}" deactivated successfully!')
        return redirect('environment_list')
    return render(request, 'inventory/environment_confirm_delete.html', {'environment': environment})

# GROUPS
@login_required
def group_list(request):
    groups = Group.objects.filter(active=True).order_by('name')
    return render(request, 'inventory/group_list.html', {'groups': groups})

@login_required
def group_detail(request, pk):
    group = get_object_or_404(Group, pk=pk)
    return render(request, 'inventory/group_detail.html', {'group': group})

@login_required
def group_create(request):
    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('group_list')
    else:
        form = GroupForm()
    return render(request, 'inventory/group_form.html', {'form': form})

@login_required
def group_update(request, pk):
    group = get_object_or_404(Group, pk=pk)
    if request.method == 'POST':
        form = GroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            messages.success(request, f'Group "{group.name}" updated successfully!')
            return redirect('group_list')
    else:
        form = GroupForm(instance=group)
    return render(request, 'inventory/group_form.html', {'form': form})

@login_required
def group_delete(request, pk):
    group = get_object_or_404(Group, pk=pk)
    if request.method == 'POST':
        group_name = group.name
        group.active = False
        group.save()
        messages.success(request, f'Group "{group_name}" deactivated successfully!')
        return redirect('group_list')
    return render(request, 'inventory/group_confirm_delete.html', {'group': group})

# HOSTS
@login_required
def host_list(request):
    hosts = Host.objects.filter(active=True).order_by('name')
    environments = Environment.objects.filter(active=True).order_by('name')
    groups = Group.objects.filter(active=True).order_by('name')
    os_choices = Host.OPERATING_SYSTEM_CHOICES
    
    # Get unique vCenter servers
    vcenter_servers = Host.objects.filter(active=True).exclude(vcenter_server='').values_list('vcenter_server', flat=True).distinct().order_by('vcenter_server')
    
    # Filters
    search_query = request.GET.get('search', '')
    env_id = request.GET.get('environment', '')
    group_id = request.GET.get('group', '')
    os_filter = request.GET.get('operating_system', '')
    vcenter_filter = request.GET.get('vcenter_server', '')
    
    if search_query:
        hosts = hosts.filter(
            models.Q(name__icontains=search_query) |
            models.Q(ip__icontains=search_query) |
            models.Q(group__name__icontains=search_query) |
            models.Q(environment__name__icontains=search_query) |
            models.Q(operating_system__icontains=search_query) |
            models.Q(vcenter_server__icontains=search_query)
        )
    if env_id:
        hosts = hosts.filter(environment_id=env_id)
    if group_id:
        hosts = hosts.filter(group_id=group_id)
    if os_filter:
        hosts = hosts.filter(operating_system=os_filter)
    if vcenter_filter:
        hosts = hosts.filter(vcenter_server=vcenter_filter)
    paginator = Paginator(hosts, 10)
    page = request.GET.get('page')
    try:
        hosts_paginated = paginator.page(page)
    except PageNotAnInteger:
        hosts_paginated = paginator.page(1)
    except EmptyPage:
        hosts_paginated = paginator.page(paginator.num_pages)
    context = {
        'hosts': hosts_paginated,
        'environments': environments,
        'groups': groups,
        'os_choices': os_choices,
        'vcenter_servers': vcenter_servers,
        'search_query': search_query,
        'env_id': env_id,
        'group_id': group_id,
        'os_filter': os_filter,
        'vcenter_filter': vcenter_filter,
        'total_hosts': hosts.count(),
    }
    return render(request, 'inventory/host_list.html', context)

@login_required
def host_detail(request, pk):
    host = get_object_or_404(Host, pk=pk)
    return render(request, 'inventory/host_detail.html', {'host': host})

from django.contrib import messages
from settings.models import DeploymentCredential
import subprocess

@login_required
def host_create(request):
    if request.method == 'POST':
        form = HostForm(request.POST)
        if form.is_valid():
            environment_id = request.POST.get('environment')
            if not environment_id:
                form.add_error('environment', 'This field is required')
                messages.error(request, 'Environment is required.')
                return render(request, 'inventory/host_form.html', {'form': form})
            try:
                environment = Environment.objects.get(pk=environment_id)
                host = form.save(commit=False)
                host.environment = environment
                host.save()
                form.save_m2m()
                # SSH fingerprint logic (only for Linux hosts)
                fingerprint_success = False
                
                # Check if this is a Windows host
                is_windows = host.operating_system and host.operating_system.lower() == 'windows'
                
                if is_windows:
                    # For Windows hosts, just show success message
                    messages.success(request, f"✓ Host '{host.name}' ({host.ip}) added successfully!")
                else:
                    # For Linux hosts, handle SSH fingerprint
                    try:
                        cred = form.cleaned_data.get('deployment_credential')
                        if cred and host.ip:
                            result = subprocess.run([
                                'ssh-keyscan', '-H', host.ip
                            ], capture_output=True, text=True, timeout=10)
                            if result.returncode == 0 and result.stdout:
                                with open('/root/.ssh/known_hosts', 'a') as kh:
                                    kh.write(result.stdout)
                                fingerprint_success = True
                                messages.success(request, f"✓ Host '{host.name}' ({host.ip}) added successfully and SSH fingerprint accepted.")
                            else:
                                messages.warning(request, f"⚠ Host '{host.name}' added, but SSH fingerprint could not be retrieved. You may need to accept it manually.")
                        else:
                            if not cred:
                                messages.warning(request, f"⚠ Host '{host.name}' added successfully, but no deployment credential was selected.")
                            else:
                                messages.warning(request, f"⚠ Host '{host.name}' added successfully, but IP address is missing for SSH fingerprint.")
                    except subprocess.TimeoutExpired:
                        messages.warning(request, f"⚠ Host '{host.name}' added, but SSH fingerprint retrieval timed out. Host may be unreachable.")
                    except Exception as e:
                        messages.warning(request, f"⚠ Host '{host.name}' added, but error accepting SSH fingerprint: {str(e)}")
                    
                    # If no fingerprint message was shown, show a generic success
                    if not fingerprint_success:
                        messages.success(request, f"✓ Host '{host.name}' added successfully!")
                return redirect('host_list')
            except Environment.DoesNotExist:
                form.add_error('environment', 'Selected environment does not exist')
                messages.error(request, 'Selected environment does not exist.')
            except Exception as e:
                messages.error(request, f"Error adding host: {str(e)}")
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = HostForm()
    
    # Get vCenter servers from VCenterCredential model
    from settings.models import VCenterCredential
    vcenters = VCenterCredential.objects.all().order_by('name')
    
    return render(request, 'inventory/host_form.html', {
        'form': form,
        'vcenters': vcenters
    })

@login_required
def host_update(request, pk):
    host = get_object_or_404(Host, pk=pk)
    if request.method == 'POST':
        form = HostForm(request.POST, instance=host)
        if form.is_valid():
            environment_id = request.POST.get('environment')
            if not environment_id:
                form.add_error('environment', 'This field is required')
                return render(request, 'inventory/host_form.html', {'form': form})
            try:
                environment = Environment.objects.get(pk=environment_id)
                host = form.save(commit=False)
                host.environment = environment
                host.save()
                form.save_m2m()
                messages.success(request, f"✓ Host '{host.name}' updated successfully!")
                return redirect('host_list')
            except Environment.DoesNotExist:
                form.add_error('environment', 'Selected environment does not exist')
                messages.error(request, 'Selected environment does not exist.')
            except Exception as e:
                messages.error(request, f"Error updating host: {str(e)}")
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = HostForm(instance=host)
    
    # Get vCenter servers from VCenterCredential model
    from settings.models import VCenterCredential
    vcenters = VCenterCredential.objects.all().order_by('name')
    
    return render(request, 'inventory/host_form.html', {
        'form': form,
        'vcenters': vcenters
    })

@login_required
def host_delete(request, pk):
    host = get_object_or_404(Host, pk=pk)
    if request.method == 'POST':
        # Delete the host permanently (will also remove from /etc/hosts)
        host_name = host.name
        host_ip = host.ip
        host.delete()
        
        # Add success message
        from django.contrib import messages
        messages.success(request, f'Host {host_name} ({host_ip}) deleted successfully and removed from /etc/hosts')
        
        return redirect('host_list')
    return render(request, 'inventory/host_confirm_delete.html', {'host': host})

# Create your views here.
