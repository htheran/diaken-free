from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.utils.safestring import mark_safe
from inventory.models import Environment, Group, Host
from playbooks.models import Playbook
from history.models import DeploymentHistory
from snapshots.models import SnapshotHistory
from settings.models import WindowsCredential, GlobalSetting, VCenterCredential
import subprocess
import json
import logging
import traceback
import tempfile
from django.conf import settings
import os
from django.utils import timezone
from datetime import timedelta
from .vcenter_snapshot import get_vcenter_connection, create_snapshot, Disconnect

logger = logging.getLogger(__name__)

@login_required
def deploy_playbook_windows(request):
    """Form to select host/group and playbook to execute on Windows"""
    environments = Environment.objects.filter(active=True).order_by('name')
    groups = Group.objects.filter(active=True).order_by('name')
    hosts = Host.objects.filter(active=True, operating_system='windows').order_by('name')
    
    # Get Windows playbooks (both host and group)
    playbooks_host = Playbook.objects.filter(playbook_type='host', os_family='windows').order_by('name')
    playbooks_group = Playbook.objects.filter(playbook_type='group', os_family='windows').order_by('name')
    
    context = {
        'environments': environments,
        'groups': groups,
        'hosts': hosts,
        'playbooks_host': playbooks_host,
        'playbooks_group': playbooks_group,
    }
    return render(request, 'deploy/deploy_playbook_windows_form.html', context)

