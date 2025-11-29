"""
Django management command to clear invalid encrypted credentials

This command is useful when the encryption key has changed and existing
credentials can no longer be decrypted.

Usage:
    python manage.py clear_invalid_credentials
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from settings.models import VCenterCredential, WindowsCredential
from security_fixes.credential_encryption import CredentialEncryptor


class Command(BaseCommand):
    help = 'Clear credentials that cannot be decrypted (invalid encryption token)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Skip confirmation prompt',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        
        self.stdout.write(self.style.WARNING(
            '\n' + '='*70 + '\n'
            'Clear Invalid Encrypted Credentials\n'
            '='*70 + '\n'
        ))
        
        # Initialize encryptor
        try:
            encryptor = CredentialEncryptor()
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f'Failed to initialize encryptor: {e}'
            ))
            return
        
        # Check vCenter credentials
        invalid_vcenter = []
        self.stdout.write('\nChecking vCenter credentials...')
        
        for cred in VCenterCredential.objects.all():
            try:
                # Try to decrypt password
                if cred.password:
                    encryptor.decrypt(cred.password)
                self.stdout.write(self.style.SUCCESS(
                    f'  ✓ {cred.name} - Valid'
                ))
            except Exception:
                self.stdout.write(self.style.ERROR(
                    f'  ✗ {cred.name} - Invalid (cannot decrypt)'
                ))
                invalid_vcenter.append(cred)
        
        # Check Windows credentials
        invalid_windows = []
        self.stdout.write('\nChecking Windows credentials...')
        
        for cred in WindowsCredential.objects.all():
            try:
                # Try to decrypt password
                if cred.password:
                    encryptor.decrypt(cred.password)
                self.stdout.write(self.style.SUCCESS(
                    f'  ✓ {cred.name} - Valid'
                ))
            except Exception:
                self.stdout.write(self.style.ERROR(
                    f'  ✗ {cred.name} - Invalid (cannot decrypt)'
                ))
                invalid_windows.append(cred)
        
        # Summary
        total_invalid = len(invalid_vcenter) + len(invalid_windows)
        
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.WARNING(
            f'Found {total_invalid} invalid credential(s):'
        ))
        self.stdout.write(f'  - vCenter: {len(invalid_vcenter)}')
        self.stdout.write(f'  - Windows: {len(invalid_windows)}')
        self.stdout.write('='*70 + '\n')
        
        if total_invalid == 0:
            self.stdout.write(self.style.SUCCESS(
                '✓ All credentials are valid. No action needed.'
            ))
            return
        
        # Ask for confirmation
        if not force and not dry_run:
            self.stdout.write(self.style.WARNING(
                '\nThis will permanently delete the invalid credentials.'
            ))
            self.stdout.write(self.style.WARNING(
                'You will need to re-create them in the admin panel.'
            ))
            
            confirm = input('\nDo you want to continue? (yes/no): ')
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.WARNING('Operation cancelled.'))
                return
        
        # Delete invalid credentials
        if dry_run:
            self.stdout.write(self.style.WARNING(
                '\n[DRY RUN] Would delete the following credentials:'
            ))
            for cred in invalid_vcenter:
                self.stdout.write(f'  - vCenter: {cred.name}')
            for cred in invalid_windows:
                self.stdout.write(f'  - Windows: {cred.name}')
        else:
            self.stdout.write('\nDeleting invalid credentials...')
            
            with transaction.atomic():
                vcenter_count = 0
                for cred in invalid_vcenter:
                    cred_name = cred.name
                    cred.delete()
                    vcenter_count += 1
                    self.stdout.write(self.style.SUCCESS(
                        f'  ✓ Deleted vCenter credential: {cred_name}'
                    ))
                
                windows_count = 0
                for cred in invalid_windows:
                    cred_name = cred.name
                    cred.delete()
                    windows_count += 1
                    self.stdout.write(self.style.SUCCESS(
                        f'  ✓ Deleted Windows credential: {cred_name}'
                    ))
            
            self.stdout.write('\n' + '='*70)
            self.stdout.write(self.style.SUCCESS(
                f'✓ Successfully deleted {total_invalid} invalid credential(s)'
            ))
            self.stdout.write(self.style.WARNING(
                '\n⚠  Please re-create the deleted credentials in:'
            ))
            self.stdout.write('   Settings > vCenter Credentials')
            self.stdout.write('   Settings > Windows Credentials')
            self.stdout.write('='*70 + '\n')
