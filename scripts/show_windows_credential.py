#!/usr/bin/env python3
"""
Show Windows credential details (including password)
Usage: python show_windows_credential.py <credential_id>
"""

import sys
import os
import django

# Setup Django - use dynamic path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'diaken.settings')
django.setup()

from settings.models import WindowsCredential
from inventory.models import Host

def show_credential(credential_id):
    """Show Windows credential details"""
    
    try:
        # Get credential
        try:
            credential = WindowsCredential.objects.get(pk=credential_id)
        except WindowsCredential.DoesNotExist:
            print(f"❌ Windows Credential with ID {credential_id} not found")
            print(f"\nAvailable credentials:")
            for cred in WindowsCredential.objects.all():
                print(f"  ID: {cred.id} - {cred.name} ({cred.username})")
            return False
        
        print(f"\n{'='*60}")
        print(f"Windows Credential Details")
        print(f"{'='*60}")
        print(f"ID: {credential.id}")
        print(f"Name: {credential.name}")
        print(f"Username: {credential.username}")
        print(f"Password: {credential.password}")
        print(f"Auth Type: {credential.auth_type}")
        print(f"Port: {credential.get_port()}")
        print(f"")
        
        # Show hosts using this credential
        hosts = Host.objects.filter(windows_credential=credential)
        
        if hosts.exists():
            print(f"{'='*60}")
            print(f"Hosts Using This Credential ({hosts.count()})")
            print(f"{'='*60}")
            for host in hosts:
                status = "✓ Active" if host.active else "✗ Inactive"
                print(f"  • {host.name} ({host.ip}) - {status}")
            print(f"")
        else:
            print(f"⚠️  No hosts are currently using this credential")
            print(f"")
        
        # Show test command
        if hosts.exists():
            first_host = hosts.first()
            print(f"{'='*60}")
            print(f"Test Connection Command")
            print(f"{'='*60}")
            print(f"python {os.path.join(BASE_DIR, 'scripts', 'test_winrm_connection.py')} \\")
            print(f"  {first_host.ip} \\")
            print(f"  {credential.username} \\")
            print(f"  '{credential.password}' \\")
            print(f"  {credential.auth_type}")
            print(f"")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python show_windows_credential.py <credential_id>")
        print("\nTo list all credentials:")
        print("  python show_windows_credential.py list")
        sys.exit(1)
    
    if sys.argv[1] == 'list':
        from settings.models import WindowsCredential
        print("\nAvailable Windows Credentials:")
        print("="*60)
        for cred in WindowsCredential.objects.all():
            print(f"ID: {cred.id} - {cred.name} ({cred.username})")
        print("")
        sys.exit(0)
    
    credential_id = sys.argv[1]
    success = show_credential(credential_id)
    sys.exit(0 if success else 1)
