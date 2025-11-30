from django.shortcuts import render, redirect
from django.conf import settings
from django.http import JsonResponse
from .forms import DeployVMForm
from settings.models import GlobalSetting
from django.contrib import messages
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.html import escape
import logging

from inventory.models import Host, Environment, Group
from history.models import DeploymentHistory
from .govc_helper import change_vm_network_govc
from security_fixes.sanitization_helpers import InputSanitizer

# Configure logger for deployment operations
logger = logging.getLogger('deploy.views')

def deploy_vm(request):
    # Obtener plantillas parametrizadas desde settings
    template_names = GlobalSetting.objects.filter(key__icontains='template').values_list('value', flat=True)
    template_choices = [(name, name) for name in template_names]

    # Leer credenciales vCenter desde VCenterCredential
    from settings.models import VCenterCredential
    vcenters = VCenterCredential.objects.all()
    if not vcenters.exists():
        messages.error(request, 'No hay credenciales de vCenter configuradas.')
        return render(request, 'deploy/deploy_vm_form.html', {'form': DeployVMForm()})
    
    # Crear choices para el selector de vCenter
    vcenter_choices = [('', '------------')] + [(str(vc.pk), vc.name) for vc in vcenters]
    
    # Por defecto usar el primer vCenter
    cred = vcenters.first()
    vcenter_host = cred.host
    vcenter_user = cred.user
    vcenter_password = cred.get_password()
    
    # Obtener configuraciones globales con valores por defecto
    deploy_env_obj = GlobalSetting.objects.filter(key='deploy_env').first()
    deploy_group_obj = GlobalSetting.objects.filter(key='deploy_group').first()
    deploy_env = deploy_env_obj.value if deploy_env_obj else None
    deploy_group = deploy_group_obj.value if deploy_group_obj else None

    datacenters = []
    templates = []
    # SSH Credentials
    from settings.models import DeploymentCredential
    ssh_creds = DeploymentCredential.objects.all()
    ssh_choices = [(str(c.pk), c.name) for c in ssh_creds]
    
    # Playbooks de tipo host
    from playbooks.models import Playbook
    host_playbooks = Playbook.objects.filter(playbook_type='host')
    playbook_choices = [('basic', 'Basic (No additional playbook)')] + [(str(p.pk), p.name) for p in host_playbooks]
    if request.method == 'POST':
        form = DeployVMForm(request.POST)
        # Poblar campo vcenter
        form.fields['vcenter'].choices = vcenter_choices
        
        # Obtener vCenter seleccionado
        vcenter_id = request.POST.get('vcenter')
        from settings.models import VCenterCredential
        import ssl
        from pyVim.connect import SmartConnect, Disconnect
        from pyVmomi import vim
        
        if vcenter_id:
            cred = VCenterCredential.objects.get(pk=vcenter_id)
        else:
            cred = vcenters.first()
        
        if cred:
            try:
                context = ssl._create_unverified_context()
                si = SmartConnect(host=cred.host, user=cred.user, pwd=cred.get_password(), sslContext=context)
                content = si.RetrieveContent()
                for entity in content.rootFolder.childEntity:
                    if hasattr(entity, 'vmFolder'):
                        datacenters.append(entity.name)
                for vm in content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True).view:
                    if vm.config.template:
                        templates.append(vm.name)
                Disconnect(si)
            except Exception as e:
                datacenters = []
                templates = []
        form.fields['template'].choices = [(t, t) for t in templates]
        form.fields['datacenter'].choices = [(d, d) for d in datacenters]
        form.fields['ssh_credential'].choices = ssh_choices
        # additional_playbook is now a CharField (hidden), no choices needed
        # Choices dependientes:
        clusters = []
        resource_pools = []
        datastores = []
        networks = []
        dc_selected = request.POST.get('datacenter')
        cl_selected = request.POST.get('cluster')
        if cred and dc_selected:
            try:
                context = ssl._create_unverified_context()
                si = SmartConnect(host=cred.host, user=cred.user, pwd=cred.get_password(), sslContext=context)
                content = si.RetrieveContent()
                # Buscar datacenter
                dc = next((entity for entity in content.rootFolder.childEntity if hasattr(entity, 'vmFolder') and entity.name == dc_selected), None)
                if dc:
                    # Clusters
                    clusters = [c.name for c in dc.hostFolder.childEntity if hasattr(c, 'resourcePool')]
                    # Resource pools
                    if cl_selected:
                        cl = next((c for c in dc.hostFolder.childEntity if hasattr(c, 'resourcePool') and c.name == cl_selected), None)
                        if cl:
                            resource_pools = [cl.resourcePool.name] + [rp.name for rp in cl.resourcePool.resourcePool]
                # Datastores
                datastores = [ds.name for ds in content.viewManager.CreateContainerView(content.rootFolder, [vim.Datastore], True).view]
                # Networks
                networks = [net.name for net in content.viewManager.CreateContainerView(content.rootFolder, [vim.Network], True).view]
                Disconnect(si)
            except Exception as e:
                clusters = []
                resource_pools = []
                datastores = []
                networks = []
        form.fields['cluster'].choices = [(cl, cl) for cl in clusters]
        form.fields['resource_pool'].choices = [(rp, rp) for rp in resource_pools]
        form.fields['datastore'].choices = [(ds, ds) for ds in datastores]
        form.fields['network'].choices = [(net, net) for net in networks]
        if form.is_valid():
            datacenter = form.cleaned_data['datacenter']
            cluster = form.cleaned_data['cluster']
            resource_pool = form.cleaned_data['resource_pool']
            datastore = form.cleaned_data['datastore']
            network = form.cleaned_data['network']
            template = form.cleaned_data['template']
            hostname = form.cleaned_data['hostname']
            ip = form.cleaned_data['ip']
            folder_path = request.POST.get('folder', '')  # Optional folder path
            
            # Get optional playbooks
            additional_playbooks = request.POST.getlist('playbooks[]', [])
            logger.info(f"DEPLOY: Additional playbooks selected: {additional_playbooks}")
            
            # SECURITY: Sanitize all user inputs to prevent injection attacks
            try:
                hostname = InputSanitizer.sanitize_hostname(hostname)
                ip = InputSanitizer.sanitize_ip_address(ip)
                # Template comes from vCenter, no need for strict sanitization
                # Just validate it's not empty and doesn't contain dangerous characters
                if not template or not template.strip():
                    raise ValueError("Template name cannot be empty")
                template = template.strip()
                network = InputSanitizer.sanitize_network_name(network)
                logger.info(f"Deploy VM request: hostname={hostname}, ip={ip}, template={template}, user={request.user.username}")
            except ValueError as e:
                logger.error(f"Input validation failed: {e}")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': f'Invalid input: {e}'})
                messages.error(request, f'Invalid input: {e}')
                return redirect('deploy:deploy_vm')
            
            # Validar si el hostname ya existe en el inventario (solo hosts activos)
            from inventory.models import Host
            if Host.objects.filter(name=hostname, active=True).exists():
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': f'Hostname {hostname} already exists in inventory'})
                messages.error(request, mark_safe(f'<b>❌ Hostname already exists!</b><br>The hostname <b>{escape(hostname)}</b> is already registered in the inventory.<br>Please choose a different hostname.'))
                return redirect('deploy:deploy_vm')
            
            # Validar si la IP ya existe en el inventario (solo hosts activos)
            if Host.objects.filter(ip=ip, active=True).exists():
                existing_host = Host.objects.get(ip=ip, active=True)
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': f'IP {ip} already assigned to {existing_host.name}'})
                messages.error(request, mark_safe(f'<b>❌ IP address already exists!</b><br>The IP <b>{escape(ip)}</b> is already assigned to host <b>{escape(existing_host.name)}</b>.<br>Please choose a different IP address.'))
                return redirect('deploy:deploy_vm')
            
            # --- INTEGRACIÓN REAL vCENTER (pyVmomi) ---
            try:
                import socket
                from pyVim.connect import SmartConnect, Disconnect
                from pyVmomi import vim
                import ssl
                
                # IMPORTANTE: Obtener credenciales del vCenter SELECCIONADO en el formulario
                vcenter_id = request.POST.get('vcenter')
                if vcenter_id:
                    selected_vcenter = VCenterCredential.objects.get(pk=vcenter_id)
                else:
                    selected_vcenter = vcenters.first()
                
                # Usar credenciales del vCenter seleccionado
                vcenter_host = selected_vcenter.host
                vcenter_user = selected_vcenter.user
                vcenter_password = selected_vcenter.get_password()
                
                logger.info(f"DEPLOY: Using vCenter: {selected_vcenter.name} ({vcenter_host})")
                
                context = ssl._create_unverified_context()
                si = SmartConnect(host=vcenter_host, user=vcenter_user, pwd=vcenter_password, sslContext=context)
                content = si.RetrieveContent()

                # Buscar datacenter
                dc = next((entity for entity in content.rootFolder.childEntity if hasattr(entity, 'vmFolder') and entity.name == datacenter), None)
                if not dc:
                    raise Exception(f"Datacenter '{datacenter}' no encontrado.")
                # Buscar cluster
                cl = next((c for c in dc.hostFolder.childEntity if hasattr(c, 'resourcePool') and c.name == cluster), None)
                if not cl:
                    available_clusters = [c.name for c in dc.hostFolder.childEntity if hasattr(c, 'resourcePool')]
                    raise Exception(f"Cluster '{cluster}' no encontrado en vCenter '{selected_vcenter.name}'. Clusters disponibles: {', '.join(available_clusters)}")
                # Buscar resource pool
                rp = None
                for r in [cl.resourcePool] + list(cl.resourcePool.resourcePool):
                    if r.name == resource_pool:
                        rp = r
                        break
                if not rp:
                    raise Exception(f"Resource Pool '{resource_pool}' no encontrado.")
                # Buscar datastore
                ds = next((d for d in content.viewManager.CreateContainerView(content.rootFolder, [vim.Datastore], True).view if d.name == datastore), None)
                if not ds:
                    raise Exception(f"Datastore '{datastore}' no encontrado.")
                # Buscar red
                net = next((n for n in content.viewManager.CreateContainerView(content.rootFolder, [vim.Network], True).view if n.name == network), None)
                if not net:
                    raise Exception(f"Network '{network}' no encontrada.")
                # Verificar si ya existe una VM con el mismo nombre en vCenter (excluir templates)
                existing_vm = next((vm for vm in content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True).view 
                                   if vm.name == hostname and not vm.config.template), None)
                if existing_vm:
                    Disconnect(si)
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'error': f'VM {hostname} already exists in vCenter'})
                    messages.error(request, mark_safe(f'<b>❌ VM already exists in vCenter!</b><br>A VM with the name <b>{escape(hostname)}</b> already exists in vCenter.<br>Datacenter: {escape(datacenter)}<br>Power State: {existing_vm.runtime.powerState}<br>Please choose a different hostname.'))
                    return redirect('deploy:deploy_vm')
                
                # Buscar plantilla
                template_vm = next((t for t in content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True).view if t.name == template and t.config.template), None)
                if not template_vm:
                    raise Exception(f"Plantilla '{template}' no encontrada.")
                
                # Get target folder (use selected folder or default to vmFolder)
                folder = dc.vmFolder
                if folder_path:
                    # Navigate to the specified folder
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
                    else:
                        logger.info(f"DEPLOY: Warning: Folder '{folder_path}' not found, using default vmFolder")
                # CustomizationSpec para hostname, IP y red
                # IMPORTANTE: NO usar customization spec porque puede causar problemas
                # con plantillas Debian/Ubuntu que no tienen open-vm-tools o perl
                # La configuración de IP/hostname se hará con Ansible después del boot
                custom_spec = None
                # RelocateSpec y CloneSpec con customization
                # Configure thin provisioning for disk
                relospec = vim.vm.RelocateSpec(
                    pool=rp, 
                    datastore=ds,
                    transform=vim.vm.RelocateSpec.Transformation.sparse  # Thin provisioning
                )
                clonespec = vim.vm.CloneSpec(location=relospec, powerOn=False, template=False, customization=custom_spec)
                task = template_vm.Clone(folder=folder, name=hostname, spec=clonespec)
                from time import sleep
                while task.info.state not in ["success", "error"]:
                    sleep(2)
                if task.info.state == "error":
                    raise Exception(f"Error en el clonado: {task.info.error}")
                
                # Reconfigurar la VM clonada para conectar la interfaz de red
                cloned_vm = task.info.result
                vm_mac_address = None
                nic_spec = vim.vm.device.VirtualDeviceSpec()
                nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
                # Buscar la primera NIC de la VM clonada y obtener MAC address
                for device in cloned_vm.config.hardware.device:
                    if isinstance(device, vim.vm.device.VirtualEthernetCard):
                        vm_mac_address = device.macAddress
                        logger.info(f'DEPLOY: MAC Address de la VM: {vm_mac_address}')
                        nic_spec.device = device
                        # NO cambiar la red - mantener la red de la plantilla
                        # La VM debe estar en la misma red que la plantilla para SSH inicial
                        # nic_spec.device.backing = vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
                        # nic_spec.device.backing.network = net
                        # nic_spec.device.backing.deviceName = network
                        # Configurar conectividad
                        nic_spec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
                        nic_spec.device.connectable.startConnected = True
                        nic_spec.device.connectable.allowGuestControl = True
                        nic_spec.device.connectable.connected = True
                        logger.info(f'DEPLOY: Configurando NIC para auto-conectar al encender')
                        break
                
                # Aplicar la reconfiguración
                config_spec = vim.vm.ConfigSpec()
                config_spec.deviceChange = [nic_spec]
                reconfig_task = cloned_vm.ReconfigVM_Task(spec=config_spec)
                while reconfig_task.info.state not in ["success", "error"]:
                    sleep(2)
                if reconfig_task.info.state == "error":
                    raise Exception(f"Error reconfigurando NIC: {reconfig_task.info.error}")
                
                # Encender la VM
                logger.info(f'DEPLOY: Encendiendo VM {hostname}...')
                logger.info(f'DEPLOY: VM State before PowerOn: {cloned_vm.runtime.powerState}')
                try:
                    power_task = cloned_vm.PowerOn()
                    while power_task.info.state not in ["success", "error"]:
                        sleep(2)
                    if power_task.info.state == "error":
                        error_msg = str(power_task.info.error)
                        logger.error(f'DEPLOY: Error encendiendo VM {hostname}: {error_msg}')
                        raise Exception(f"Error encendiendo VM: {error_msg}")
                    logger.info(f'DEPLOY: PowerOn task completed successfully')
                    # Esperar 5 segundos para que la VM inicie el boot
                    sleep(5)
                    # Refrescar estado de la VM
                    cloned_vm_refreshed = next((v for v in content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True).view if v.name == hostname), None)
                    if cloned_vm_refreshed:
                        logger.info(f'DEPLOY: VM State after PowerOn: {cloned_vm_refreshed.runtime.powerState}')
                        logger.info(f'DEPLOY: VM Connection State: {cloned_vm_refreshed.runtime.connectionState}')
                        logger.info(f'DEPLOY: VM Guest State: {cloned_vm_refreshed.guest.guestState}')
                    else:
                        logger.warning(f'DEPLOY: Could not refresh VM state after PowerOn')
                except Exception as e:
                    logger.error(f'DEPLOY: Exception during PowerOn: {str(e)}')
                    raise
                
                Disconnect(si)

                # Post-provision con Ansible (ASÍNCRONO con Celery)
                import os
                
                # Obtener credencial SSH seleccionada
                ssh_cred_pk = form.cleaned_data['ssh_credential']
                ssh_cred = DeploymentCredential.objects.get(pk=ssh_cred_pk)
                ssh_user = ssh_cred.user
                ssh_key_path = ssh_cred.ssh_key_file_path
                
                if not ssh_key_path or not os.path.exists(ssh_key_path):
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'error': f'SSH key file not found for credential {ssh_cred.name}'})
                    messages.error(request, f'Archivo de llave SSH no encontrado para la credencial {ssh_cred.name}.')
                    return redirect('deploy:deploy_vm')
                
                # Obtener os_family del formulario
                os_family = form.cleaned_data['operating_system']
                
                # Obtener la IP de la plantilla desde GlobalSettings
                if os_family == 'debian':
                    template_ip_key = 'ubuntu_template_ip'
                else:
                    template_ip_key = 'ip_template'
                
                template_ip_setting = GlobalSetting.objects.filter(key=template_ip_key).first()
                if not template_ip_setting:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'error': f'GlobalSetting {template_ip_key} not found'})
                    messages.error(request, f'No se encontró la variable {template_ip_key} en GlobalSettings.')
                    return redirect('deploy:deploy_vm')
                
                template_ip = template_ip_setting.value
                
                # Calcular gateway
                gateway = ip.rsplit('.', 1)[0] + '.1'
                interface = 'ens192'
                python_interpreter = form.cleaned_data.get('ansible_python_interpreter', '/usr/bin/python3') or '/usr/bin/python3'
                
                # Crear registro de historial
                playbook_name = 'Basic Setup'
                history_record = DeploymentHistory.objects.create(
                    user=request.user,
                    environment=deploy_env,
                    target=hostname,
                    target_type='VM',
                    playbook=playbook_name,
                    status='pending',
                    hostname=hostname,
                    ip_address=ip,
                    mac_address=vm_mac_address,
                    datacenter=datacenter,
                    cluster=cluster,
                    template=template
                )
                
                logger.info(f'DEPLOY: Dispatching async provisioning task for VM: {hostname} on vCenter: {selected_vcenter.name}')
                
                # Dispatch async Celery task
                from deploy.tasks import provision_linux_vm_async
                celery_task = provision_linux_vm_async.delay(
                    history_id=history_record.pk,
                    template_ip=template_ip,
                    new_ip=ip,
                    new_hostname=hostname,
                    gateway=gateway,
                    interface=interface,
                    os_family=os_family,
                    ssh_user=ssh_user,
                    ssh_key_path=ssh_key_path,
                    python_interpreter=python_interpreter,
                    vcenter_host=vcenter_host,
                    vcenter_user=vcenter_user,
                    vcenter_password=vcenter_password,
                    network_name=network,
                    # Inventory parameters
                    deploy_env=deploy_env,
                    deploy_group=deploy_group,
                    template=template,
                    datacenter=datacenter,
                    cluster=cluster,
                    # Optional playbooks
                    additional_playbooks=additional_playbooks
                )
                
                logger.info(f'DEPLOY: Celery task dispatched: {celery_task.id}')
                
                # Actualizar historial con task ID
                history_record.celery_task_id = celery_task.id
                history_record.status = 'running'
                history_record.save()
                
                # Mensaje de éxito con link al historial
                messages.success(
                    request,
                    mark_safe(
                        f'<b>✅ VM Deployment Started!</b><br>'
                        f'VM <b>{escape(hostname)}</b> is being provisioned asynchronously.<br>'
                        f'IP: <b>{escape(ip)}</b><br>'
                        f'Network: <b>{escape(network)}</b><br>'
                        f'<a href="/history/{history_record.pk}/" class="btn btn-sm btn-primary mt-2">'
                        f'<i class="fas fa-eye"></i> View Progress</a>'
                    )
                )
                
                # Redirigir a historial
                # Si es AJAX, retornar JSON con history_id para polling; si no, redirect normal
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'history_id': history_record.pk,
                        'task_id': celery_task.id,
                        'message': f'VM {hostname} deployment started'
                    })
                else:
                    return redirect('history:history_detail', pk=history_record.pk)

            except Exception as e:
                import traceback
                error_msg = str(e)
                error_trace = traceback.format_exc()
                logger.error(f'DEPLOY: Exception during deployment: {error_msg}')
                logger.error(f'DEPLOY: Traceback: {error_trace}')
                
                # Return JSON error for AJAX requests
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': f'Deployment error: {error_msg}'
                    })
                
                messages.error(request, f"Error al desplegar en vCenter o registrar VM: {error_msg}")
                return redirect('deploy:deploy_vm')
    else:
        # GET request - No pre-cargar datacenters, se cargarán dinámicamente vía AJAX
        datacenters = []
        templates = []
        form = DeployVMForm()
        form.fields['vcenter'].choices = vcenter_choices
        form.fields['datacenter'].choices = [('', 'Select datacenter...')]
        form.fields['template'].choices = [('', 'Select template...')]
        form.fields['ssh_credential'].choices = ssh_choices
        # additional_playbook is now a CharField (hidden), no choices needed

    return render(request, 'deploy/deploy_vm_form.html', {'form': form, 'datacenters': datacenters, 'templates': templates})

