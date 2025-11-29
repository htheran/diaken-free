from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from inventory.models import Environment, Group, Host
from playbooks.models import Playbook
from settings.models import DeploymentCredential, GlobalSetting
from history.models import DeploymentHistory
import subprocess
import tempfile
import json
import os
import logging
import traceback
from .vcenter_snapshot import get_vcenter_connection, create_snapshot, Disconnect

logger = logging.getLogger(__name__)

@login_required
def execute_group_playbook(request):
    """Form to select environment, group, and playbook for group execution"""
    environments = Environment.objects.filter(active=True).order_by('name')
    groups = Group.objects.filter(active=True).order_by('name')
    playbooks = Playbook.objects.filter(playbook_type='group')
    
    context = {
        'environments': environments,
        'groups': groups,
        'playbooks': playbooks,
    }
    return render(request, 'deploy/execute_group_playbook.html', context)

@login_required
def execute_group_playbook_run(request):
    """Execute playbook on all hosts in a group"""
    if request.method != 'POST':
        return redirect('deploy:execute_group_playbook')
    
    # Get form data
    group_id = request.POST.get('group')
    playbook_id = request.POST.get('playbook')
    
    # Get and log snapshot flag
    create_snapshot_value = request.POST.get('create_snapshot')
    create_snapshot_flag = create_snapshot_value == '1'
    logger.info(f"[Group] Snapshot checkbox value received: '{create_snapshot_value}' (type: {type(create_snapshot_value).__name__})")
    logger.info(f"[Group] Snapshot flag evaluated to: {create_snapshot_flag}")
    
    try:
        group = Group.objects.get(pk=group_id)
        playbook = Playbook.objects.get(pk=playbook_id)
    except (Group.DoesNotExist, Playbook.DoesNotExist):
        return JsonResponse({'success': False, 'error': 'Group or Playbook not found'})
    
    # Get all active hosts in the group
    hosts = Host.objects.filter(group=group, active=True)
    
    if not hosts.exists():
        return JsonResponse({'success': False, 'error': 'No active hosts found in this group'})
    
    # Get SSH credentials
    ssh_cred = DeploymentCredential.objects.first()
    if not ssh_cred:
        return JsonResponse({'success': False, 'error': 'No SSH credentials configured'})
    
    # Create snapshots for all hosts if requested
    snapshots_created = []
    if create_snapshot_flag:
        try:
            # Get vCenter credentials from VCenterCredential model
            from settings.models import VCenterCredential
            
            # Always try to get credentials (we'll check per vCenter below)
            if True:
                # Group hosts by vCenter server
                vcenter_hosts = {}
                for host in hosts:
                    if host.vcenter_server:
                        if host.vcenter_server not in vcenter_hosts:
                            vcenter_hosts[host.vcenter_server] = []
                        vcenter_hosts[host.vcenter_server].append(host)
                
                # Create snapshots for each vCenter
                for vcenter_server, vcenter_host_list in vcenter_hosts.items():
                    try:
                        # Get credentials for this specific vCenter
                        vcenter_cred = VCenterCredential.objects.filter(host=vcenter_server).first()
                        
                        if not vcenter_cred:
                            logger.warning(f"vCenter credential not found for {vcenter_server}. Skipping snapshots for this vCenter.")
                            continue
                        
                        logger.info(f"Creating snapshots on vCenter: {vcenter_cred.name} ({vcenter_server})")
                        
                        si = get_vcenter_connection(
                            vcenter_server,
                            vcenter_cred.user,
                            vcenter_cred.get_password()
                        )
                        
                        for host in vcenter_host_list:
                            # Use local timezone for snapshot name
                            local_time = timezone.localtime(timezone.now())
                            snapshot_name = f"Before executing {playbook.name} - {local_time.strftime('%Y-%m-%d %H:%M:%S')}"
                            success, message, snap_id = create_snapshot(
                                si, host.ip, snapshot_name,
                                f"Safety snapshot before {playbook.name} on group {group.name}"
                            )
                            
                            if success:
                                snapshots_created.append(f"{host.name}: {snapshot_name}")
                                logger.info(f"Snapshot created for {host.name}: {snapshot_name}")
                                
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
                                        group=group,
                                        playbook=playbook,
                                        user=request.user,
                                        description=f"Safety snapshot before {playbook.name} on group {group.name}",
                                        retention_hours=retention_hours,
                                        status='active'
                                    )
                                    logger.info(f"Snapshot for {host.name} recorded in history with {retention_hours}h retention")
                                except Exception as hist_error:
                                    logger.error(f"Failed to record snapshot in history for {host.name}: {hist_error}")
                            else:
                                logger.warning(f"Failed to create snapshot for {host.name}: {message}")
                        
                        Disconnect(si)
                    except Exception as e:
                        logger.error(f"Exception creating snapshots on vCenter {vcenter_server}: {e}")
        except Exception as e:
            logger.error(f"Exception creating group snapshots: {e}")
            # Continue with playbook execution even if snapshots fail
    
    # Create deployment history record
    history = DeploymentHistory.objects.create(
        user=request.user,
        environment=group.environment.name if group.environment else '',
        target=group.name,
        target_type='Group',
        playbook=playbook.name,
        status='running',
        hostname=f'{group.name} ({hosts.count()} hosts)',
        ip_address=', '.join([h.ip for h in hosts[:3]]) + ('...' if hosts.count() > 3 else '')
    )
    
    try:
        # Create Ansible inventory file with all hosts in the group
        # Use 'target_group' as the group name so playbooks can reference it consistently
        inventory_lines = ['[target_group]']
        
        for host in hosts:
            inventory_vars = [
                f"ansible_host={host.ip}",
                f"ansible_user={ssh_cred.user}",
                f"ansible_ssh_private_key_file={ssh_cred.ssh_key_file_path}",
                "ansible_ssh_common_args='-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'"
            ]
            
            # Add Python interpreter if configured
            if host.ansible_python_interpreter:
                inventory_vars.append(f"ansible_python_interpreter={host.ansible_python_interpreter}")
            
            inventory_lines.append(f"{host.name} {' '.join(inventory_vars)}")
        
        # Add group variables section
        inventory_lines.append('')
        inventory_lines.append('[target_group:vars]')
        inventory_lines.append(f'group_name={group.name}')
        inventory_lines.append(f'target_environment={group.environment.name if group.environment else ""}')
        
        inventory_content = '\n'.join(inventory_lines)
        inventory_path = f'/tmp/ansible_inventory_group_{history.id}.ini'
        
        with open(inventory_path, 'w') as f:
            f.write(inventory_content)
        
        logger.info(f'[GROUP] Created inventory: {inventory_path}')
        logger.info(f'[GROUP] Inventory content:\n{inventory_content}')
        
        # Get global settings for extra vars
        global_settings = GlobalSetting.objects.all()
        extra_vars = {
            'group_name': group.name,
            'target_environment': group.environment.name if group.environment else '',
            'host_count': hosts.count()
        }
        for setting in global_settings:
            extra_vars[setting.key] = setting.value
        
        # Add common aliases for backward compatibility
        if 'log_dir_update' in extra_vars and 'log_dir' not in extra_vars:
            extra_vars['log_dir'] = extra_vars['log_dir_update']
        
        logger.info(f'[GROUP] Extra vars: {extra_vars}')
        
        # Convert extra_vars to JSON string
        extra_vars_json = json.dumps(extra_vars)
        
        # Execute playbook
        cmd = [
            settings.ANSIBLE_PLAYBOOK_PATH,
            '-i', inventory_path,
            playbook.file.path,
            '--extra-vars', extra_vars_json,
            '-v'
        ]
        
        logger.info(f'[GROUP] Executing: {" ".join(cmd)}')
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes timeout
        )
        
        # Combine output
        full_output = result.stdout + '\n' + result.stderr
        
        # Determine success by checking PLAY RECAP for failed tasks
        is_success = False
        if 'PLAY RECAP' in full_output:
            import re
            # Look for patterns like "failed=0" and "unreachable=0"
            # Check all hosts in the recap
            failed_match = re.findall(r'failed=(\d+)', full_output)
            unreachable_match = re.findall(r'unreachable=(\d+)', full_output)
            
            total_failed = sum(int(x) for x in failed_match)
            total_unreachable = sum(int(x) for x in unreachable_match)
            
            is_success = (total_failed == 0 and total_unreachable == 0)
        else:
            # Fallback to returncode if no PLAY RECAP found
            is_success = (result.returncode == 0)
        
        # Update history with results
        history.status = 'success' if is_success else 'failed'
        history.ansible_output = full_output
        history.completed_at = timezone.now()
        history.save()
        
        # Send notification
        try:
            from notifications.utils import send_playbook_notification
            target_info = {
                'type': 'group',
                'name': group.name
            }
            send_playbook_notification(history, request.user, target_info)
        except Exception as notif_error:
            logger.warning(f'Failed to send notification: {notif_error}')
        
        # Clean up inventory file
        try:
            os.remove(inventory_path)
            logger.info(f'[GROUP] Cleaned up inventory: {inventory_path}')
        except Exception as e:
            logger.warning(f'[GROUP] Failed to clean up inventory: {e}')
        
        return JsonResponse({
            'success': True,
            'status': history.status,
            'output': full_output,
            'history_id': history.id
        })
        
    except subprocess.TimeoutExpired:
        history.status = 'failed'
        history.ansible_output = 'Playbook execution timed out after 10 minutes'
        history.completed_at = timezone.now()
        history.save()
        
        # Send notification for timeout
        try:
            from notifications.utils import send_playbook_notification
            target_info = {'type': 'group', 'name': group.name}
            send_playbook_notification(history, request.user, target_info)
        except Exception as notif_error:
            logger.warning(f'Failed to send notification: {notif_error}')
        
        return JsonResponse({
            'success': False,
            'error': 'Playbook execution timed out'
        })
        
    except Exception as e:
        logger.error(f'[GROUP] Error executing playbook: {e}')
        logger.error(traceback.format_exc())
        
        history.status = 'failed'
        history.ansible_output = f'Error: {str(e)}\n\n{traceback.format_exc()}'
        history.completed_at = timezone.now()
        history.save()
        
        # Send notification for error
        try:
            from notifications.utils import send_playbook_notification
            target_info = {'type': 'group', 'name': group.name}
            send_playbook_notification(history, request.user, target_info)
        except Exception as notif_error:
            logger.warning(f'Failed to send notification: {notif_error}')
        
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
