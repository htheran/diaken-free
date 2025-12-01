#!/usr/bin/env python
"""
Script to diagnose and show IP mismatches between Diaken database and vCenter
Run with: sudo -u diaken /opt/diaken/venv/bin/python diagnose_host_ips.py
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
from pyVmomi import vim

def diagnose_all_hosts():
    print("=" * 80)
    print("DIAKEN vs vCENTER IP MISMATCH DIAGNOSTIC")
    print("=" * 80)
    print()
    
    hosts = Host.objects.filter(active=True, vcenter_server__isnull=False)
    
    if not hosts:
        print("No active hosts with vCenter server configured")
        return
    
    print(f"Found {hosts.count()} active host(s) with vCenter configured\n")
    
    mismatches = []
    
    for host in hosts:
        print(f"{'=' * 80}")
        print(f"HOST: {host.name}")
        print(f"{'=' * 80}")
        print(f"  IP in Diaken DB: {host.ip}")
        print(f"  vCenter Server: {host.vcenter_server}")
        
        try:
            # Get vCenter credentials
            vcenter_cred = VCenterCredential.objects.filter(host=host.vcenter_server).first()
            
            if not vcenter_cred:
                print(f"  ✗ No vCenter credentials found")
                print()
                continue
            
            # Connect to vCenter
            si = get_vcenter_connection(
                host.vcenter_server,
                vcenter_cred.user,
                vcenter_cred.get_password()
            )
            
            # Search by IP from database
            print(f"\n  Searching vCenter by IP: {host.ip}")
            vm_by_ip = find_vm_by_ip(si, host.ip)
            
            if vm_by_ip:
                vm_ip_real = vm_by_ip.guest.ipAddress if vm_by_ip.guest else "No IP"
                print(f"    ✓ Found VM: {vm_by_ip.name}")
                print(f"    VM IP in vCenter: {vm_ip_real}")
                
                if vm_by_ip.name != host.name:
                    print(f"    ⚠️  WARNING: VM name mismatch!")
                    print(f"    Expected: {host.name}")
                    print(f"    Found: {vm_by_ip.name}")
                    mismatches.append({
                        'host': host.name,
                        'ip_in_db': host.ip,
                        'vm_found': vm_by_ip.name,
                        'vm_ip': vm_ip_real,
                        'issue': 'VM name mismatch'
                    })
            else:
                print(f"    ✗ No VM found with IP {host.ip}")
            
            # Search by hostname
            print(f"\n  Searching vCenter by hostname: {host.name}")
            vm_by_name = find_vm_by_ip(si, host.name)
            
            if vm_by_name:
                vm_name_ip = vm_by_name.guest.ipAddress if vm_by_name.guest else "No IP"
                print(f"    ✓ Found VM: {vm_by_name.name}")
                print(f"    VM IP in vCenter: {vm_name_ip}")
                
                if vm_name_ip != host.ip:
                    print(f"    ⚠️  WARNING: IP mismatch!")
                    print(f"    IP in Diaken DB: {host.ip}")
                    print(f"    IP in vCenter: {vm_name_ip}")
                    mismatches.append({
                        'host': host.name,
                        'ip_in_db': host.ip,
                        'vm_found': vm_by_name.name,
                        'vm_ip': vm_name_ip,
                        'issue': 'IP mismatch'
                    })
                    print(f"\n    💡 SOLUTION: Update IP in Diaken to: {vm_name_ip}")
            else:
                print(f"    ✗ No VM found with name {host.name}")
                print(f"    ⚠️  VM may not exist in vCenter or VMware Tools not running")
            
            Disconnect(si)
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
        
        print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    if mismatches:
        print(f"\n⚠️  Found {len(mismatches)} mismatch(es):\n")
        for m in mismatches:
            print(f"  Host: {m['host']}")
            print(f"    Issue: {m['issue']}")
            print(f"    IP in Diaken: {m['ip_in_db']}")
            print(f"    VM found: {m['vm_found']}")
            print(f"    VM IP in vCenter: {m['vm_ip']}")
            print()
        
        print("=" * 80)
        print("RECOMMENDED ACTIONS")
        print("=" * 80)
        print()
        print("1. Update IPs in Diaken:")
        print("   - Go to: Inventory → Hosts")
        print("   - Edit each host with mismatch")
        print("   - Update IP to match vCenter")
        print()
        print("2. Update /etc/hosts:")
        print("   sudo -u diaken venv/bin/python manage.py update_hosts_file")
        print()
        print("3. Test snapshots again")
        print()
    else:
        print("\n✓ No mismatches found! All hosts have correct IPs.")
        print()

if __name__ == '__main__':
    diagnose_all_hosts()
