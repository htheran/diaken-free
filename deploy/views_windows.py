from django.shortcuts import render
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from settings.models import VCenterCredential, WindowsCredential, GlobalSetting
from history.models import DeploymentHistory
from inventory.models import Host, Environment, Group
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
import ssl
import time
import subprocess
import tempfile
import os
import socket
import winrm
import logging

logger = logging.getLogger(__name__)

def find_vm_by_name(si, name):
    """Find VM by name"""
    content = si.RetrieveContent()
    for child in content.rootFolder.childEntity:
        if hasattr(child, 'vmFolder'):
            for vm in child.vmFolder.childEntity:
                if isinstance(vm, vim.VirtualMachine) and vm.name == name:
                    return vm
    return None

def wait_for_task(task):
    """Wait for vCenter task to complete"""
    while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
        time.sleep(1)
    return task.info.state == vim.TaskInfo.State.success

@login_required
def deploy_windows_vm(request):
    """Form to deploy Windows VM"""
    vcenter_creds = VCenterCredential.objects.all()
    windows_creds = WindowsCredential.objects.all()
    
    # Get global settings
    global_settings = {}
    for setting in GlobalSetting.objects.all():
        global_settings[setting.key] = setting.value
    
    context = {
        'vcenter_credentials': vcenter_creds,
        'windows_credentials': windows_creds,
        'global_settings': global_settings,
    }
    return render(request, 'deploy/deploy_windows_vm_form.html', context)

