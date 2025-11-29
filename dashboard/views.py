from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from inventory.models import Host, Group, Environment
from playbooks.models import Playbook
from settings.models import VCenterCredential
from history.models import DeploymentHistory
from scheduler.models import ScheduledTaskHistory
import json

@login_required
def dashboard_home(request):
    """Main dashboard with statistics and charts"""
    
    # Get filter parameters
    days = int(request.GET.get('days', 7))
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    # Section 1: Statistics Cards
    total_playbooks = Playbook.objects.count()
    total_hosts = Host.objects.filter(active=True).count()
    total_vcenters = VCenterCredential.objects.count()
    total_environments = Environment.objects.filter(active=True).count()
    total_groups = Group.objects.filter(active=True).count()
    
    # OS Distribution
    redhat_count = Host.objects.filter(active=True, operating_system__icontains='redhat').count()
    debian_count = Host.objects.filter(active=True, operating_system__icontains='debian').count()
    ubuntu_count = Host.objects.filter(active=True, operating_system__icontains='ubuntu').count()
    centos_count = Host.objects.filter(active=True, operating_system__icontains='centos').count()
    windows_count = Host.objects.filter(active=True, operating_system__icontains='windows').count()
    other_os_count = total_hosts - (redhat_count + debian_count + ubuntu_count + centos_count + windows_count)
    
    # Section 2: Execution Statistics (last N days)
    # Include both manual executions and scheduled task executions
    manual_executions = DeploymentHistory.objects.filter(
        created_at__gte=start_date,
        created_at__lte=end_date
    )
    
    scheduled_executions = ScheduledTaskHistory.objects.filter(
        executed_at__gte=start_date,
        executed_at__lte=end_date
    )
    
    # Calculate totals
    manual_total = manual_executions.count()
    manual_success = manual_executions.filter(status='success').count()
    manual_failed = manual_executions.filter(status='failed').count()
    
    scheduled_total = scheduled_executions.count()
    scheduled_success = scheduled_executions.filter(status='success').count()
    scheduled_failed = scheduled_executions.filter(status='failed').count()
    
    total_executions = manual_total + scheduled_total
    successful_executions = manual_success + scheduled_success
    failed_executions = manual_failed + scheduled_failed
    success_rate = round((successful_executions / total_executions * 100) if total_executions > 0 else 0, 1)
    
    # Daily execution data for chart
    daily_data = {}
    current_date = start_date.date()
    while current_date <= end_date.date():
        daily_data[current_date.isoformat()] = {'success': 0, 'failed': 0}
        current_date += timedelta(days=1)
    
    # Add manual executions to daily data
    for execution in manual_executions:
        date_key = execution.created_at.date().isoformat()
        if date_key in daily_data:
            if execution.status == 'success':
                daily_data[date_key]['success'] += 1
            else:
                daily_data[date_key]['failed'] += 1
    
    # Add scheduled executions to daily data
    for execution in scheduled_executions:
        date_key = execution.executed_at.date().isoformat()
        if date_key in daily_data:
            if execution.status == 'success':
                daily_data[date_key]['success'] += 1
            else:
                daily_data[date_key]['failed'] += 1
    
    # Prepare chart data
    labels = sorted(daily_data.keys())
    success_data = [daily_data[date]['success'] for date in labels]
    failed_data = [daily_data[date]['failed'] for date in labels]
    
    datasets = [
        {
            'label': 'Successful',
            'data': success_data,
            'backgroundColor': 'rgba(28, 200, 138, 0.7)',
            'borderColor': 'rgba(28, 200, 138, 1)',
            'borderWidth': 1
        },
        {
            'label': 'Failed',
            'data': failed_data,
            'backgroundColor': 'rgba(231, 74, 59, 0.7)',
            'borderColor': 'rgba(231, 74, 59, 1)',
            'borderWidth': 1
        }
    ]
    
    # Top playbooks - combine manual and scheduled executions
    from collections import Counter
    playbook_counts = Counter()
    
    # Count manual executions
    for exec in manual_executions:
        if exec.playbook:
            playbook_counts[exec.playbook] += 1
    
    # Count scheduled executions
    for exec in scheduled_executions:
        if exec.playbook_name:
            playbook_counts[exec.playbook_name] += 1
    
    # Get top 5 playbooks
    top_playbooks = [{'playbook': name, 'count': count} 
                     for name, count in playbook_counts.most_common(5)]
    
    # OS Distribution data for pie chart
    os_data = {
        'labels': [],
        'data': [],
        'colors': []
    }
    
    os_colors = {
        'RedHat': '#EE0000',
        'Debian': '#A80030',
        'Ubuntu': '#E95420',
        'CentOS': '#262577',
        'Windows': '#0078D4',
        'Other': '#6c757d'
    }
    
    if redhat_count > 0:
        os_data['labels'].append('RedHat')
        os_data['data'].append(redhat_count)
        os_data['colors'].append(os_colors['RedHat'])
    
    if debian_count > 0:
        os_data['labels'].append('Debian')
        os_data['data'].append(debian_count)
        os_data['colors'].append(os_colors['Debian'])
    
    if ubuntu_count > 0:
        os_data['labels'].append('Ubuntu')
        os_data['data'].append(ubuntu_count)
        os_data['colors'].append(os_colors['Ubuntu'])
    
    if centos_count > 0:
        os_data['labels'].append('CentOS')
        os_data['data'].append(centos_count)
        os_data['colors'].append(os_colors['CentOS'])
    
    if windows_count > 0:
        os_data['labels'].append('Windows')
        os_data['data'].append(windows_count)
        os_data['colors'].append(os_colors['Windows'])
    
    if other_os_count > 0:
        os_data['labels'].append('Other')
        os_data['data'].append(other_os_count)
        os_data['colors'].append(os_colors['Other'])
    
    # Calculate number of different OS types
    os_types_count = sum([
        1 if redhat_count > 0 else 0,
        1 if debian_count > 0 else 0,
        1 if ubuntu_count > 0 else 0,
        1 if centos_count > 0 else 0,
        1 if windows_count > 0 else 0,
        1 if other_os_count > 0 else 0
    ])
    
    context = {
        # Filter info
        'days': days,
        'start_date': start_date,
        'end_date': end_date,
        
        # Statistics cards
        'total_playbooks': total_playbooks,
        'total_hosts': total_hosts,
        'total_vcenters': total_vcenters,
        'total_environments': total_environments,
        'total_groups': total_groups,
        
        # OS Distribution
        'redhat_count': redhat_count,
        'debian_count': debian_count,
        'ubuntu_count': ubuntu_count,
        'centos_count': centos_count,
        'windows_count': windows_count,
        'other_os_count': other_os_count,
        'os_types_count': os_types_count,
        
        # Execution statistics
        'total_executions': total_executions,
        'successful_executions': successful_executions,
        'failed_executions': failed_executions,
        'success_rate': success_rate,
        
        # Chart data
        'labels': json.dumps(labels),
        'datasets': json.dumps(datasets),
        'top_playbooks': top_playbooks,
        'os_data_json': json.dumps(os_data),
    }
    
    return render(request, 'dashboard/dashboard.html', context)
