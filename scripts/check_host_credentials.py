#!/usr/bin/env python3
"""
Check which Windows credential is assigned to a host
Usage: python check_host_credentials.py <hostname_or_ip>
"""

import sys
import os
import django

# Setup Django - use dynamic path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'diaken.settings')
django.setup()

from inventory.models import Host
from settings.models import WindowsCredential

def check_host_credentials(identifier):
    """Check credentials for a host by name or IP"""
    
    # Try to find host by name or IP
    try:
        host = Host.objects.filter(name=identifier).first()
        if not host:
            host = Host.objects.filter(ip=identifier).first()
        
        if not host:
            print(f"❌ Host not found: {identifier}")
            return False
        
        print(f"\n{'='*60}")
        print(f"Host Information")
        print(f"{'='*60}")
        print(f"Name: {host.name}")
        print(f"IP: {host.ip}")
        print(f"OS: {host.operating_system}")
        print(f"Environment: {host.environment.name}")
        print(f"Group: {host.group.name if host.group else 'None'}")
        print(f"Active: {host.active}")
        print(f"")
        
        # Check Windows credential
        if host.windows_credential:
            cred = host.windows_credential
            print(f"{'='*60}")
            print(f"Windows Credential (ASSIGNED)")
            print(f"{'='*60}")
            print(f"Credential Name: {cred.name}")
            print(f"Username: {cred.username}")
            print(f"Password: {'*' * len(cred.password)} (hidden)")
            print(f"Auth Type: {cred.auth_type}")
            print(f"Port: {cred.get_port()}")
            print(f"")
            
            print(f"⚠️  To test this credential, run:")
            print(f"python {os.path.join(BASE_DIR, 'scripts', 'test_winrm_connection.py')} \\")
            print(f"  {host.ip} \\")
            print(f"  {cred.username} \\")
            print(f"  'ACTUAL_PASSWORD_HERE' \\")
            print(f"  {cred.auth_type}")
            print(f"")
            
        else:
            print(f"{'='*60}")
            print(f"❌ NO Windows Credential Assigned")
            print(f"{'='*60}")
            print(f"")
            print(f"Available Windows Credentials:")
            print(f"{'-'*60}")
            
            all_creds = WindowsCredential.objects.all()
            if all_creds.exists():
                for cred in all_creds:
                    print(f"  ID: {cred.id} - {cred.name} ({cred.username})")
            else:
                print(f"  No Windows credentials configured in the system")
            
            print(f"")
            print(f"To assign a credential to this host:")
            print(f"1. Go to Settings > Windows Credentials")
            print(f"2. Create or select a credential")
            print(f"3. Go to Inventory > Hosts")
            print(f"4. Edit host '{host.name}'")
            print(f"5. Select the Windows Credential")
            print(f"")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python check_host_credentials.py <hostname_or_ip>")
        print("\nExamples:")
        print("  python check_host_credentials.py WIN-SERVER-01")
        print("  python check_host_credentials.py 10.100.5.87")
        sys.exit(1)
    
    identifier = sys.argv[1]
    success = check_host_credentials(identifier)
    sys.exit(0 if success else 1)