@login_required
def deploy_windows_vm_run(request):
    """Execute Windows VM deployment (asynchronous with Celery)"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    try:
        # Get form data
        vcenter_id = request.POST.get('vcenter')
        datacenter = request.POST.get('datacenter')
        cluster = request.POST.get('cluster')
        datastore = request.POST.get('datastore')
        folder_path = request.POST.get('folder', '')
        network = request.POST.get('network')
        template_name = request.POST.get('template')
        hostname = request.POST.get('hostname')
        ip = request.POST.get('ip')
        gateway = request.POST.get('gateway')
        dns1 = request.POST.get('dns1', '8.8.8.8')
        dns2 = request.POST.get('dns2', '8.8.4.4')
        windows_cred_id = request.POST.get('windows_credential')
        
        # Get deploy_env and deploy_group from GlobalSettings (like Linux VMs do)
        deploy_env_setting = GlobalSetting.objects.filter(key='deploy_env').first()
        deploy_group_setting = GlobalSetting.objects.filter(key='deploy_group').first()
        
        deploy_env = deploy_env_setting.value if deploy_env_setting else 'PROVISIONAL'
        deploy_group = deploy_group_setting.value if deploy_group_setting else 'PROVISIONAL'
        
        logger.info(f'[WINDOWS] Using deploy_env={deploy_env}, deploy_group={deploy_group} from GlobalSettings')
        
        # Get credentials
        vcenter_cred = VCenterCredential.objects.get(pk=vcenter_id)
        windows_cred = WindowsCredential.objects.get(pk=windows_cred_id)
        
        # Get template IP from global settings
        template_ip = GlobalSetting.objects.filter(key='windows_template_ip').first()
        if not template_ip:
            return JsonResponse({'success': False, 'error': 'windows_template_ip not configured in Global Settings'})
        template_ip = template_ip.value
        
        # Step 1: Connect to vCenter
        context = ssl._create_unverified_context() if not vcenter_cred.ssl_verify else None
        si = SmartConnect(
            host=vcenter_cred.host,
            user=vcenter_cred.user,
            pwd=vcenter_cred.get_password(),
            sslContext=context
        )
        
        content = si.RetrieveContent()
        
        # Step 2: Find datacenter
        dc = None
        for child in content.rootFolder.childEntity:
            if isinstance(child, vim.Datacenter) and child.name == datacenter:
                dc = child
                break
        
        if not dc:
            Disconnect(si)
            return JsonResponse({'success': False, 'error': f'Datacenter {datacenter} not found'})
        
        # Step 3: Find cluster
        cluster_obj = None
        for child in dc.hostFolder.childEntity:
            if isinstance(child, vim.ClusterComputeResource) and child.name == cluster:
                cluster_obj = child
                break
        
        if not cluster_obj:
            Disconnect(si)
            return JsonResponse({'success': False, 'error': f'Cluster {cluster} not found'})
        
        # Step 4: Find datastore
        ds = None
        for datastore_obj in cluster_obj.datastore:
            if datastore_obj.name == datastore:
                ds = datastore_obj
                break
        
        if not ds:
            Disconnect(si)
            return JsonResponse({'success': False, 'error': f'Datastore {datastore} not found'})
        
        # Step 5: Find network
        net = None
        for network_obj in cluster_obj.network:
            if network_obj.name == network:
                net = network_obj
                break
        
        if not net:
            Disconnect(si)
            return JsonResponse({'success': False, 'error': f'Network {network} not found'})
        
        # Step 6: Find template
        template_vm = find_vm_by_name(si, template_name)
        if not template_vm:
            Disconnect(si)
            return JsonResponse({'success': False, 'error': f'Template {template_name} not found'})
        
        # Step 7: Get target folder
        folder = dc.vmFolder
        if folder_path:
            def find_folder_by_path(root_folder, path):
                parts = path.split('/')
                current = root_folder
                for part in parts:
                    found = False
                    if hasattr(current, 'childEntity'):
                        for child in current.childEntity:
                            if isinstance(child, vim.Folder) and child.name == part:
                                current = child
                                found = True
                                break
                    if not found:
                        return None
                return current
            
            target_folder = find_folder_by_path(dc.vmFolder, folder_path)
            if target_folder:
                folder = target_folder
        
        # Step 8: Create clone spec (WITHOUT network config - will do after clone)
        relospec = vim.vm.RelocateSpec()
        relospec.datastore = ds
        relospec.pool = cluster_obj.resourcePool
        
        clonespec = vim.vm.CloneSpec()
        clonespec.location = relospec
        clonespec.powerOn = False  # Don't power on yet
        clonespec.template = False
        
        # Step 9: Clone VM
        logger.info(f'[WINDOWS] Cloning VM {hostname} from template {template_name}')
        task = template_vm.Clone(folder=folder, name=hostname, spec=clonespec)
        
        if not wait_for_task(task):
            Disconnect(si)
            return JsonResponse({'success': False, 'error': 'Failed to clone VM'})
        
        logger.info(f'[WINDOWS] VM {hostname} cloned successfully')
        
        # Step 10: Reconfigure NIC AFTER cloning (same as Linux deployment)
        cloned_vm = task.info.result
        logger.info(f'[WINDOWS] Reconfiguring network adapter...')
        
        nicspec = vim.vm.device.VirtualDeviceSpec()
        nicspec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
        
        nic_found = False
        for device in cloned_vm.config.hardware.device:
            if isinstance(device, vim.vm.device.VirtualEthernetCard):
                nicspec.device = device
                
                # DO NOT change network yet - keep template network for initial WinRM connection
                # Network will be changed AFTER reboot when VM has new IP
                # nicspec.device.backing = vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
                # nicspec.device.backing.network = net
                # nicspec.device.backing.deviceName = network
                
                # Only configure connectivity
                nicspec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
                nicspec.device.connectable.startConnected = True
                nicspec.device.connectable.allowGuestControl = True
                nicspec.device.connectable.connected = True
                nic_found = True
                logger.info(f'[WINDOWS] Configured NIC connectivity (network change will happen after reboot): {device.deviceInfo.label}')
                break
        
        if not nic_found:
            logger.warning('[WINDOWS] No network adapter found in cloned VM')
        else:
            # Apply reconfiguration
            config_spec = vim.vm.ConfigSpec()
            config_spec.deviceChange = [nicspec]
            reconfig_task = cloned_vm.ReconfigVM_Task(spec=config_spec)
            
            if not wait_for_task(reconfig_task):
                logger.error('[WINDOWS] Failed to reconfigure NIC')
            else:
                logger.info('[WINDOWS] NIC reconfigured successfully')
        
        # Get VM MAC address for history
        vm_mac_address = None
        for device in cloned_vm.config.hardware.device:
            if isinstance(device, vim.vm.device.VirtualEthernetCard):
                vm_mac_address = device.macAddress
                break
        
        # Create deployment history record
        logger.info(f'[WINDOWS] Creating deployment history record...')
        history_record = DeploymentHistory.objects.create(
            user=request.user,
            environment=deploy_env,
            target=hostname,
            target_type='VM',
            playbook='provision_windows_vm.yml',
            status='running',
            hostname=hostname,
            ip_address=ip,
            mac_address=vm_mac_address,
            datacenter=datacenter,
            cluster=cluster,
            template=template_name
        )
        logger.info(f'[WINDOWS] History record created with ID: {history_record.pk}')
        
        # Step 11: Power on VM
        logger.info(f'[WINDOWS] Powering on VM...')
        power_task = cloned_vm.PowerOn()
        wait_for_task(power_task)
        
        # Disconnect from vCenter
        Disconnect(si)
        logger.info(f'[WINDOWS] VM powered on, dispatching async Celery task...')
        
        # Dispatch Celery task for async provisioning
        from deploy.tasks_windows import provision_windows_vm_async
        
        celery_task = provision_windows_vm_async.delay(
            history_id=history_record.pk,
            template_ip=template_ip,
            new_ip=ip,
            new_hostname=hostname,
            gateway=gateway,
            dns1=dns1,
            dns2=dns2,
            vcenter_host=vcenter_cred.host,
            vcenter_user=vcenter_cred.user,
            vcenter_password=vcenter_cred.get_password(),
            datacenter=datacenter,
            cluster=cluster,
            network_name=network,
            windows_user=windows_cred.username,
            windows_password=windows_cred.get_password(),
            windows_auth_type=windows_cred.auth_type,
            windows_port=windows_cred.get_port(),
            deploy_env=deploy_env,
            deploy_group=deploy_group,
            template_name=template_name
        )
        
        logger.info(f'[WINDOWS] Celery task dispatched: {celery_task.id}')
        logger.info(f'[WINDOWS] Returning immediate response to frontend')
        
        # Return immediate response for frontend polling
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'history_id': history_record.pk,
                'task_id': celery_task.id,
                'message': f'Windows VM {hostname} deployment started asynchronously'
            })
        else:
            # Fallback redirect if not AJAX
            from django.shortcuts import redirect
            return redirect('history:history_detail', pk=history_record.pk)
        
    except Exception as e:
        logger.error(f'[WINDOWS] Deployment error: {str(e)}')
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