@login_required
def execute_playbook_windows(request):
    """Execute selected playbook on selected Windows host or group"""
    if request.method != 'POST':
        return redirect('deploy:deploy_playbook_windows')
    
    # Get form data
    target_type = request.POST.get('target_type')  # 'host' or 'group'
    execution_type = request.POST.get('execution_type', 'playbook')  # 'playbook' or 'script'
    host_id = request.POST.get('host')
    group_id = request.POST.get('group')
    playbook_id = request.POST.get('playbook')
    script_id = request.POST.get('script')
    
    # Get and log snapshot flag (only for hosts)
    create_snapshot_value = request.POST.get('create_snapshot')
    create_snapshot_flag = create_snapshot_value == '1'
    logger.info(f"[WINDOWS-PLAYBOOK] Target type: {target_type}")
    logger.info(f"[WINDOWS-PLAYBOOK] Snapshot checkbox value: '{create_snapshot_value}'")
    logger.info(f"[WINDOWS-PLAYBOOK] Snapshot flag evaluated to: {create_snapshot_flag}")
    
    scheduled = request.POST.get('scheduled') == '1'
    scheduled_time = request.POST.get('scheduled_time') if scheduled else None
    
    try:
        # Get playbook or script based on execution type
        if execution_type == 'script':
            from scripts.models import Script
            if not script_id:
                return JsonResponse({'success': False, 'error': 'Script is required'})
            script = Script.objects.get(pk=script_id)
            execution_name = script.name
            execution_file = script.file_path
            playbook = None  # No playbook for script execution
        else:
            if not playbook_id:
                return JsonResponse({'success': False, 'error': 'Playbook is required'})
            playbook = Playbook.objects.get(pk=playbook_id)
            execution_name = playbook.name
            execution_file = playbook.file.path
            script = None
        
        # Validate target type matches playbook type
        if target_type == 'host':
            if not host_id:
                return JsonResponse({'success': False, 'error': 'Host is required'})
            host = Host.objects.get(pk=host_id)
            target_name = host.name
            target_ip = host.ip
            vcenter_server = host.vcenter_server
            
            # Get Windows credentials - prioritize direct fields over credential object
            if host.windows_user and host.windows_password:
                windows_user = host.windows_user
                windows_password = host.windows_password
                windows_auth_type = 'ntlm'  # Default
                windows_port = 5985  # Default
            elif host.windows_credential:
                windows_user = host.windows_credential.username
                windows_password = host.windows_credential.get_password()
                windows_auth_type = host.windows_credential.auth_type
                windows_port = host.windows_credential.get_port()
            else:
                return JsonResponse({'success': False, 'error': 'No Windows credentials configured for host. Please set windows_user and windows_password or assign a Windows credential.'})
            
            # Validate playbook type only for playbook execution
            if execution_type == 'playbook' and playbook and playbook.playbook_type != 'host':
                return JsonResponse({'success': False, 'error': 'Selected playbook is not for hosts'})
                
        elif target_type == 'group':
            if not group_id:
                return JsonResponse({'success': False, 'error': 'Group is required'})
            group = Group.objects.get(pk=group_id)
            target_name = group.name
            target_ip = None  # Groups don't have single IP
            
            # Validate playbook type only for playbook execution
            if execution_type == 'playbook' and playbook and playbook.playbook_type != 'group':
                return JsonResponse({'success': False, 'error': 'Selected playbook is not for groups'})
            
            # For group, we'll use the first host's credential as default
            hosts_in_group = Host.objects.filter(group=group, active=True, operating_system='windows')
            if not hosts_in_group.exists():
                return JsonResponse({'success': False, 'error': 'No Windows hosts found in group'})
            
            first_host = hosts_in_group.first()
            vcenter_server = first_host.vcenter_server
            
            # Get Windows credentials from first host
            if first_host.windows_user and first_host.windows_password:
                windows_user = first_host.windows_user
                windows_password = first_host.windows_password
                windows_auth_type = 'ntlm'
                windows_port = 5985
            elif first_host.windows_credential:
                windows_user = first_host.windows_credential.username
                windows_password = first_host.windows_credential.get_password()
                windows_auth_type = first_host.windows_credential.auth_type
                windows_port = first_host.windows_credential.get_port()
            else:
                return JsonResponse({'success': False, 'error': 'No Windows credentials configured for group hosts'})
        
        # Create snapshots for all hosts in group if requested
        snapshots_created = []
        if create_snapshot_flag and target_type == 'group':
            try:
                logger.info(f'[WINDOWS-GROUP] Creating snapshots for group {group.name}...')
                
                # Group hosts by vCenter server
                from collections import defaultdict
                hosts_by_vcenter = defaultdict(list)
                for h in hosts_in_group:
                    if h.vcenter_server:
                        hosts_by_vcenter[h.vcenter_server].append(h)
                
                # Create snapshots for each vCenter
                for vcenter_server, vcenter_hosts in hosts_by_vcenter.items():
                    try:
                        vcenter_cred = VCenterCredential.objects.filter(host=vcenter_server).first()
                        if not vcenter_cred:
                            logger.warning(f"vCenter credential not found for {vcenter_server}. Skipping snapshots for this vCenter.")
                            continue
                        
                        logger.info(f"Creating snapshots on vCenter: {vcenter_cred.name} ({vcenter_server})")
                        si = get_vcenter_connection(vcenter_server, vcenter_cred.user, vcenter_cred.get_password())
                        
                        if si:
                            for host in vcenter_hosts:
                                try:
                                    # Use local timezone for snapshot name
                                    local_time = timezone.localtime(timezone.now())
                                    snapshot_name = f"Before executing {execution_name} - {local_time.strftime('%Y-%m-%d %H:%M:%S')}"
                                    success, message, snap_id = create_snapshot(
                                        si, host.ip, snapshot_name,
                                        f"Safety snapshot before {execution_name} on group {group.name}"
                                    )
                                    
                                    if success:
                                        snapshots_created.append(f"{host.name}: {snapshot_name}")
                                        logger.info(f"Snapshot created for {host.name}: {snapshot_name}")
                                        
                                        # Record snapshot in history
                                        try:
                                            from snapshots.models import SnapshotHistory
                                            from settings.models import GlobalSetting
                                            
                                            retention_setting = GlobalSetting.objects.filter(key='snapshot_retention_hours').first()
                                            retention_hours = int(retention_setting.value) if retention_setting else 24
                                            
                                            SnapshotHistory.objects.create(
                                                snapshot_name=snapshot_name,
                                                vcenter_snapshot_id=snap_id,
                                                host=host,
                                                vcenter_server=vcenter_server,
                                                created_by=request.user,
                                                retention_hours=retention_hours,
                                                description=f"Safety snapshot before {execution_name} on group {group.name}",
                                                auto_delete=True
                                            )
                                            
                                            logger.info(f"Snapshot for {host.name} recorded in history with {retention_hours}h retention")
                                        except Exception as hist_error:
                                            logger.error(f"Failed to record snapshot in history for {host.name}: {hist_error}")
                                    else:
                                        logger.warning(f"Failed to create snapshot for {host.name}: {message}")
                                        
                                except Exception as e:
                                    logger.error(f"Exception creating snapshot for {host.name}: {e}")
                            
                            Disconnect(si)
                    except Exception as e:
                        logger.error(f"Exception creating snapshots on vCenter {vcenter_server}: {e}")
            except Exception as e:
                logger.error(f"Exception creating group snapshots: {e}")
                # Continue with playbook execution even if snapshots fail
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
                    playbook=playbook,
                    script=script if execution_type == 'script' else None,
                    execution_type=execution_type,
                    os_family='windows',
                    create_snapshot=create_snapshot_flag,
                    scheduled_datetime=scheduled_dt,
                    status='pending'
                )
                
                logger.info(f"[WINDOWS-{execution_type.upper()}] Scheduled task created: {task.id} for {scheduled_dt}")
                
                return JsonResponse({
                    'success': True,
                    'scheduled': True,
                    'task_id': task.id,
                    'scheduled_time': scheduled_dt.strftime('%Y-%m-%d %H:%M:%S'),
                    'output': f"Task scheduled successfully for {scheduled_dt.strftime('%Y-%m-%d %H:%M:%S')}\n\nTask ID: {task.id}\n{execution_type.capitalize()}: {execution_name}\nTarget: {target_name}"
                })
            except Exception as e:
                logger.error(f"[WINDOWS-PLAYBOOK] Error creating scheduled task: {str(e)}")
                return JsonResponse({'success': False, 'error': f'Failed to schedule task: {str(e)}'})
        
        # Create history record
        history_record = DeploymentHistory.objects.create(
            user=request.user,
            environment=host.environment.name if target_type == 'host' else group.environment.name,
            target=target_name,
            target_type='Host' if target_type == 'host' else 'Group',
            playbook=execution_name,
            status='running',
            hostname=target_name,
            ip_address=target_ip if target_ip else 'N/A'
        )
        
        logger.info(f'[WINDOWS-{execution_type.upper()}] Executing {execution_name} on {target_type} {target_name}')
        
        # Create snapshot if requested (only for immediate execution, not scheduled)
        # For scheduled tasks, the snapshot will be created by the scheduler when the task runs
        snapshot_name = None
        snapshot_created = False
        logger.info(f'[WINDOWS-PLAYBOOK] Snapshot check - Flag: {create_snapshot_flag}, Scheduled: {scheduled}, will_create_now={create_snapshot_flag and not scheduled}, Target type: {target_type}, Has vCenter: {bool(vcenter_server)}')
        
        if create_snapshot_flag and not scheduled and target_type == 'host' and vcenter_server:
            try:
                logger.info(f'[WINDOWS-PLAYBOOK] Creating snapshot for {target_name}...')
                # Get vCenter credentials
                vcenter_cred = VCenterCredential.objects.filter(host=vcenter_server).first()
                if vcenter_cred:
                    logger.info(f'[WINDOWS-PLAYBOOK] vCenter credentials found')
                    si = get_vcenter_connection(vcenter_server, vcenter_cred.user, vcenter_cred.get_password())
                    if si:
                        # Use local timezone for snapshot name
                        local_time = timezone.localtime(timezone.now())
                        snapshot_name = f"Before executing {execution_name} - {local_time.strftime('%Y-%m-%d %H:%M:%S')}"
                        
                        logger.info(f'[WINDOWS-{execution_type.upper()}] Connected to vCenter, searching for VM...')
                        
                        # Try to find and snapshot VM by IP first, then by hostname
                        vm_identifier = target_ip  # Try IP first
                        success, message, snap_id = create_snapshot(
                            si, 
                            vm_identifier, 
                            snapshot_name, 
                            f"Safety snapshot before {execution_name}"
                        )
                        
                        # If VM not found by IP, try by hostname
                        if not success and "not found" in message.lower():
                            logger.info(f'[WINDOWS-PLAYBOOK] VM not found by IP, trying by hostname...')
                            success, message, snap_id = create_snapshot(
                                si, 
                                target_name,  # Try hostname
                                snapshot_name, 
                                f"Safety snapshot before {execution_name}"
                            )
                        
                        Disconnect(si)
                        
                        if success:
                            snapshot_created = True
                            logger.info(f'[WINDOWS-PLAYBOOK] ✓ Snapshot created successfully: {snapshot_name}')
                            
                            # Save snapshot name in deployment history
                            history_record.snapshot_name = snapshot_name
                            history_record.save()
                            
                            # Get retention hours from settings (default 24 hours)
                            retention_setting = GlobalSetting.objects.filter(key='snapshot_retention_hours').first()
                            retention_hours = int(retention_setting.value) if retention_setting and retention_setting.value else 24
                            
                            # Create SnapshotHistory record for cleanup script
                            # Note: expires_at is calculated automatically by the model's save() method
                            SnapshotHistory.objects.create(
                                snapshot_name=snapshot_name,
                                vcenter_snapshot_id=snap_id,
                                host=host,
                                playbook=playbook,  # Can be None for script execution
                                user=request.user,
                                description=f"Safety snapshot before {execution_name}",
                                retention_hours=retention_hours,
                                status='active'
                            )
                            logger.info(f'[WINDOWS-{execution_type.upper()}] Snapshot registered for auto-cleanup in {retention_hours}h')
                        else:
                            logger.error(f'[WINDOWS-PLAYBOOK] Snapshot creation failed: {message}')
                    else:
                        logger.error(f'[WINDOWS-PLAYBOOK] Failed to connect to vCenter')
                else:
                    logger.warning(f'[WINDOWS-PLAYBOOK] No vCenter credentials found')
            except Exception as e:
                logger.error(f'[WINDOWS-PLAYBOOK] Could not create snapshot: {e}')
                logger.error(traceback.format_exc())
        elif not create_snapshot_flag:
            logger.info(f'[WINDOWS-PLAYBOOK] Snapshot NOT requested (checkbox not marked)')
        elif target_type != 'host':
            logger.info(f'[WINDOWS-PLAYBOOK] Snapshot skipped (target is group, not host)')
        elif not vcenter_server:
            logger.warning(f'[WINDOWS-PLAYBOOK] Snapshot skipped (no vCenter server configured for {target_name})')
        
        # Create temporary inventory file
        # Use [windows_hosts:vars] format (same as deployment) for better compatibility
        inventory_content = ''
        if target_type == 'host':
            # Using vars section format with hostname as alias for better visual identification
            # Get hostname from the host object
            hostname_alias = host.name if host.name else target_ip
            inventory_content = f'''[windows_hosts]
{hostname_alias} ansible_host={target_ip}

[windows_hosts:vars]
ansible_user={windows_user}
ansible_password={windows_password}
ansible_connection=winrm
ansible_winrm_transport={windows_auth_type}
ansible_winrm_server_cert_validation=ignore
ansible_port={windows_port}
ansible_winrm_read_timeout_sec=300
ansible_winrm_operation_timeout_sec=240
'''
        else:  # group
            # For groups, list all IPs with hostname as alias for better visual identification
            inventory_content = '[windows_group]\n'
            for h in hosts_in_group:
                # Use hostname as alias if available, otherwise just use IP
                if h.name:
                    inventory_content += f'{h.name} ansible_host={h.ip}\n'
                else:
                    inventory_content += f'{h.ip}\n'
            
            # Use first host's credentials for group vars
            inventory_content += f'''\n[windows_group:vars]
ansible_user={windows_user}
ansible_password={windows_password}
ansible_connection=winrm
ansible_winrm_transport={windows_auth_type}
ansible_winrm_server_cert_validation=ignore
ansible_port={windows_port}
ansible_winrm_read_timeout_sec=300
ansible_winrm_operation_timeout_sec=240
'''
        
        # Write inventory to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            f.write(inventory_content)
            inventory_path = f.name
        
        logger.info(f'[WINDOWS-{execution_type.upper()}] Inventory created at {inventory_path}')
        logger.info(f'[WINDOWS-{execution_type.upper()}] Inventory content:\n{inventory_content}')
        
        # Execute playbook or script
        playbook_content = None
        playbook_path = None
        
        if execution_type == 'script':
            # For scripts, create playbook content that executes the script
            playbook_content = f'''---
- name: Execute PowerShell Script
  hosts: windows_hosts
  gather_facts: no
  tasks:
    - name: Execute {script.name}
      win_shell: |
'''
            # Read script content and indent it
            with open(script.file_path, 'r') as f:
                script_lines = f.readlines()
                for line in script_lines:
                    playbook_content += f'        {line}'
            
            playbook_content += '''
      register: script_output
    
    - name: Display output
      debug:
        var: script_output
'''
            
            logger.info(f'[WINDOWS-SCRIPT] Playbook content created for script: {script.name}')
        else:
            # For playbooks, use the playbook file directly
            playbook_path = playbook.file.path
            logger.info(f'[WINDOWS-PLAYBOOK] Using playbook file: {playbook_path}')
        
        # Execute asynchronously with Celery
        from deploy.tasks import execute_windows_playbook_async
        
        logger.info(f'[WINDOWS-ASYNC] Dispatching Celery task for Windows {execution_type} execution')
        logger.info(f'[WINDOWS-ASYNC] History ID: {history_record.id}')
        
        # Dispatch to Celery with either playbook_path or playbook_content
        celery_task = execute_windows_playbook_async.delay(
            history_id=history_record.id,
            inventory_content=inventory_content,
            execution_file=playbook_path,
            playbook_content=playbook_content,
            windows_user=windows_user,
            windows_password=windows_password,
            auth_type=windows_auth_type,
            port=windows_port
        )
        
        logger.info(f'[WINDOWS-ASYNC] Celery task dispatched: {celery_task.id}')
        
        # Update history with task ID
        history_record.celery_task_id = celery_task.id
        history_record.status = 'running'
        history_record.save()
        
        # Return immediately with task info
        return JsonResponse({
            'success': True,
            'message': f'Windows {execution_type} execution started in background',
            'task_id': celery_task.id,
            'history_id': history_record.id,
            'async': True
        })
            
    except Exception as e:
        logger.error(f'[WINDOWS-PLAYBOOK] Error: {str(e)}')
        logger.error(traceback.format_exc())
        
        if 'history_record' in locals():
            history_record.status = 'failed'
            history_record.ansible_output = f'Exception: {str(e)}\n\n{traceback.format_exc()}'
            history_record.completed_at = timezone.now()
            history_record.save()
            
            # Send notification for exception
            try:
                from notifications.utils import send_playbook_notification
                target_info = {'type': target_type, 'name': target_name}
                send_playbook_notification(history_record, request.user, target_info, os_type='windows')
            except Exception as notif_error:
                logger.warning(f'Failed to send notification: {notif_error}')
        
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
