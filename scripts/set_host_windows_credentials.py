#!/usr/bin/env python3
"""
Set Windows credentials for a host
Usage: python set_host_windows_credentials.py <hostname_or_ip> <username> <password>
"""

import sys
import os
import django

# Setup Django
sys.path.insert(0, '/opt/www/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'diaken.settings')
django.setup()

from inventory.models import Host

def set_credentials(identifier, username, password):
    """Set Windows credentials for a host"""
    
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
        print(f"Windows User: {host.windows_user if host.windows_user else 'Not set'}")
        print(f"Windows Password: {'*' * len(host.windows_password) if host.windows_password else 'Not set'}")
        print(f"")
        
        # Update credentials
        print(f"{'='*60}")
        print(f"Updating Windows Credentials")
        print(f"{'='*60}")
        
        old_user = host.windows_user
        old_pass_len = len(host.windows_password) if host.windows_password else 0
        
        host.windows_user = username
        host.windows_password = password
        host.save()
        
        print(f"✓ Credentials updated successfully!")
        print(f"")
        print(f"  • Username: {old_user if old_user else 'None'} → {username}")
        print(f"  • Password: {'*' * old_pass_len if old_pass_len else 'None'} → {'*' * len(password)}")
        print(f"")
        
        # Show final configuration
        print(f"{'='*60}")
        print(f"Final Host Configuration")
        print(f"{'='*60}")
        print(f"Name: {host.name}")
        print(f"IP: {host.ip}")
        print(f"OS: {host.operating_system}")
        print(f"Windows User: {host.windows_user}")
        print(f"Windows Password: {'*' * len(host.windows_password)}")
        print(f"")
        
        print(f"✓ Host is now ready for Windows playbook execution!")
        print(f"")
        
        # Show test command
        print(f"{'='*60}")
        print(f"Test Connection Command")
        print(f"{'='*60}")
        print(f"python /opt/www/app/scripts/test_winrm_connection.py \\")
        print(f"  {host.ip} \\")
        print(f"  {username} \\")
        print(f"  '{password}' \\")
        print(f"  ntlm")
        print(f"")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: python set_host_windows_credentials.py <hostname_or_ip> <username> <password>")
        print("\nExamples:")
        print("  python set_host_windows_credentials.py WIN-SERVER-01 Administrator 'MyPassword123'")
        print("  python set_host_windows_credentials.py 10.100.5.87 administrator 'TestConexi0n'")
        sys.exit(1)
    
    identifier = sys.argv[1]
    username = sys.argv[2]
    password = sys.argv[3]
    
    success = set_credentials(identifier, username, password)
    sys.exit(0 if success else 1)
