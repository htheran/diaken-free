#!/usr/bin/env python3
"""
Fix Windows host configuration
Usage: python fix_windows_host.py <hostname_or_ip> <windows_credential_id>
"""

import sys
import os
import django

# Setup Django
sys.path.insert(0, '/opt/www/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'diaken.settings')
django.setup()

from inventory.models import Host
from settings.models import WindowsCredential

def fix_windows_host(identifier, credential_id):
    """Fix Windows host configuration"""
    
    try:
        # Find host
        host = Host.objects.filter(name=identifier).first()
        if not host:
            host = Host.objects.filter(ip=identifier).first()
        
        if not host:
            print(f"❌ Host not found: {identifier}")
            return False
        
        print(f"\n{'='*60}")
        print(f"Current Host Configuration")
        print(f"{'='*60}")
        print(f"Name: {host.name}")
        print(f"IP: {host.ip}")
        print(f"OS: {host.operating_system}")
        print(f"Active: {host.active}")
        print(f"Windows Credential: {host.windows_credential.name if host.windows_credential else 'None'}")
        print(f"")
        
        # Get Windows credential
        try:
            credential = WindowsCredential.objects.get(pk=credential_id)
        except WindowsCredential.DoesNotExist:
            print(f"❌ Windows Credential with ID {credential_id} not found")
            print(f"\nAvailable credentials:")
            for cred in WindowsCredential.objects.all():
                print(f"  ID: {cred.id} - {cred.name} ({cred.username})")
            return False
        
        # Update host
        print(f"{'='*60}")
        print(f"Updating Host Configuration")
        print(f"{'='*60}")
        
        changes = []
        
        if host.operating_system != 'windows':
            host.operating_system = 'windows'
            changes.append(f"OS: {host.operating_system} → windows")
        
        if not host.active:
            host.active = True
            changes.append(f"Active: False → True")
        
        if host.windows_credential != credential:
            old_cred = host.windows_credential.name if host.windows_credential else 'None'
            host.windows_credential = credential
            changes.append(f"Windows Credential: {old_cred} → {credential.name}")
        
        if changes:
            host.save()
            print(f"✓ Host updated successfully!")
            print(f"")
            for change in changes:
                print(f"  • {change}")
            print(f"")
        else:
            print(f"✓ No changes needed - host is already configured correctly")
            print(f"")
        
        # Show final configuration
        print(f"{'='*60}")
        print(f"Final Host Configuration")
        print(f"{'='*60}")
        print(f"Name: {host.name}")
        print(f"IP: {host.ip}")
        print(f"OS: {host.operating_system}")
        print(f"Active: {host.active}")
        print(f"Windows Credential: {host.windows_credential.name}")
        print(f"  - Username: {host.windows_credential.username}")
        print(f"  - Auth Type: {host.windows_credential.auth_type}")
        print(f"  - Port: {host.windows_credential.get_port()}")
        print(f"")
        
        print(f"✓ Host is now ready for Windows playbook execution!")
        print(f"")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python fix_windows_host.py <hostname_or_ip> <windows_credential_id>")
        print("\nExamples:")
        print("  python fix_windows_host.py WIN-SERVER-01 1")
        print("  python fix_windows_host.py 10.100.5.87 1")
        print("\nTo see available credentials, run:")
        print("  python check_host_credentials.py <hostname_or_ip>")
        sys.exit(1)
    
    identifier = sys.argv[1]
    credential_id = sys.argv[2]
    
    success = fix_windows_host(identifier, credential_id)
    sys.exit(0 if success else 1)
