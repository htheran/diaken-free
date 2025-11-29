#!/usr/bin/env python
"""
Test Windows credential connection
Usage: python test_windows_credential.py <credential_name> <ip_address>
"""
import os
import sys
import django

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'diaken.settings_production')
django.setup()

from settings.models import WindowsCredential
import winrm

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python test_windows_credential.py <credential_name> <ip_address>")
        print("\nAvailable credentials:")
        for cred in WindowsCredential.objects.all():
            print(f"  - {cred.name} ({cred.username})")
        sys.exit(1)
    
    cred_name = sys.argv[1]
    ip = sys.argv[2]
    
    try:
        cred = WindowsCredential.objects.get(name=cred_name)
        username = cred.username
        password = cred.get_password()
        
        print(f"Testing connection to {ip}...")
        print(f"  Credential: {cred.name}")
        print(f"  Username: {username}")
        print(f"  Auth type: {cred.auth_type}")
        print(f"  Port: {cred.get_port()}")
        print(f"  Protocol: {cred.get_protocol()}")
        print()
        
        # Test WinRM connection
        endpoint = f"{cred.get_protocol()}://{ip}:{cred.get_port()}/wsman"
        print(f"Connecting to: {endpoint}")
        
        session = winrm.Session(
            endpoint,
            auth=(username, password),
            transport=cred.auth_type,
            server_cert_validation='ignore'
        )
        
        # Try a simple command
        result = session.run_cmd('echo', ['Hello from DIAKEN'])
        
        if result.status_code == 0:
            print("\n✓✓✓ CONNECTION SUCCESSFUL ✓✓✓")
            print(f"Output: {result.std_out.decode('utf-8').strip()}")
        else:
            print(f"\n✗ Command failed with status code: {result.status_code}")
            print(f"Error: {result.std_err.decode('utf-8')}")
            
    except WindowsCredential.DoesNotExist:
        print(f"✗ Credential '{cred_name}' not found")
        print("\nAvailable credentials:")
        for cred in WindowsCredential.objects.all():
            print(f"  - {cred.name} ({cred.username})")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗✗✗ CONNECTION FAILED ✗✗✗")
        print(f"Error: {e}")
        print("\nPossible causes:")
        print("  1. Incorrect username or password")
        print("  2. WinRM not enabled on target server")
        print("  3. Firewall blocking port 5985/5986")
        print("  4. Authentication type mismatch")
        sys.exit(1)
