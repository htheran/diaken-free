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
import traceback
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
    # Filter only Linux hosts
    hosts = Host.objects.filter(active=True, operating_system='linux').order_by('name')
    # Playbooks will be loaded dynamically based on target_type
    
    context = {
        'environments': environments,
        'groups': groups,
        'hosts': hosts,
    }
    return render(request, 'deploy/deploy_playbook_form.html', context)

@login_required
def execute_playbook(request):
    """Execute selected playbook on selected host"""
    if request.method != 'POST':
        return redirect('deploy_playbook')
    
    # Get form data
    host_id = request.POST.get('host')
    playbook_id = request.POST.get('playbook')
    
    # Get and log snapshot flag
    create_snapshot_value = request.POST.get('create_snapshot')
    create_snapshot_flag = create_snapshot_value == '1'
    logger.info(f"Snapshot checkbox value received: '{create_snapshot_value}' (type: {type(create_snapshot_value).__name__})")
    logger.info(f"Snapshot flag evaluated to: {create_snapshot_flag}")
    
    try:
        host = Host.objects.get(pk=host_id)
        playbook = Playbook.objects.get(pk=playbook_id)
    except (Host.DoesNotExist, Playbook.DoesNotExist):
        return JsonResponse({'success': False, 'error': 'Host or Playbook not found'})
    
    # Get SSH credentials - use host's credential if configured, otherwise use first available
    ssh_cred = host.deployment_credential if host.deployment_credential else DeploymentCredential.objects.first()
    if not ssh_cred:
        return JsonResponse({'success': False, 'error': 'No SSH credentials configured. Please assign a deployment credential to the host or create one in Settings.'})
    
    # Create snapshot if requested
    snapshot_created = False
    snapshot_name = None
    snapshot_info = ""
    
    if create_snapshot_flag:
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
                    snapshot_name = f"Before executing {playbook.name} - {local_time.strftime('%Y-%m-%d %H:%M:%S')}"
                    
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
                    
                    success, message, snap_id = create_snapshot(si, host.ip, snapshot_name, f"Safety snapshot before {playbook.name}")
                    
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
                                playbook=playbook,
                                user=request.user,
                                description=f"Safety snapshot before {playbook.name}",
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
    
    # Create deployment history record
    history = DeploymentHistory.objects.create(
        user=request.user,
        environment=host.environment.name if host.environment else '',
        target=host.name,
        target_type='Host',
        playbook=playbook.name,
        status='running',
        hostname=host.name,
        ip_address=host.ip
    )
    
    try:
        # Create Ansible inventory file
        # Build inventory line with host variables
        # Priority order for ansible_user: host.ansible_user > credential.user
        ansible_user = host.ansible_user if host.ansible_user else ssh_cred.user
        # Priority order for SSH key: host.ansible_ssh_private_key_file > credential.ssh_key_file_path
        ssh_key_path = host.ansible_ssh_private_key_file if host.ansible_ssh_private_key_file else ssh_cred.ssh_key_file_path
        
        logger.info(f'[PLAYBOOK] Using ansible_user: {ansible_user}')
        logger.info(f'[PLAYBOOK] Using SSH key: {ssh_key_path}')
        logger.info(f'[PLAYBOOK] Using credential: {ssh_cred.name}')
        
        inventory_vars = [
            f"ansible_user={ansible_user}",
            f"ansible_ssh_private_key_file={ssh_key_path}",
            "ansible_ssh_common_args='-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'"
        ]
        
        # Add Python interpreter if configured
        if host.ansible_python_interpreter:
            inventory_vars.append(f"ansible_python_interpreter={host.ansible_python_interpreter}")
        
        inventory_line = f"{host.ip} {' '.join(inventory_vars)}"
        inventory_content = f"""[target_host]
{inventory_line}
"""
        inventory_path = f'/tmp/ansible_inventory_{history.id}.ini'
        with open(inventory_path, 'w') as f:
            f.write(inventory_content)
        
        # Get global settings for extra vars
        global_settings = GlobalSetting.objects.all()
        extra_vars = {'target_host': host.ip, 'inventory_hostname': host.name}
        for setting in global_settings:
            extra_vars[setting.key] = setting.value
        
        # Convert extra_vars to JSON string
        extra_vars_json = json.dumps(extra_vars)
        
        # Execute playbook
        cmd = [
            'ansible-playbook',
            '-i', inventory_path,
            playbook.file.path,
            '--extra-vars', extra_vars_json,
            '-v'
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes timeout
        )
        
        # Combine output
        full_output = result.stdout + '\n' + result.stderr
        
        # Determine success by checking PLAY RECAP for failed tasks
        # Look for "failed=0" and "unreachable=0" in the output
        is_success = False
        if 'PLAY RECAP' in full_output:
            # Check if there are no failures or unreachable hosts
            import re
            # Look for patterns like "failed=0" and "unreachable=0"
            failed_match = re.search(r'failed=(\d+)', full_output)
            unreachable_match = re.search(r'unreachable=(\d+)', full_output)
            
            failed_count = int(failed_match.group(1)) if failed_match else 0
            unreachable_count = int(unreachable_match.group(1)) if unreachable_match else 0
            
            is_success = (failed_count == 0 and unreachable_count == 0)
        else:
            # Fallback to returncode if no PLAY RECAP found
            is_success = (result.returncode == 0)
        
        # Update history with results
        history.status = 'success' if is_success else 'failed'
        history.ansible_output = full_output
        history.completed_at = timezone.now()
        history.save()
        
        # Clean up inventory file
        import os
        os.remove(inventory_path)
        
        return JsonResponse({
            'success': True,
            'history_id': history.id,
            'status': history.status,
            'output': history.ansible_output
        })
        
    except subprocess.TimeoutExpired:
        history.status = 'failed'
        history.ansible_output = 'Playbook execution timed out after 10 minutes'
        history.completed_at = timezone.now()
        history.save()
        return JsonResponse({'success': False, 'error': 'Execution timed out'})
    
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        logger.error(f'Error executing playbook: {error_msg}')
        logger.error(f'Traceback: {error_trace}')
        
        history.status = 'failed'
        history.ansible_output = f'Error: {error_msg}\n\nTraceback:\n{error_trace}'
        history.completed_at = timezone.now()
        history.save()
        
        return JsonResponse({
            'success': False, 
            'error': error_msg,
            'traceback': error_trace
        })
