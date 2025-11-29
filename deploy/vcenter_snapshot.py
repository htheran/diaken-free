"""
vCenter Snapshot Management Utilities
"""
import logging
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
import ssl
from datetime import datetime, timedelta
from django.utils import timezone
from settings.models import GlobalSetting

logger = logging.getLogger(__name__)


def get_vcenter_connection(vcenter_host, vcenter_user, vcenter_password):
    """
    Connect to vCenter server
    """
    try:
        context = ssl._create_unverified_context()
        si = SmartConnect(
            host=vcenter_host,
            user=vcenter_user,
            pwd=vcenter_password,
            port=443,
            sslContext=context
        )
        return si
    except Exception as e:
        logger.error(f"Failed to connect to vCenter {vcenter_host}: {e}")
        raise


def find_vm_by_ip(si, vm_ip):
    """
    Find VM by IP address or hostname
    
    Search criteria:
    1. VM guest IP address (from VMware Tools)
    2. VM name (exact match with IP or hostname)
    3. VM hostname (from VMware Tools)
    """
    content = si.RetrieveContent()
    container = content.rootFolder
    viewType = [vim.VirtualMachine]
    recursive = True
    
    containerView = content.viewManager.CreateContainerView(
        container, viewType, recursive
    )
    
    vms = containerView.view
    containerView.Destroy()
    
    logger.info(f"Searching for VM with IP/name: {vm_ip} among {len(vms)} VMs")
    
    for vm in vms:
        # Skip templates
        if vm.config and vm.config.template:
            continue
            
        # Method 1: Check VM guest IP (from VMware Tools)
        if vm.guest and vm.guest.ipAddress:
            if vm.guest.ipAddress == vm_ip:
                logger.info(f"Found VM by guest IP: {vm.name}")
                return vm
            
            # Check all NICs for matching IP
            if vm.guest.net:
                for nic in vm.guest.net:
                    if nic.ipAddress:
                        for ip in nic.ipAddress:
                            if ip == vm_ip:
                                logger.info(f"Found VM by NIC IP: {vm.name}")
                                return vm
        
        # Method 2: Check VM name (might be hostname or IP)
        if vm.name == vm_ip:
            logger.info(f"Found VM by name: {vm.name}")
            return vm
        
        # Method 3: Check VM hostname (from VMware Tools)
        if vm.guest and vm.guest.hostName:
            # Try exact match
            if vm.guest.hostName == vm_ip:
                logger.info(f"Found VM by hostname: {vm.name}")
                return vm
            # Try hostname without domain
            hostname_short = vm.guest.hostName.split('.')[0]
            if hostname_short == vm_ip:
                logger.info(f"Found VM by short hostname: {vm.name}")
                return vm
    
    logger.error(f"VM not found with IP/name: {vm_ip}")
    return None


def create_snapshot(si, vm_ip, snapshot_name, description=""):
    """
    Create a snapshot for a VM
    
    Args:
        si: vCenter connection
        vm_ip: IP address of the VM
        snapshot_name: Name for the snapshot
        description: Description for the snapshot
    
    Returns:
        tuple: (success: bool, message: str, snapshot_id: str)
    """
    try:
        vm = find_vm_by_ip(si, vm_ip)
        
        if not vm:
            return False, f"VM with IP {vm_ip} not found", None
        
        logger.info(f"Creating snapshot '{snapshot_name}' for VM {vm.name} ({vm_ip})")
        
        # Create snapshot WITHOUT memory and WITHOUT quiesce (simple disk snapshot)
        # memory=False: Does NOT capture RAM state
        #   - Smaller snapshot size
        #   - Faster creation
        # quiesce=False: Does NOT put guest filesystem in inactive mode
        #   - Faster snapshot creation
        #   - No VMware Tools requirement
        #   - Matches manual snapshot behavior
        task = vm.CreateSnapshot_Task(
            name=snapshot_name,
            description=description,
            memory=False,   # NO memory capture
            quiesce=False   # NO filesystem quiesce
        )
        
        logger.info(f"Snapshot parameters: memory=False, quiesce=False")
        
        # Wait for task to complete
        while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
            pass
        
        if task.info.state == vim.TaskInfo.State.success:
            # IMPORTANT: Refresh VM object to get updated snapshot list
            # vCenter doesn't update vm.snapshot automatically after CreateSnapshot_Task
            logger.info(f"Snapshot task completed, refreshing VM object...")
            
            # Re-fetch the VM to get updated snapshot information
            vm = find_vm_by_ip(si, vm_ip)
            
            # Get snapshot ID from the refreshed VM object
            snapshot_id = None
            if vm and vm.snapshot and vm.snapshot.rootSnapshotList:
                for snap in vm.snapshot.rootSnapshotList:
                    if snap.name == snapshot_name:
                        snapshot_id = str(snap.id)
                        logger.info(f"Found snapshot ID: {snapshot_id}")
                        break
            
            if not snapshot_id:
                logger.warning(f"Snapshot created but ID not found. VM snapshot property: {vm.snapshot if vm else 'VM not found'}")
            
            logger.info(f"Snapshot created successfully: {snapshot_name}")
            return True, f"Snapshot '{snapshot_name}' created successfully", snapshot_id
        else:
            error_msg = task.info.error.msg if task.info.error else "Unknown error"
            logger.error(f"Failed to create snapshot: {error_msg}")
            return False, f"Failed to create snapshot: {error_msg}", None
            
    except Exception as e:
        logger.error(f"Exception creating snapshot: {e}")
        return False, f"Exception creating snapshot: {str(e)}", None


