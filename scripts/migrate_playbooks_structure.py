#!/usr/bin/env python3
"""
Migrate playbooks from old structure to new OS-based structure
Old: media/playbooks/{target_type}/{filename}
New: media/playbooks/{os_family}/{target_type}/{filename}
"""

import sys
import os
import shutil
import django

# Setup Django - use dynamic path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'diaken.settings')
django.setup()

from playbooks.models import Playbook
from django.conf import settings


def detect_os_family(filename):
    """Detect OS family from filename"""
    filename_lower = filename.lower()
    
    if 'windows' in filename_lower or 'win' in filename_lower:
        return 'windows'
    elif 'debian' in filename_lower or 'ubuntu' in filename_lower:
        return 'debian'
    elif 'redhat' in filename_lower or 'centos' in filename_lower or 'rhel' in filename_lower:
        return 'redhat'
    
    # Default to redhat for generic playbooks
    return 'redhat'


def migrate_playbooks():
    """Migrate existing playbooks to new structure"""
    print("=" * 70)
    print("Migrating Playbooks to New Structure")
    print("=" * 70)
    
    media_root = str(settings.MEDIA_ROOT)
    old_base = os.path.join(media_root, 'playbooks')
    
    migrated = 0
    errors = 0
    skipped = 0
    
    # Process playbooks from database
    for playbook in Playbook.objects.all():
        try:
            if not playbook.file:
                print(f"⚠️  Skipping {playbook.name}: No file associated")
                skipped += 1
                continue
            
            old_path = os.path.join(media_root, str(playbook.file))
            
            if not os.path.exists(old_path):
                print(f"⚠️  File not found: {old_path}")
                skipped += 1
                continue
            
            # Detect OS family if not set correctly
            filename = os.path.basename(old_path)
            detected_os = detect_os_family(filename)
            
            # Update OS family if detection differs
            if playbook.os_family != detected_os:
                print(f"📝 Updating OS family for {playbook.name}: {playbook.os_family} -> {detected_os}")
                playbook.os_family = detected_os
                playbook.save()
            
            # New path based on model
            new_relative_path = f"playbooks/{playbook.os_family}/{playbook.playbook_type}/{filename}"
            new_path = os.path.join(media_root, new_relative_path)
            
            # Skip if already in correct location
            if old_path == new_path:
                print(f"✅ Already migrated: {playbook.name}")
                migrated += 1
                continue
            
            # Create directory if it doesn't exist
            new_dir = os.path.dirname(new_path)
            os.makedirs(new_dir, exist_ok=True)
            
            # Move file
            if os.path.exists(new_path):
                print(f"⚠️  Target exists, backing up: {new_path}")
                backup_path = new_path + '.backup'
                shutil.move(new_path, backup_path)
            
            shutil.move(old_path, new_path)
            
            # Update database
            playbook.file = new_relative_path
            playbook.save(update_fields=['file'])
            
            print(f"✅ Migrated: {playbook.name}")
            print(f"   From: {old_path}")
            print(f"   To:   {new_path}")
            migrated += 1
            
        except Exception as e:
            print(f"❌ Error migrating {playbook.name}: {e}")
            errors += 1
    
    # Process orphan files (not in database)
    print("\n" + "=" * 70)
    print("Checking for orphan playbook files...")
    print("=" * 70)
    
    for target_type in ['host', 'group']:
        old_dir = os.path.join(old_base, target_type)
        if not os.path.exists(old_dir):
            continue
        
        for filename in os.listdir(old_dir):
            if not filename.endswith(('.yml', '.yaml')):
                continue
            
            old_file_path = os.path.join(old_dir, filename)
            
            # Check if this file is in database
            in_db = Playbook.objects.filter(file__icontains=filename).exists()
            
            if not in_db:
                print(f"\n⚠️  Orphan file found: {filename}")
                print(f"   Location: {old_file_path}")
                
                # Detect OS and move
                os_family = detect_os_family(filename)
                new_path = os.path.join(old_base, os_family, target_type, filename)
                
                os.makedirs(os.path.dirname(new_path), exist_ok=True)
                shutil.move(old_file_path, new_path)
                
                print(f"   Moved to: {new_path}")
                print(f"   💡 Consider adding this playbook to the database")
    
    print("\n" + "=" * 70)
    print("Migration Summary")
    print("=" * 70)
    print(f"✅ Migrated:  {migrated}")
    print(f"⚠️  Skipped:   {skipped}")
    print(f"❌ Errors:    {errors}")
    print(f"\nNew structure:")
    print(f"  media/playbooks/{{os_family}}/{{target_type}}/{{filename}}")
    print(f"  - os_family: windows, redhat, debian")
    print(f"  - target_type: host, group")
    print("=" * 70)


if __name__ == '__main__':
    migrate_playbooks()
