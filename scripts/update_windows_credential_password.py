#!/usr/bin/env python3
"""
Update Windows credential password
Usage: python update_windows_credential_password.py <credential_id> <new_password>
"""

import sys
import os
import django

# Setup Django
sys.path.insert(0, '/opt/www/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'diaken.settings')
django.setup()

from settings.models import WindowsCredential

def update_password(credential_id, new_password):
    """Update Windows credential password"""
    
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
        print(f"Updating Windows Credential Password")
        print(f"{'='*60}")
        print(f"Credential: {credential.name}")
        print(f"Username: {credential.username}")
        print(f"Auth Type: {credential.auth_type}")
        print(f"Port: {credential.get_port()}")
        print(f"")
        
        # Update password
        credential.password = new_password
        credential.save()
        
        print(f"✓ Password updated successfully!")
        print(f"")
        
        # Show hosts using this credential
        from inventory.models import Host
        hosts = Host.objects.filter(windows_credential=credential)
        
        if hosts.exists():
            print(f"{'='*60}")
            print(f"Hosts Using This Credential ({hosts.count()})")
            print(f"{'='*60}")
            for host in hosts:
                print(f"  • {host.name} ({host.ip})")
            print(f"")
            print(f"✓ All these hosts will now use the updated password")
        else:
            print(f"⚠️  No hosts are currently using this credential")
        
        print(f"")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python update_windows_credential_password.py <credential_id> <new_password>")
        print("\nExamples:")
        print("  python update_windows_credential_password.py 1 'MyNewPassword123'")
        print("\nTo see available credentials:")
        print("  python -c \"import django; import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'diaken.settings'); django.setup(); from settings.models import WindowsCredential; [print(f'ID: {c.id} - {c.name} ({c.username})') for c in WindowsCredential.objects.all()]\"")
        sys.exit(1)
    
    credential_id = sys.argv[1]
    new_password = sys.argv[2]
    
    success = update_password(credential_id, new_password)
    sys.exit(0 if success else 1)