def delete_snapshot(si, vm_ip, snapshot_name):
    """
    Delete a snapshot by name
    
    Args:
        si: vCenter connection
        vm_ip: IP address of the VM
        snapshot_name: Name of the snapshot to delete
    
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        vm = find_vm_by_ip(si, vm_ip)
        
        if not vm:
            return False, f"VM with IP {vm_ip} not found"
        
        if not vm.snapshot:
            return False, "VM has no snapshots"
        
        # Find snapshot by name
        snapshot_obj = None
        for snap in vm.snapshot.rootSnapshotList:
            if snap.name == snapshot_name:
                snapshot_obj = snap.snapshot
                break
        
        if not snapshot_obj:
            return False, f"Snapshot '{snapshot_name}' not found"
        
        logger.info(f"Deleting snapshot '{snapshot_name}' for VM {vm.name} ({vm_ip})")
        
        # Delete snapshot
        task = snapshot_obj.RemoveSnapshot_Task(removeChildren=False)
        
        # Wait for task to complete
        while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
            pass
        
        if task.info.state == vim.TaskInfo.State.success:
            logger.info(f"Snapshot deleted successfully: {snapshot_name}")
            return True, f"Snapshot '{snapshot_name}' deleted successfully"
        else:
            error_msg = task.info.error.msg if task.info.error else "Unknown error"
            logger.error(f"Failed to delete snapshot: {error_msg}")
            return False, f"Failed to delete snapshot: {error_msg}"
            
    except Exception as e:
        logger.error(f"Exception deleting snapshot: {e}")
        return False, f"Exception deleting snapshot: {str(e)}"


def cleanup_old_snapshots(si, vm_ip, retention_hours=24):
    """
    Delete snapshots older than retention_hours
    
    Args:
        si: vCenter connection
        vm_ip: IP address of the VM
        retention_hours: Hours to keep snapshots (exact, not rounded)
    
    Returns:
        list: List of deleted snapshot names
    """
    try:
        vm = find_vm_by_ip(si, vm_ip)
        
        if not vm:
            return []
        
        if not vm.snapshot:
            return []
        
        deleted_snapshots = []
        # Use timezone-aware UTC time for accurate comparison
        from datetime import timezone as dt_timezone
        cutoff_time = datetime.now(dt_timezone.utc) - timedelta(hours=retention_hours)
        
        # Create a copy of the snapshot list to avoid iteration issues during deletion
        # When we delete a snapshot, the original list changes, which can cause some snapshots to be skipped
        snapshot_list = list(vm.snapshot.rootSnapshotList)
        
        logger.info(f"cleanup_old_snapshots: VM {vm.name} has {len(snapshot_list)} snapshot(s)")
        
        for snap in snapshot_list:
            # Make snapshot time timezone-aware (vCenter returns UTC time)
            if snap.createTime.tzinfo is None:
                snap_time = snap.createTime.replace(tzinfo=dt_timezone.utc)
            else:
                snap_time = snap.createTime
            
            # Calculate age in hours for precise comparison
            age_hours = (datetime.now(dt_timezone.utc) - snap_time).total_seconds() / 3600
            
            # Check if snapshot name starts with "Before executing"
            if snap.name.startswith("Before executing"):
                # Get retention from snapshot history (each snapshot has its own retention)
                snapshot_retention = retention_hours  # Default
                try:
                    from snapshots.models import SnapshotHistory
                    snapshot_history = SnapshotHistory.objects.filter(
                        snapshot_name=snap.name,
                        status='active'
                    ).first()
                    if snapshot_history:
                        snapshot_retention = snapshot_history.retention_hours
                except Exception as hist_error:
                    logger.warning(f"Could not get retention from history for {snap.name}, using default: {hist_error}")
                
                # Check if snapshot is older than its specific retention
                if age_hours >= snapshot_retention:
                    logger.info(f"Deleting old snapshot: {snap.name} (created {snap_time}, age: {age_hours:.2f} hours, retention: {snapshot_retention} hours)")
                    
                    task = snap.snapshot.RemoveSnapshot_Task(removeChildren=False)
                    
                    while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
                        pass
                    
                    if task.info.state == vim.TaskInfo.State.success:
                        deleted_snapshots.append(snap.name)
                        
                        # Mark snapshot as deleted in history
                        try:
                            from snapshots.models import SnapshotHistory
                            snapshot_history = SnapshotHistory.objects.filter(
                                snapshot_name=snap.name,
                                status='active'
                            ).first()
                            if snapshot_history:
                                snapshot_history.mark_as_deleted()
                                logger.info(f"Snapshot marked as deleted in history: {snap.name}")
                        except Exception as hist_error:
                            logger.error(f"Failed to update snapshot history: {hist_error}")
        
        return deleted_snapshots
        
    except Exception as e:
        logger.error(f"Exception cleaning up snapshots: {e}")
        return []
