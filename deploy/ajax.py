from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from settings.models import VCenterCredential
from inventory.models import Group, Host
import ssl
import logging
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim

# Configure logger
logger = logging.getLogger('deploy.ajax')

@login_required
def get_groups(request):
    """Get groups filtered by environment"""
    env_id = request.GET.get('environment_id')
    groups = []
    
    if env_id:
        groups_qs = Group.objects.filter(active=True, environment_id=env_id).order_by('name')
    else:
        groups_qs = Group.objects.filter(active=True).order_by('name')
        
    for grp in groups_qs:
        groups.append({
            'id': grp.id,
            'name': grp.name,
            'environment_id': grp.environment_id,
            'environment_name': grp.environment.name
        })
        
    return JsonResponse({'groups': groups})

@login_required
def get_hosts(request):
    """Get hosts filtered by environment, group and OS family"""
    env_id = request.GET.get('environment_id')
    group_id = request.GET.get('group_id')
    os_family = request.GET.get('os_family')
    
    hosts_qs = Host.objects.filter(active=True).order_by('name')
    
    if env_id:
        hosts_qs = hosts_qs.filter(environment_id=env_id)
        
    if group_id:
        hosts_qs = hosts_qs.filter(group_id=group_id)
        
    if os_family:
        if os_family == 'redhat':
            hosts_qs = hosts_qs.filter(operating_system__in=['redhat', 'centos', 'oracle'])
        elif os_family == 'debian':
            hosts_qs = hosts_qs.filter(operating_system__in=['debian', 'ubuntu'])
        elif os_family == 'linux':
            hosts_qs = hosts_qs.filter(operating_system__in=['redhat', 'centos', 'oracle', 'debian', 'ubuntu'])
        elif os_family == 'windows':
            hosts_qs = hosts_qs.filter(operating_system='windows')
            
    hosts = []
    for host in hosts_qs:
        hosts.append({
            'id': host.id,
            'name': host.name,
            'ip': host.ip,
            'environment_name': host.environment.name,
            'group_name': host.group.name if host.group else '',
            'operating_system': host.operating_system
        })
        
    return JsonResponse({'hosts': hosts})

@login_required
def get_datacenters(request):
    dcs = []
    # Obtener vCenter ID del parámetro, o usar el primero por defecto
    vcenter_id = request.GET.get('vcenter_id')
    if vcenter_id:
        try:
            cred = VCenterCredential.objects.get(pk=vcenter_id)
        except VCenterCredential.DoesNotExist:
            cred = VCenterCredential.objects.first()
    else:
        cred = VCenterCredential.objects.first()
    
    if not cred:
        return JsonResponse({'datacenters': []})
    try:
        context = ssl._create_unverified_context()
        si = SmartConnect(host=cred.host, user=cred.user, pwd=cred.get_password(), sslContext=context)
        content = si.RetrieveContent()
        for entity in content.rootFolder.childEntity:
            if hasattr(entity, 'vmFolder'):
                dcs.append(entity.name)
        Disconnect(si)
        # Sort alphabetically
        dcs.sort()
    except Exception as e:
        logger.error(f'Error getting datacenters from vCenter {cred.host}: {str(e)}')
    return JsonResponse({'datacenters': dcs})

@login_required
def get_clusters(request):
    import logging
    dc_name = request.GET.get('datacenter')
    clusters = []
    error = None
    
    # Obtener vCenter ID del parámetro, o usar el primero por defecto
    vcenter_id = request.GET.get('vcenter_id')
    if vcenter_id:
        try:
            cred = VCenterCredential.objects.get(pk=vcenter_id)
        except VCenterCredential.DoesNotExist:
            cred = VCenterCredential.objects.first()
    else:
        cred = VCenterCredential.objects.first()
    
    if not cred or not dc_name:
        return JsonResponse({'clusters': [], 'error': 'No credentials or datacenter provided'})
    try:
        context = ssl._create_unverified_context()
        si = SmartConnect(host=cred.host, user=cred.user, pwd=cred.get_password(), sslContext=context)
        content = si.RetrieveContent()
        dc_name_norm = dc_name.strip().lower()
        datacenter = next((entity for entity in content.rootFolder.childEntity if hasattr(entity, 'vmFolder') and entity.name.strip().lower() == dc_name_norm), None)
        if datacenter:
            for c in datacenter.hostFolder.childEntity:
                if hasattr(c, 'resourcePool'):
                    clusters.append(c.name)
            # Sort alphabetically
            clusters.sort()
        else:
            error = f"Datacenter '{dc_name}' not found."
        Disconnect(si)
    except Exception as e:
        error = str(e)
        logging.exception("Error in get_clusters")
    return JsonResponse({'clusters': clusters, 'error': error})

