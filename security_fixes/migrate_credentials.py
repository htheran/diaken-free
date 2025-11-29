#!/usr/bin/env python
"""Script to migrate existing plaintext credentials to encrypted format"""

import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'diaken.settings')
django.setup()

from settings.models import VCenterCredential, WindowsCredential, DeploymentCredential
from security_fixes.credential_encryption import CredentialEncryptor

def migrate_credentials():
    print("="* 70)
    print("🔐 CREDENTIAL MIGRATION TOOL")
    print("=" * 70)
    
    try:
        encryptor = CredentialEncryptor()
        print("✅ ENCRYPTION_KEY configured correctly\n")
    except ValueError as e:
        print(f"❌ ERROR: {e}")
        return False
    
    stats = {'vcenter': 0, 'windows': 0, 'deployment': 0}
    
    # Migrate VCenter
    print("\n📍 Migrating VCenterCredential...")
    for cred in VCenterCredential.objects.all():
        if cred.password and not cred.password.startswith('gAAAAA'):
            encrypted = encryptor.encrypt(cred.password)
            VCenterCredential.objects.filter(pk=cred.pk).update(password=encrypted)
            print(f"  ✓ Encrypted: {cred.name}")
            stats['vcenter'] += 1
    
    # Migrate Windows
    print("\n📍 Migrating WindowsCredential...")
    for cred in WindowsCredential.objects.all():
        if cred.password and not cred.password.startswith('gAAAAA'):
            encrypted = encryptor.encrypt(cred.password)
            WindowsCredential.objects.filter(pk=cred.pk).update(password=encrypted)
            print(f"  ✓ Encrypted: {cred.name}")
            stats['windows'] += 1
    
    # Migrate Deployment
    print("\n📍 Migrating DeploymentCredential...")
    for cred in DeploymentCredential.objects.all():
        if cred.password and not cred.password.startswith('gAAAAA'):
            encrypted = encryptor.encrypt(cred.password)
            DeploymentCredential.objects.filter(pk=cred.pk).update(password=encrypted)
            print(f"  ✓ Encrypted: {cred.name}")
            stats['deployment'] += 1
    
    print("\n" + "=" * 70)
    print("📊 SUMMARY")
    print(f"VCenter: {stats['vcenter']} | Windows: {stats['windows']} | Deployment: {stats['deployment']}")
    print("✅ Migration completed!\n")
    return True

if __name__ == '__main__':
    migrate_credentials()