from django.http import JsonResponse
from django.views.decorators.http import require_POST

@require_POST
def clear_auto_open(request):
    """Clear auto_open_url from session after it has been used"""
    if 'auto_open_url' in request.session:
        del request.session['auto_open_url']
    if 'auto_open_rendered' in request.session:
        del request.session['auto_open_rendered']
    return JsonResponse({'status': 'ok'})

# Import playbook execution views
from .views_playbook import deploy_index, deploy_playbook, execute_playbook
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from inventory.models import Environment, Group, Host
from playbooks.models import Playbook
from history.models import DeploymentHistory
from settings.models import DeploymentCredential, GlobalSetting
from scheduler.models import ScheduledTask
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
    # Filter only Linux/RedHat hosts
    hosts = Host.objects.filter(active=True, operating_system='redhat').order_by('name')
    # Playbooks will be loaded dynamically based on target_type
    
    context = {
        'environments': environments,
        'groups': groups,
        'hosts': hosts,
    }
    return render(request, 'deploy/deploy_playbook_form.html', context)

@login_required
def execute_playbook(request):
    """Execute selected playbook on selected host or group"""
    if request.method != 'POST':
        return redirect('deploy:deploy_playbook')
    
    # Get form data
    target_type = request.POST.get('target_type')  # 'host' or 'group'
    host_id = request.POST.get('host')
    group_id = request.POST.get('group')
    playbook_id = request.POST.get('playbook')
    scheduled = request.POST.get('scheduled') == '1'
    scheduled_time = request.POST.get('scheduled_time')
    
    # Get and log snapshot flag (only for hosts)
    create_snapshot_value = request.POST.get('create_snapshot')
    create_snapshot_flag = create_snapshot_value == '1' if target_type == 'host' else False
    logger.info(f"[LINUX-PLAYBOOK] Target type: {target_type}")
    logger.info(f"[LINUX-PLAYBOOK] Snapshot checkbox value: '{create_snapshot_value}'")
    logger.info(f"[LINUX-PLAYBOOK] Snapshot flag evaluated to: {create_snapshot_flag}")
    
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
            hosts_in_group = Host.objects.filter(group=group, active=True, operating_system='redhat')
            if not hosts_in_group.exists():
                return JsonResponse({'success': False, 'error': f'No active Linux hosts found in group {group.name}'})
        except Group.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Group not found'})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid target type'})
    
    # Get playbook
    try:
        playbook = Playbook.objects.get(pk=playbook_id)
    except Playbook.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Playbook not found'})
    
    # Handle scheduled execution
    if scheduled and scheduled_time:
        try:
            from datetime import datetime
            # Parse scheduled time (format: YYYY-MM-DDTHH:MM)
            scheduled_dt = datetime.strptime(scheduled_time, '%Y-%m-%dT%H:%M')
            # Make it timezone-aware
            scheduled_dt = timezone.make_aware(scheduled_dt)
            
            # Create scheduled task
            task = ScheduledTask.objects.create(
                task_type=target_type,
                name=f"Execute {playbook.name} on {target_name}",
                created_by=request.user,
                environment=Environment.objects.get(pk=request.POST.get('environment')) if request.POST.get('environment') else None,
                group=group if target_type == 'group' else None,
                host=host if target_type == 'host' else None,
                playbook=playbook,
                create_snapshot=create_snapshot_flag,
                scheduled_datetime=scheduled_dt,
                status='pending'
            )
            
            logger.info(f"Scheduled task created: {task.id} for {scheduled_dt}")
            
            return JsonResponse({
                'success': True,
                'scheduled': True,
                'task_id': task.id,
                'scheduled_time': scheduled_dt.strftime('%Y-%m-%d %H:%M:%S'),
                'output': f"Task scheduled successfully for {scheduled_dt.strftime('%Y-%m-%d %H:%M:%S')}\n\nTask ID: {task.id}\nPlaybook: {playbook.name}\nTarget: {target_name}"
            })
        except Exception as e:
            logger.error(f"Error creating scheduled task: {str(e)}")
            return JsonResponse({'success': False, 'error': f'Failed to schedule task: {str(e)}'})
    
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
            settings.ANSIBLE_PLAYBOOK_PATH,
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

@login_required
def get_playbooks(request):
    """Get playbooks filtered by target type and OS family"""
    target_type = request.GET.get('target_type')
    os_family = request.GET.get('os_family', 'linux')
    
    if not target_type:
        return JsonResponse({'playbooks': []})
    
    # Map 'linux' to 'redhat' for compatibility
    if os_family == 'linux':
        os_family = 'redhat'
    
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