@login_required
def get_resource_pools(request):
    dc_name = request.GET.get('datacenter')
    cluster_name = request.GET.get('cluster')
    resource_pools = []
    
    # Obtener vCenter ID del parámetro, o usar el primero por defecto
    vcenter_id = request.GET.get('vcenter_id')
    if vcenter_id:
        try:
            cred = VCenterCredential.objects.get(pk=vcenter_id)
        except VCenterCredential.DoesNotExist:
            cred = VCenterCredential.objects.first()
    else:
        cred = VCenterCredential.objects.first()
    
    if not cred or not dc_name or not cluster_name:
        return JsonResponse({'resource_pools': []})
    try:
        context = ssl._create_unverified_context()
        si = SmartConnect(host=cred.host, user=cred.user, pwd=cred.get_password(), sslContext=context)
        content = si.RetrieveContent()
        datacenter = next((entity for entity in content.rootFolder.childEntity if hasattr(entity, 'vmFolder') and entity.name.strip().lower() == dc_name.strip().lower()), None)
        if datacenter:
            cluster = None
            cluster_name_norm = cluster_name.strip().lower()
            for c in datacenter.hostFolder.childEntity:
                if hasattr(c, 'resourcePool') and c.name.strip().lower() == cluster_name_norm:
                    cluster = c
                    break
            if cluster:
                resource_pools.append(cluster.resourcePool.name)
                for rp in cluster.resourcePool.resourcePool:
                    resource_pools.append(rp.name)
        Disconnect(si)
    except Exception as e:
        logger.error(f"Error in get_resource_pools: {e}")
    return JsonResponse({'resource_pools': list(set(resource_pools))})

@login_required
def get_templates(request):
    templates = []
    # Obtener vCenter ID del parámetro, o usar el primero por defecto
    vcenter_id = request.GET.get('vcenter_id')
    if vcenter_id:
        try:
            cred = VCenterCredential.objects.get(pk=vcenter_id)
        except VCenterCredential.DoesNotExist:
            cred = VCenterCredential.objects.first()
    else:
        cred = VCenterCredential.objects.first()
    
    if not cred:
        return JsonResponse({'templates': []})
    try:
        context = ssl._create_unverified_context()
        si = SmartConnect(host=cred.host, user=cred.user, pwd=cred.get_password(), sslContext=context)
        content = si.RetrieveContent()
        viewType = [vim.VirtualMachine]
        recursive = True
        containerView = content.viewManager.CreateContainerView(content.rootFolder, viewType, recursive)
        for vm in containerView.view:
            if vm.config.template:
                templates.append(vm.name)
        Disconnect(si)
        # Sort alphabetically
        templates.sort()
    except Exception as e:
        logger.error(f'Error getting templates from vCenter: {str(e)}')
    return JsonResponse({'templates': templates})

@login_required
def get_datastores(request):
    datastores = []
    
    # Obtener vCenter ID del parámetro, o usar el primero por defecto
    vcenter_id = request.GET.get('vcenter_id')
    if vcenter_id:
        try:
            cred = VCenterCredential.objects.get(pk=vcenter_id)
        except VCenterCredential.DoesNotExist:
            cred = VCenterCredential.objects.first()
    else:
        cred = VCenterCredential.objects.first()
    
    if not cred:
        return JsonResponse({'datastores': []})
    try:
        context = ssl._create_unverified_context()
        si = SmartConnect(host=cred.host, user=cred.user, pwd=cred.get_password(), sslContext=context)
        content = si.RetrieveContent()
        for ds in content.viewManager.CreateContainerView(content.rootFolder, [vim.Datastore], True).view:
            datastores.append(ds.name)
        Disconnect(si)
        # Sort alphabetically
        datastores.sort()
    except Exception as e:
        logger.error(f'Error getting datastores from vCenter: {str(e)}')
    return JsonResponse({'datastores': datastores})

