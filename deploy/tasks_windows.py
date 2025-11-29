"""
Celery task for Windows VM deployment (asynchronous)
"""
from celery import shared_task
from django.utils import timezone
from django.conf import settings
import logging
import time
import socket
import ssl
import winrm
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim

logger = logging.getLogger('deploy.tasks')


@shared_task(
    bind=True,
    name='deploy.tasks.provision_windows_vm_async',
    time_limit=1800,  # 30 minutes hard limit
    soft_time_limit=1680  # 28 minutes soft limit
)
def provision_windows_vm_async(
    self,
    history_id,
    template_ip,
    new_ip,
    new_hostname,
    gateway,
    dns1,
    dns2,
    vcenter_host,
    vcenter_user,
    vcenter_password,
    datacenter,
    cluster,
    network_name,
    windows_user,
    windows_password,
    windows_auth_type,
    windows_port,
    deploy_env,
    deploy_group,
    template_name
):
    """
    Execute Windows VM provisioning asynchronously using Celery.
    
    This allows the frontend to show real-time progress while the deployment runs in background.
    """
    from history.models import DeploymentHistory
    from inventory.models import Host, Environment, Group
    from settings.models import WindowsCredential
    
    try:
        # Get history record
        history_record = DeploymentHistory.objects.get(pk=history_id)
        history_record.status = 'running'
        history_record.celery_task_id = self.request.id
        history_record.save()
        
        logger.info(f'[CELERY-WINDOWS-{self.request.id}] Starting Windows VM provisioning')
        logger.info(f'[CELERY-WINDOWS-{self.request.id}] Target: {new_hostname} ({new_ip})')
        
        output_buffer = []
        
        def update_output(message):
            """Helper to update output incrementally"""
            output_buffer.append(message)
            history_record.ansible_output = '\n'.join(output_buffer)
            history_record.save(update_fields=['ansible_output'])
            logger.info(f'[CELERY-WINDOWS-{self.request.id}] {message}')
        
        update_output(f'=== WINDOWS VM PROVISIONING ===')
        update_output(f'Hostname: {new_hostname}')
        update_output(f'IP: {new_ip}')
        update_output(f'Gateway: {gateway}')
        update_output(f'Network: {network_name}')
        update_output('')
        
        # Step 1: Wait for VM to boot
        update_output('Step 1/8: Waiting 30 seconds for Windows to boot...')
        time.sleep(30)
        update_output('✓ Boot wait completed')
        update_output('')
        
        # Step 2: Test WinRM connectivity to template IP
        update_output(f'Step 2/8: Testing WinRM connectivity to {template_ip}...')
        max_retries = 6
        connected = False
        
        for i in range(max_retries):
            try:
                endpoint = f'http://{template_ip}:{windows_port}/wsman' if windows_auth_type != 'ssl' else f'https://{template_ip}:{windows_port}/wsman'
                session = winrm.Session(
                    endpoint,
                    auth=(windows_user, windows_password),
                    transport=windows_auth_type,
                    server_cert_validation='ignore'
                )
                result = session.run_cmd('hostname')
                if result.status_code == 0:
                    connected = True
                    update_output(f'✓ WinRM connected successfully (attempt {i+1}/{max_retries})')
                    break
            except Exception as e:
                update_output(f'  Attempt {i+1}/{max_retries} failed: {str(e)[:100]}')
                time.sleep(10)
        
        if not connected:
            update_output('❌ ERROR: Could not connect to VM via WinRM')
            history_record.status = 'failed'
            history_record.completed_at = timezone.now()
            history_record.save()
            return {'status': 'failed', 'error': 'WinRM connection failed'}
        
        update_output('')
        
        # Step 3: Execute Ansible playbook
        update_output('Step 3/8: Executing Ansible playbook for Windows configuration...')
        update_output(f'  - Changing hostname to: {new_hostname}')
        update_output(f'  - Configuring IP: {new_ip}')
        update_output(f'  - Gateway: {gateway}')
        update_output('')
        
        # Create inventory
        inventory_content = f"""[windows_hosts]
{template_ip}

[windows_hosts:vars]
ansible_user={windows_user}
ansible_password={windows_password}
ansible_connection=winrm
ansible_winrm_transport={windows_auth_type}
ansible_winrm_server_cert_validation=ignore
ansible_port={windows_port}
"""
        
        inventory_path = f'/tmp/ansible_inventory_windows_{new_hostname}.ini'
        with open(inventory_path, 'w') as f:
            f.write(inventory_content)
        
        # Execute playbook with real-time output
        import subprocess
        import os
        cmd = [
            settings.ANSIBLE_PLAYBOOK_PATH,
            '-vv',
            '-i', inventory_path,
            os.path.join(settings.BASE_DIR, 'ansible', 'provision_windows_vm.yml'),
            '-e', f'hostname={new_hostname}',
            '-e', f'ip={new_ip}',
            '-e', f'gateway={gateway}',
            '-e', f'winrm_transport={windows_auth_type}',
            '-e', f'dns1={dns1}',
            '-e', f'dns2={dns2}'
        ]
        
        update_output('Executing Ansible playbook...')
        update_output('')
        
        # Use Popen for real-time output
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        line_count = 0
        for line in process.stdout:
            output_buffer.append(line.rstrip())
            line_count += 1
            
            # Update DB every 5 lines
            if line_count % 5 == 0:
                history_record.ansible_output = '\n'.join(output_buffer)
                history_record.save(update_fields=['ansible_output'])
        
        return_code = process.wait(timeout=600)
        
        # Final update
        history_record.ansible_output = '\n'.join(output_buffer)
        history_record.save(update_fields=['ansible_output'])
        
        update_output('')
        update_output(f'Ansible playbook completed with return code: {return_code}')
        
        if return_code != 0:
            update_output('❌ ERROR: Ansible playbook failed')
            history_record.status = 'failed'
            history_record.completed_at = timezone.now()
            history_record.save()
            return {'status': 'failed', 'error': 'Ansible playbook failed'}
        
        update_output('✓ Ansible playbook completed successfully')
        update_output('')
        
        # Cleanup inventory
        try:
            import os
            os.remove(inventory_path)
        except Exception as e:
            pass
        
        # Step 4: Wait for VM shutdown
        update_output('Step 4/8: Waiting 50 seconds for VM to shutdown...')
        time.sleep(50)
        update_output('✓ Shutdown wait completed')
        update_output('')
        
        # Step 5: Change network in vCenter
        update_output(f'Step 5/8: Changing network to {network_name} in vCenter...')
        network_changed = False
        
        try:
            context = ssl._create_unverified_context()
            si = SmartConnect(
                host=vcenter_host,
                user=vcenter_user,
                pwd=vcenter_password,
                sslContext=context
            )
            content = si.RetrieveContent()
            
            # Find VM
            vm_to_update = next((vm for vm in content.viewManager.CreateContainerView(
                content.rootFolder, [vim.VirtualMachine], True).view 
                if vm.name == new_hostname), None)
            
            if vm_to_update:
                update_output(f'  ✓ VM found: {vm_to_update.name}')
                
                # Find network
                target_net = next((n for n in content.viewManager.CreateContainerView(
                    content.rootFolder, [vim.Network], True).view 
                    if n.name == network_name), None)
                
                if target_net:
                    update_output(f'  ✓ Network found: {target_net.name}')
                    
                    # Change network for first NIC
                    for device in vm_to_update.config.hardware.device:
                        if isinstance(device, vim.vm.device.VirtualEthernetCard):
                            nic_spec = vim.vm.device.VirtualDeviceSpec()
                            nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
                            nic_spec.device = device
                            
                            if isinstance(target_net, vim.dvs.DistributedVirtualPortgroup):
                                dvs_port_connection = vim.dvs.PortConnection()
                                dvs_port_connection.portgroupKey = target_net.key
                                dvs_port_connection.switchUuid = target_net.config.distributedVirtualSwitch.uuid
                                nic_spec.device.backing = vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo()
                                nic_spec.device.backing.port = dvs_port_connection
                            else:
                                nic_spec.device.backing = vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
                                nic_spec.device.backing.network = target_net
                                nic_spec.device.backing.deviceName = network_name
                            
                            config_spec = vim.vm.ConfigSpec()
                            config_spec.deviceChange = [nic_spec]
                            
                            reconfig_task = vm_to_update.ReconfigVM_Task(spec=config_spec)
                            while reconfig_task.info.state not in ["success", "error"]:
                                time.sleep(1)
                            
                            if reconfig_task.info.state == "success":
                                network_changed = True
                                update_output(f'  ✓ Network changed successfully')
                                break
                            else:
                                update_output(f'  ❌ Network change failed: {reconfig_task.info.error}')
                else:
                    update_output(f'  ❌ Network not found: {network_name}')
            else:
                update_output(f'  ❌ VM not found: {new_hostname}')
            
            Disconnect(si)
        except Exception as e:
            update_output(f'  ❌ Error changing network: {str(e)[:200]}')
        
        update_output('')
        
        # Step 6: Power on VM
        update_output('Step 6/8: Powering on VM...')
        try:
            si = SmartConnect(host=vcenter_host, user=vcenter_user, pwd=vcenter_password, sslContext=context)
            content = si.RetrieveContent()
            vm_to_power = next((vm for vm in content.viewManager.CreateContainerView(
                content.rootFolder, [vim.VirtualMachine], True).view 
                if vm.name == new_hostname), None)
            
            if vm_to_power and vm_to_power.runtime.powerState == 'poweredOff':
                power_task = vm_to_power.PowerOn()
                while power_task.info.state not in ["success", "error"]:
                    time.sleep(1)
                update_output('  ✓ VM powered on successfully')
            
            Disconnect(si)
        except Exception as e:
            update_output(f'  ❌ Error powering on: {str(e)[:200]}')
        
        update_output('')
        
        # Step 7: Wait for Windows to boot
        update_output('Step 7/8: Waiting 60 seconds for Windows to boot...')
        time.sleep(60)
        update_output('✓ Boot wait completed')
        update_output('')
        
        # Step 8: Validate network connectivity
        update_output(f'Step 8/8: Validating network connectivity to {new_ip}...')
        validation_success = False
        max_wait = 60
        elapsed = 0
        
        while elapsed < max_wait and not validation_success:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((new_ip, 3389))
                sock.close()
                
                if result == 0:
                    validation_success = True
                    update_output(f'  ✓ Network connectivity verified (RDP port 3389 accessible)')
                    break
                else:
                    time.sleep(5)
                    elapsed += 5
            except:
                time.sleep(5)
                elapsed += 5
        
        if not validation_success:
            update_output(f'  ❌ Could not verify connectivity to {new_ip}')
            history_record.status = 'failed'
            history_record.completed_at = timezone.now()
            history_record.save()
            return {'status': 'failed', 'error': 'Network validation failed'}
        
        update_output('')
        update_output('=== DEPLOYMENT SUCCESSFUL ===')
        update_output(f'✓ VM {new_hostname} is ready at {new_ip}')
        update_output(f'✓ Network: {network_name}')
        
        # Update history as successful
        history_record.status = 'success'
        history_record.completed_at = timezone.now()
        history_record.save()
        
        # Add to inventory
        try:
            env, _ = Environment.objects.get_or_create(
                name=deploy_env,
                defaults={'description': f'Environment {deploy_env}'}
            )
            group, _ = Group.objects.get_or_create(
                name=deploy_group,
                environment=env,
                defaults={'description': f'Group {deploy_group}'}
            )
            Host.objects.create(
                name=new_hostname,
                ip=new_ip,
                vcenter_server=vcenter_host,
                environment=env,
                group=group,
                operating_system='windows',
                description=f'Windows VM deployed from template {template_name}',
                active=True
            )
            update_output(f'✓ VM added to inventory')
        except Exception as e:
            update_output(f'  Warning: Could not add to inventory: {str(e)[:100]}')
        
        # Send notification
        try:
            from notifications.utils import send_deployment_notification
            send_deployment_notification(history_record, history_record.user, os_type='windows')
            logger.info('Deployment notification sent successfully')
        except Exception as e:
            logger.warning(f'Could not send deployment notification: {str(e)}')
        
        return {
            'status': 'success',
            'history_id': history_id,
            'hostname': new_hostname,
            'ip': new_ip
        }
        
    except Exception as e:
        logger.error(f'[CELERY-WINDOWS-{self.request.id}] Error: {str(e)}')
        
        try:
            history_record = DeploymentHistory.objects.get(pk=history_id)
            history_record.status = 'failed'
            history_record.completed_at = timezone.now()
            history_record.ansible_output += f'\n\n❌ CRITICAL ERROR: {str(e)}'
            history_record.save()
            
            # Send notification
            try:
                from notifications.utils import send_deployment_notification
                send_deployment_notification(history_record, history_record.user, os_type='windows')
            except Exception as notif_error:
                logger.warning(f'Could not send deployment notification: {str(notif_error)}')
        except Exception as db_error:
            logger.error(f'Could not update deployment history: {str(db_error)}')
        
        return {'status': 'error', 'message': str(e)}
