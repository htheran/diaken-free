from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from inventory.models import Environment, Group, Host
from playbooks.models import Playbook
from history.models import DeploymentHistory
from settings.models import DeploymentCredential, GlobalSetting
import subprocess
import json
import logging
import os
from django.conf import settings
#import traceback
import traceback as tb
from django.utils import timezone
from .vcenter_snapshot import get_vcenter_connection, create_snapshot, Disconnect

logger = logging.getLogger(__name__)

@login_required
def deploy_index(request):
    """Index page for deploy menu with options"""
    return render(request, 'deploy/deploy_index.html')

@login_required
def deploy_playbook(request):
    """Form to select host/group and playbook to execute (Linux)"""
    environments = Environment.objects.filter(active=True).order_by('name')
    groups = Group.objects.filter(active=True).order_by('name')
    # Filter only Linux hosts (RedHat and Debian)
    hosts = Host.objects.filter(active=True, operating_system__in=['redhat', 'debian']).order_by('name')
    # Playbooks will be loaded dynamically based on target_type
    
    context = {
        'environments': environments,
        'groups': groups,
        'hosts': hosts,
    }
    return render(request, 'deploy/deploy_playbook_form.html', context)

@login_required
def execute_playbook(request):
    """Execute selected playbook or script on selected host or group"""
    if request.method != 'POST':
        return redirect('deploy:deploy_playbook')
    
    # Get form data
    execution_type = request.POST.get('execution_type')  # 'playbook' or 'script'
    os_family = request.POST.get('os_family')  # 'redhat' or 'debian'
    target_type = request.POST.get('target_type')  # 'host' or 'group'
    host_id = request.POST.get('host')
    group_id = request.POST.get('group')
    playbook_id = request.POST.get('playbook')
    script_id = request.POST.get('script')
    scheduled = request.POST.get('scheduled') == '1'
    scheduled_time = request.POST.get('scheduled_time')
    
    # Validate execution type
    if not execution_type or execution_type not in ['playbook', 'script']:
        return JsonResponse({'success': False, 'error': 'Invalid execution type'})
    
    # Validate OS family
    if not os_family or os_family not in ['redhat', 'debian']:
        return JsonResponse({'success': False, 'error': 'Invalid OS family'})
    
    # Get and log snapshot flag (for hosts and groups)
    create_snapshot_value = request.POST.get('create_snapshot')
    create_snapshot_flag = create_snapshot_value == '1'
    logger.info(f"[LINUX-EXECUTION] Execution type: {execution_type}")
    logger.info(f"[LINUX-EXECUTION] OS family: {os_family}")
    logger.info(f"[LINUX-EXECUTION] Target type: {target_type}")
    logger.info(f"[LINUX-EXECUTION] Snapshot checkbox value: '{create_snapshot_value}'")
    logger.info(f"[LINUX-EXECUTION] Snapshot flag evaluated to: {create_snapshot_flag}")
    
    # Validate target
    if target_type == 'host':
        if not host_id:
            return JsonResponse({'success': False, 'error': 'Host is required'})
        try:
            host = Host.objects.get(pk=host_id)
            target_name = host.name
            target_ip = host.ip
        except Host.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Host not found'})
    elif target_type == 'group':
        if not group_id:
            return JsonResponse({'success': False, 'error': 'Group is required'})
        try:
            group = Group.objects.get(pk=group_id)
            target_name = group.name
            hosts_in_group = Host.objects.filter(group=group, active=True, operating_system__in=['redhat', 'debian'])
            if not hosts_in_group.exists():
                return JsonResponse({'success': False, 'error': f'No active Linux hosts found in group {group.name}'})
        except Group.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Group not found'})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid target type'})
    
    # Get playbook or script
    if execution_type == 'playbook':
        if not playbook_id:
            return JsonResponse({'success': False, 'error': 'Playbook is required'})
        try:
            playbook = Playbook.objects.get(pk=playbook_id)
            execution_name = playbook.name
            execution_file = playbook.file.path
        except Playbook.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Playbook not found'})
    else:  # script
        if not script_id:
            return JsonResponse({'success': False, 'error': 'Script is required'})
        try:
            from scripts.models import Script
            script = Script.objects.get(pk=script_id)
            execution_name = script.name
            execution_file = script.file_path
            playbook = None  # No playbook for script execution
        except Script.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Script not found'})
    
    # For host execution, use the host variable from above
    # For group execution, we'll use the first host's credentials
    if target_type == 'group':
        host = hosts_in_group.first()
    
    # Get SSH credentials - use host's credential if configured, otherwise use first available
    ssh_cred = host.deployment_credential if host.deployment_credential else DeploymentCredential.objects.first()
    if not ssh_cred:
        return JsonResponse({'success': False, 'error': 'No SSH credentials configured. Please assign a deployment credential to the host or create one in Settings.'})
    
    # Create snapshot if requested (only for immediate execution, not scheduled)
    # For scheduled tasks, the snapshot will be created by the scheduler when the task runs
    snapshot_created = False
    snapshot_name = None
    snapshot_info = ""
    
    logger.info(f"[SNAPSHOT-CHECK] create_snapshot_flag={create_snapshot_flag}, scheduled={scheduled}, will_create_now={create_snapshot_flag and not scheduled}")
    
    if create_snapshot_flag and not scheduled:
        logger.info(f"Snapshot requested for host {host.name} ({host.ip})")
        
        if not host.vcenter_server:
            snapshot_info = f"Warning: No vCenter server configured for {host.name}"
            logger.warning(snapshot_info)
        else:
            try:
                # Get vCenter credentials from VCenterCredential model
                from settings.models import VCenterCredential
                vcenter_cred = VCenterCredential.objects.filter(host=host.vcenter_server).first()
                
                logger.info(f"vCenter credential found: {vcenter_cred is not None}")
                
                if vcenter_cred:
                    # Use local timezone for snapshot name
                    local_time = timezone.localtime(timezone.now())
                    snapshot_name = f"Before executing {execution_name} - {local_time.strftime('%Y-%m-%d %H:%M:%S')}"
                    
                    logger.info(f"Connecting to vCenter: {host.vcenter_server}")
                    logger.info(f"Using vCenter: {vcenter_cred.name}")
                    logger.info(f"Using user: {vcenter_cred.user}")
                    logger.info(f"Creating snapshot: {snapshot_name}")
                    
                    si = get_vcenter_connection(
                        host.vcenter_server,
                        vcenter_cred.user,
                        vcenter_cred.get_password()
                    )
                    
                    logger.info(f"vCenter connection established")
                    logger.info(f"Searching for VM with IP: {host.ip}")
                    
                    success, message, snap_id = create_snapshot(si, host.ip, snapshot_name, f"Safety snapshot before {execution_name}")
                    
                    logger.info(f"Snapshot creation result - Success: {success}, Message: {message}")
                    
                    Disconnect(si)
                    
                    if success:
                        snapshot_created = True
                        snapshot_info = f"Snapshot created successfully: {snapshot_name}"
                        logger.info(snapshot_info)
                        
                        # Record snapshot in history
                        try:
                            from snapshots.models import SnapshotHistory
                            
                            # Get retention hours
                            retention_setting = GlobalSetting.objects.filter(key='snapshot_retention_hours').first()
                            retention_hours = int(retention_setting.value) if retention_setting else 24
                            
                            SnapshotHistory.objects.create(
                                snapshot_name=snapshot_name,
                                vcenter_snapshot_id=snap_id,
                                host=host,
                                group=None,  # Single host execution
                                playbook=playbook if execution_type == 'playbook' else None,
                                script_name=execution_name if execution_type == 'script' else None,
                                user=request.user,
                                description=f"Safety snapshot before {execution_name}",
                                retention_hours=retention_hours,
                                status='active'
                            )
                            logger.info(f"Snapshot recorded in history with {retention_hours}h retention")
                        except Exception as hist_error:
                            logger.error(f"Failed to record snapshot in history: {hist_error}")
                    else:
                        snapshot_info = f"Failed to create snapshot: {message}"
                        logger.warning(snapshot_info)
                        # Continue with playbook execution even if snapshot fails
                else:
                    snapshot_info = f"vCenter credential not found for {host.vcenter_server}. Please add it in Settings -> vCenter Credentials"
                    logger.warning(snapshot_info)
            except Exception as e:
                import traceback
                snapshot_info = f"Exception creating snapshot: {str(e)}"
                logger.error(snapshot_info)
                logger.error(traceback.format_exc())
                # Continue with playbook execution even if snapshot fails
    
    # Handle scheduled execution
    if scheduled and scheduled_time:
        try:
            from datetime import datetime
            from scheduler.models import ScheduledTask
            
            # Parse scheduled time (format: YYYY-MM-DDTHH:MM)
            scheduled_dt = datetime.strptime(scheduled_time, '%Y-%m-%dT%H:%M')
            # Make it timezone-aware
            scheduled_dt = timezone.make_aware(scheduled_dt)
            
            # Create scheduled task
            task = ScheduledTask.objects.create(
                task_type=target_type,
                name=f"Execute {execution_name} on {target_name}",
                created_by=request.user,
                environment=host.environment if target_type == 'host' else group.environment,
                group=group if target_type == 'group' else None,
                host=host if target_type == 'host' else None,
                playbook=playbook if execution_type == 'playbook' else None,
                script=script if execution_type == 'script' else None,
                execution_type=execution_type,
                os_family=os_family,
                create_snapshot=create_snapshot_flag,
                scheduled_datetime=scheduled_dt,
                status='pending'
            )
            
            logger.info(f"[LINUX-EXECUTION] Scheduled task created: {task.id} for {scheduled_dt}")
            
            return JsonResponse({
                'success': True,
                'scheduled': True,
                'task_id': task.id,
                'scheduled_time': scheduled_dt.strftime('%Y-%m-%d %H:%M:%S'),
                'output': f"Task scheduled successfully for {scheduled_dt.strftime('%Y-%m-%d %H:%M:%S')}\n\nTask ID: {task.id}\nExecution Type: {execution_type.title()}\nName: {execution_name}\nTarget: {target_name}"
            })
        except Exception as e:
            logger.error(f"[LINUX-EXECUTION] Error creating scheduled task: {str(e)}")
            return JsonResponse({'success': False, 'error': f'Failed to schedule task: {str(e)}'})
    
    # Create deployment history record
    history = DeploymentHistory.objects.create(
        user=request.user,
        environment=host.environment.name if host.environment else '',
        target=host.name,
        target_type='Host',
        playbook=execution_name,
        status='running',
        hostname=host.name,
        ip_address=host.ip
    )
    
    try:
        # Get SSH user and key
        ansible_user = host.ansible_user if host.ansible_user else ssh_cred.user
        ssh_key_path = host.ansible_ssh_private_key_file if host.ansible_ssh_private_key_file else ssh_cred.ssh_key_file_path
        
        logger.info(f'[EXECUTION] Execution type: {execution_type}')
        logger.info(f'[EXECUTION] Using user: {ansible_user}')
        logger.info(f'[EXECUTION] Using SSH key: {ssh_key_path}')
        logger.info(f'[EXECUTION] Using credential: {ssh_cred.name}')
        
        if execution_type == 'playbook':
            # Execute playbook with Ansible
            inventory_vars = [
                f"ansible_user={ansible_user}",
                f"ansible_ssh_private_key_file={ssh_key_path}",
                "ansible_ssh_common_args='-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'"
            ]
            
            # Add Python interpreter (use host config or default to /usr/bin/python3)
            python_interp = host.ansible_python_interpreter if host.ansible_python_interpreter else '/usr/bin/python3'
            inventory_vars.append(f"ansible_python_interpreter={python_interp}")
            
            # Create inventory based on target type
            if target_type == 'host':
                inventory_line = f"{host.ip} {' '.join(inventory_vars)}"
                inventory_content = f"""[target_host]
{inventory_line}
"""
            else:  # group
                # Create inventory with all hosts in group
                inventory_lines = ['[target_group]']
                for group_host in hosts_in_group:
                    # Use each host's specific settings
                    host_ansible_user = group_host.ansible_user if group_host.ansible_user else ansible_user
                    host_ssh_key = group_host.ansible_ssh_private_key_file if group_host.ansible_ssh_private_key_file else ssh_key_path
                    host_vars = [
                        f"ansible_user={host_ansible_user}",
                        f"ansible_ssh_private_key_file={host_ssh_key}",
                        "ansible_ssh_common_args='-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'"
                    ]
                    # Add Python interpreter (use host config or default to /usr/bin/python3)
                    host_python_interp = group_host.ansible_python_interpreter if group_host.ansible_python_interpreter else '/usr/bin/python3'
                    host_vars.append(f"ansible_python_interpreter={host_python_interp}")
                    inventory_lines.append(f"{group_host.ip} {' '.join(host_vars)}")
                inventory_content = '\n'.join(inventory_lines) + '\n'
            
            inventory_path = f'/tmp/ansible_inventory_{history.id}.ini'
            with open(inventory_path, 'w') as f:
                f.write(inventory_content)
            
            # Get global settings for extra vars
            global_settings = GlobalSetting.objects.all()
            if target_type == 'host':
                extra_vars = {'target_host': host.ip, 'inventory_hostname': host.name}
            else:  # group
                extra_vars = {}
            
            # Add all global settings as extra vars
            for setting in global_settings:
                extra_vars[setting.key] = setting.value
            
            # Convert extra_vars to JSON string
            extra_vars_json = json.dumps(extra_vars)
            
            # Execute playbook asynchronously with Celery
            from deploy.tasks import execute_playbook_async
            
            logger.info(f'[ASYNC] Dispatching Celery task for playbook execution')
            logger.info(f'[ASYNC] History ID: {history.id}')
            
            # Dispatch Celery task
            task = execute_playbook_async.delay(
                history_id=history.id,
                inventory_content=inventory_content,
                execution_file=execution_file,
                extra_vars_json=extra_vars_json,
                ansible_user=ansible_user,
                ssh_key_path=ssh_key_path
            )
            
            logger.info(f'[ASYNC] Celery task dispatched: {task.id}')
            
            # Update history with task ID
            history.celery_task_id = task.id
            history.status = 'running'
            history.save()
            
            # Return immediately with task info
            return JsonResponse({
                'success': True,
                'message': f'Playbook execution started in background',
                'task_id': task.id,
                'history_id': history.id,
                'async': True
            })
            
        else:  # script execution
            # Execute script via Celery for real-time output
            from deploy.tasks import execute_script_async
            
            logger.info(f'[SCRIPT] Executing script asynchronously: {execution_file}')
            
            # Read script content once
            with open(execution_file, 'r') as f:
                script_content = f.read()
            
            # Determine which hosts to execute on
            if target_type == 'host':
                execution_hosts = [host]
                logger.info(f'[SCRIPT] Target: Single host {host.ip}')
            else:  # group
                execution_hosts = list(hosts_in_group)
                logger.info(f'[SCRIPT] Target: Group with {len(execution_hosts)} hosts')
            
            # Prepare hosts data for Celery task
            hosts_data = []
            for exec_host in execution_hosts:
                exec_ansible_user = exec_host.ansible_user if exec_host.ansible_user else ansible_user
                exec_ssh_key = exec_host.ansible_ssh_private_key_file if exec_host.ansible_ssh_private_key_file else ssh_key_path
                hosts_data.append({
                    'name': exec_host.name,
                    'ip': exec_host.ip,
                    'ansible_user': exec_ansible_user,
                    'ssh_key': exec_ssh_key
                })
            
            # Dispatch to Celery
            task = execute_script_async.delay(
                history_id=history.id,
                script_content=script_content,
                hosts_data=hosts_data,
                ansible_user=ansible_user,
                ssh_key_path=ssh_key_path
            )
            
            history.celery_task_id = task.id
            history.save()
            
            logger.info(f'[SCRIPT] Dispatched to Celery: task_id={task.id}, history_id={history.id}')
            
            return JsonResponse({
                'success': True,
                'message': f'Script execution started in background',
                'task_id': task.id,
                'history_id': history.id,
                'async': True
            })
        
    except subprocess.TimeoutExpired:
        history.status = 'failed'
        history.ansible_output = 'Playbook execution timed out after 10 minutes'
        history.completed_at = timezone.now()
        history.save()
        
        # Send notification for timeout
        try:
            from notifications.utils import send_playbook_notification
            target_info = {'type': 'host', 'name': host.name}
            send_playbook_notification(history, request.user, target_info)
        except Exception as notif_error:
            logger.warning(f'Failed to send notification: {notif_error}')
        
        return JsonResponse({'success': False, 'error': 'Execution timed out'})
    
    except Exception as e:
        error_msg = str(e)
        error_trace = tb.format_exc()
        #error_trace = traceback.format_exc()
        logger.error(f'Error executing playbook: {error_msg}')
        logger.error(f'Traceback: {error_trace}')
        
        history.status = 'failed'
        history.ansible_output = f'Error: {error_msg}\n\nTraceback:\n{error_trace}'
        history.completed_at = timezone.now()
        history.save()
        
        # Send notification for error
        try:
            from notifications.utils import send_playbook_notification
            target_info = {'type': 'host', 'name': host.name}
            send_playbook_notification(history, request.user, target_info)
        except Exception as notif_error:
            logger.warning(f'Failed to send notification: {notif_error}')
        
        return JsonResponse({
            'success': False, 
            'error': error_msg,
            'traceback': error_trace
        })

@login_required
def get_playbooks(request):
    """Get playbooks filtered by target type and OS family"""
    target_type = request.GET.get('target_type')
    os_family = request.GET.get('os_family', 'linux')
    
    if not target_type:
        return JsonResponse({'playbooks': []})
    
    # Filter playbooks by type and OS
    playbooks = Playbook.objects.filter(
        playbook_type=target_type,
        os_family=os_family
    ).order_by('name')
    
    playbooks_data = [
        {
            'id': pb.id,
            'name': pb.name,
            'description': pb.description
        }
        for pb in playbooks
    ]
    
    return JsonResponse({'playbooks': playbooks_data})
