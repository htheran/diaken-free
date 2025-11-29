"""
vCenter utility functions for folder management and VM operations
"""
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
import ssl
import logging

logger = logging.getLogger(__name__)


def get_vcenter_connection(host, user, password):
    """
    Connect to vCenter server
    
    Args:
        host: vCenter hostname or IP
        user: Username
        password: Password
    
    Returns:
        ServiceInstance connection
    """
    context = ssl._create_unverified_context()
    si = SmartConnect(
        host=host,
        user=user,
        pwd=password,
        sslContext=context
    )
    return si


def get_all_folders(si):
    """
    Get all VM folders from vCenter in alphabetical order
    
    Args:
        si: ServiceInstance connection
    
    Returns:
        list: List of tuples (folder_name, folder_path, folder_obj)
    """
    try:
        content = si.RetrieveContent()
        container = content.rootFolder
        viewType = [vim.Folder]
        recursive = True
        
        containerView = content.viewManager.CreateContainerView(
            container, viewType, recursive
        )
        
        folders = []
        for folder in containerView.view:
            # Only include VM folders (not datastore, network, etc.)
            if hasattr(folder, 'childType') and vim.VirtualMachine in folder.childType:
                folder_path = get_folder_path(folder)
                # Exclude root folders and system folders
                if folder_path and folder_path not in ['vm', 'Datacenters']:
                    folders.append({
                        'name': folder.name,
                        'path': folder_path,
                        'obj': folder
                    })
        
        # Sort alphabetically by path
        folders.sort(key=lambda x: x['path'].lower())
        
        containerView.Destroy()
        return folders
        
    except Exception as e:
        logger.error(f"Error getting folders from vCenter: {e}")
        return []


def get_folder_path(folder):
    """
    Get full path of a folder
    
    Args:
        folder: Folder object
    
    Returns:
        str: Full path like "Datacenter/vm/Servidores-ABCFlex"
    """
    path = []
    current = folder
    
    while current:
        if hasattr(current, 'name') and current.name:
            path.insert(0, current.name)
        
        if hasattr(current, 'parent'):
            current = current.parent
        else:
            break
    
    return '/'.join(path)


def get_folder_by_path(si, folder_path):
    """
    Get folder object by its path
    
    Args:
        si: ServiceInstance connection
        folder_path: Full folder path
    
    Returns:
        Folder object or None
    """
    try:
        folders = get_all_folders(si)
        for folder in folders:
            if folder['path'] == folder_path:
                return folder['obj']
        return None
    except Exception as e:
        logger.error(f"Error getting folder by path: {e}")
        return None
