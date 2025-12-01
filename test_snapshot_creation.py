#!/usr/bin/env python
"""
Test script to diagnose snapshot creation issues
Run with: sudo -u diaken /opt/diaken/venv/bin/python test_snapshot_creation.py
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, '/opt/diaken')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'diaken.settings')
django.setup()

from deploy.vcenter_snapshot import get_vcenter_connection, find_vm_by_ip, Disconnect
from settings.models import VCenterCredential
from inventory.models import Host
from datetime import datetime

def test_snapshot_creation():
    print("=" * 70)
    print("SNAPSHOT CREATION DIAGNOSTIC TEST")
    print("=" * 70)
    print()
    
    # Get host
    try:
        host = Host.objects.get(name='red07')
        print(f"✓ Found host: {host.name}")
        print(f"  IP: {host.ip}")
        print(f"  vCenter Server: {host.vcenter_server}")
        print()
    except Host.DoesNotExist:
        print("✗ Host 'red07' not found")
        return
    
    if not host.vcenter_server:
        print("✗ Host has no vCenter server configured")
        return
    
    # Get vCenter credentials
    try:
        vcenter_cred = VCenterCredential.objects.filter(host=host.vcenter_server).first()
        if not vcenter_cred:
            print(f"✗ No vCenter credentials found for {host.vcenter_server}")
            return
        print(f"✓ Found vCenter credentials")
        print(f"  Server: {host.vcenter_server}")
        print(f"  User: {vcenter_cred.user}")
        print()
    except Exception as e:
        print(f"✗ Error getting vCenter credentials: {e}")
        return
    
    # Connect to vCenter
    print("Connecting to vCenter...")
    try:
        si = get_vcenter_connection(
            host.vcenter_server,
            vcenter_cred.user,
            vcenter_cred.get_password()
        )
        print(f"✓ Connected to vCenter")
        print()
    except Exception as e:
        print(f"✗ Failed to connect to vCenter: {e}")
        return
    
    # Find VM
    print(f"Searching for VM with IP: {host.ip}")
    try:
        vm = find_vm_by_ip(si, host.ip)
        if not vm:
            print(f"✗ VM not found")
            Disconnect(si)
            return
        print(f"✓ Found VM: {vm.name}")
        print(f"  MoRef: {vm}")
        print(f"  Power State: {vm.runtime.powerState if vm.runtime else 'Unknown'}")
        print()
    except Exception as e:
        print(f"✗ Error finding VM: {e}")
        Disconnect(si)
        return
    
    # Check existing snapshots
    print("Checking existing snapshots...")
    if vm.snapshot and vm.snapshot.rootSnapshotList:
        print(f"  VM has {len(vm.snapshot.rootSnapshotList)} root snapshot(s)")
        for snap in vm.snapshot.rootSnapshotList:
            print(f"    - {snap.name} (ID: {snap.id})")
    else:
        print("  VM has no snapshots")
    print()
    
    # Create test snapshot
    snapshot_name = f"TEST-Snapshot-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    description = "Test snapshot from diagnostic script"
    
    print(f"Creating test snapshot: {snapshot_name}")
    print(f"  Description: {description}")
    print(f"  Parameters: memory=False, quiesce=False")
    print()
    
    try:
        from pyVmomi import vim
        
        print("Calling CreateSnapshot_Task...")
        task = vm.CreateSnapshot_Task(
            name=snapshot_name,
            description=description,
            memory=False,
            quiesce=False
        )
        print(f"✓ CreateSnapshot_Task called successfully")
        print(f"  Task: {task}")
        print(f"  Initial state: {task.info.state}")
        print()
        
        print("Waiting for task to complete...")
        import time
        start_time = time.time()
        timeout = 60  # 1 minute timeout
        
        while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
            if time.time() - start_time > timeout:
                print(f"✗ Task timeout after {timeout} seconds")
                print(f"  Last state: {task.info.state}")
                Disconnect(si)
                return
            time.sleep(1)
            print(f"  State: {task.info.state} (elapsed: {time.time() - start_time:.1f}s)")
        
        elapsed = time.time() - start_time
        print(f"\nTask completed in {elapsed:.2f} seconds")
        print(f"  Final state: {task.info.state}")
        print()
        
        if task.info.state == vim.TaskInfo.State.success:
            print("✓ Snapshot task succeeded!")
            print()
            
            # Verify snapshot was created
            print("Verifying snapshot in vCenter...")
            vm = find_vm_by_ip(si, host.ip)
            
            if vm.snapshot and vm.snapshot.rootSnapshotList:
                print(f"  VM now has {len(vm.snapshot.rootSnapshotList)} root snapshot(s)")
                found = False
                for snap in vm.snapshot.rootSnapshotList:
                    print(f"    - {snap.name} (ID: {snap.id})")
                    if snap.name == snapshot_name:
                        found = True
                        print(f"      ✓ THIS IS OUR NEW SNAPSHOT!")
                
                if found:
                    print()
                    print("✓✓✓ SUCCESS! Snapshot created and verified in vCenter ✓✓✓")
                else:
                    print()
                    print("✗✗✗ WARNING: Snapshot task succeeded but snapshot not found in VM ✗✗✗")
                    print("This indicates a vCenter permissions or configuration issue")
            else:
                print("  ✗ VM has no snapshots after creation")
                print("  This indicates a vCenter permissions or configuration issue")
        else:
            error_msg = task.info.error.msg if task.info.error else "Unknown error"
            print(f"✗ Snapshot task failed: {error_msg}")
            if task.info.error:
                print(f"  Error details: {task.info.error}")
        
    except Exception as e:
        print(f"✗ Exception during snapshot creation: {e}")
        print(f"  Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
    finally:
        Disconnect(si)
        print()
        print("=" * 70)
        print("TEST COMPLETED")
        print("=" * 70)

if __name__ == '__main__':
    test_snapshot_creation()