@login_required
def get_networks(request):
    networks = set()  # Usar set para evitar duplicados
    
    # Obtener vCenter ID del parámetro, o usar el primero por defecto
    vcenter_id = request.GET.get('vcenter_id')
    if vcenter_id:
        try:
            cred = VCenterCredential.objects.get(pk=vcenter_id)
        except VCenterCredential.DoesNotExist:
            cred = VCenterCredential.objects.first()
    else:
        cred = VCenterCredential.objects.first()
    
    if not cred:
        return JsonResponse({'networks': []})
    try:
        context = ssl._create_unverified_context()
        si = SmartConnect(host=cred.host, user=cred.user, pwd=cred.get_password(), sslContext=context)
        content = si.RetrieveContent()
        # Agregar redes estándar y DVS (puede haber duplicados por nombre)
        for net in content.viewManager.CreateContainerView(content.rootFolder, [vim.Network], True).view:
            networks.add(net.name)  # set automáticamente elimina duplicados
        Disconnect(si)
        # Convertir a lista ordenada
        networks = sorted(list(networks))
    except Exception as e:
        logger.error(f'Error getting networks from vCenter: {str(e)}')
        networks = []  # Retornar lista vacía en caso de error
    return JsonResponse({'networks': networks})

@login_required
def get_folders(request):
    """
    Get all VM folders from vCenter
    Returns list of folders in alphabetical order
    """
    folders = []
    vcenter_id = request.GET.get('vcenter_id')
    datacenter_name = request.GET.get('datacenter')
    
    if vcenter_id:
        try:
            cred = VCenterCredential.objects.get(pk=vcenter_id)
        except VCenterCredential.DoesNotExist:
            cred = VCenterCredential.objects.first()
    else:
        cred = VCenterCredential.objects.first()
    
    if not cred:
        return JsonResponse({'folders': []})
    
    try:
        context = ssl._create_unverified_context()
        si = SmartConnect(host=cred.host, user=cred.user, pwd=cred.get_password(), sslContext=context)
        content = si.RetrieveContent()
        
        # Find the specified datacenter
        datacenter = None
        for dc in content.rootFolder.childEntity:
            if hasattr(dc, 'vmFolder') and dc.name == datacenter_name:
                datacenter = dc
                break
        
        if datacenter:
            # Get all folders recursively
            def get_folder_tree(folder, path=""):
                for child in folder.childEntity:
                    if isinstance(child, vim.Folder):
                        folder_path = f"{path}/{child.name}" if path else child.name
                        folders.append({
                            'name': child.name,
                            'path': folder_path
                        })
                        # Recursively get subfolders
                        get_folder_tree(child, folder_path)
            
            # Start from vmFolder of the datacenter
            get_folder_tree(datacenter.vmFolder)
        
        Disconnect(si)
        
        # Sort folders alphabetically by path
        folders.sort(key=lambda x: x['path'].lower())
        
    except Exception as e:
        import logging
        logging.error(f"Error getting folders: {e}")
        pass
    
    return JsonResponse({'folders': folders})


@login_required
def get_task_progress(request, task_id):
    """
    Get the progress of a Celery task in real-time.
    
    Args:
        task_id: Celery task ID
    
    Returns:
        JSON with task status and progress information
    """
    from celery.result import AsyncResult
    
    task = AsyncResult(task_id)
    
    response_data = {
        'task_id': task_id,
        'state': task.state,
    }
    
    if task.state == 'PENDING':
        response_data.update({
            'status': 'pending',
            'current_step': 0,
            'total_steps': 8,
            'percent': 0,
            'message': 'Task is waiting to start...'
        })
    elif task.state == 'PROGRESS':
        # Task is running and reporting progress
        response_data.update({
            'status': 'running',
            'current_step': task.info.get('current_step', 0),
            'total_steps': task.info.get('total_steps', 8),
            'percent': task.info.get('percent', 0),
            'message': task.info.get('message', 'Processing...')
        })
    elif task.state == 'SUCCESS':
        # Task completed successfully
        result = task.result if task.result else {}
        response_data.update({
            'status': 'success',
            'current_step': result.get('total_steps', 8),
            'total_steps': result.get('total_steps', 8),
            'percent': 100,
            'message': result.get('message', 'Deployment completed successfully!')
        })
    elif task.state == 'FAILURE':
        # Task failed
        response_data.update({
            'status': 'failed',
            'current_step': 0,
            'total_steps': 8,
            'percent': 0,
            'message': f"Deployment failed: {str(task.info)}",
            'error': str(task.info)
        })
    else:
        # Unknown state
        response_data.update({
            'status': 'unknown',
            'message': f'Unknown task state: {task.state}'
        })
    
    return JsonResponse(response_data)
