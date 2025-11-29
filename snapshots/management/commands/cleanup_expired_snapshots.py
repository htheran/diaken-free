"""
Django management command to cleanup expired snapshots from database and vCenter
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from snapshots.models import SnapshotHistory
from settings.models import VCenterCredential
from deploy.vcenter_snapshot import get_vcenter_connection, delete_snapshot, Disconnect
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Cleanup expired snapshots from database and vCenter'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
        parser.add_argument(
            '--delete-from-vcenter',
            action='store_true',
            help='Also delete snapshots from vCenter (not just mark as deleted in DB)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        delete_from_vcenter = options['delete_from_vcenter']
        
        self.stdout.write(self.style.WARNING(f'Mode: {"DRY RUN" if dry_run else "LIVE"}'))
        if delete_from_vcenter:
            self.stdout.write(self.style.WARNING('Will also delete from vCenter'))
        
        # Find all expired snapshots that are still active
        now = timezone.now()
        expired_snapshots = SnapshotHistory.objects.filter(
            status='active',
            expires_at__lte=now
        ).order_by('expires_at')
        
        total_count = expired_snapshots.count()
        self.stdout.write(f'\nFound {total_count} expired snapshots')
        
        if total_count == 0:
            self.stdout.write(self.style.SUCCESS('✓ No expired snapshots to cleanup'))
            return
        
        # Show summary
        self.stdout.write('\nExpired snapshots:')
        for snapshot in expired_snapshots[:10]:  # Show first 10
            expired_hours = (now - snapshot.expires_at).total_seconds() / 3600
            self.stdout.write(
                f'  - {snapshot.snapshot_name} ({snapshot.host.name}) '
                f'- Expired {expired_hours:.1f}h ago'
            )
        
        if total_count > 10:
            self.stdout.write(f'  ... and {total_count - 10} more')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n[DRY RUN] No changes made'))
            return
        
        # Delete expired snapshots
        deleted_count = 0
        failed_count = 0
        
        for snapshot in expired_snapshots:
            try:
                # Delete from vCenter if requested
                if delete_from_vcenter and snapshot.host.vcenter_server:
                    try:
                        vcenter_cred = VCenterCredential.objects.filter(
                            host=snapshot.host.vcenter_server
                        ).first()
                        
                        if vcenter_cred:
                            si = get_vcenter_connection(
                                snapshot.host.vcenter_server,
                                vcenter_cred.user,
                                vcenter_cred.get_password()  # Use decrypted password
                            )
                            
                            # Try to delete by snapshot name
                            success = delete_snapshot(
                                si,
                                snapshot.host.ip,
                                snapshot.snapshot_name
                            )
                            
                            Disconnect(si)
                            
                            if success:
                                self.stdout.write(
                                    self.style.SUCCESS(
                                        f'  ✓ Deleted from vCenter: {snapshot.snapshot_name}'
                                    )
                                )
                            else:
                                self.stdout.write(
                                    self.style.WARNING(
                                        f'  ⚠ Could not delete from vCenter: {snapshot.snapshot_name}'
                                    )
                                )
                        else:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'  ⚠ No vCenter credentials for {snapshot.host.vcenter_server}'
                                )
                            )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(
                                f'  ✗ Error deleting from vCenter: {snapshot.snapshot_name} - {e}'
                            )
                        )
                
                # Mark as deleted in database
                snapshot.status = 'deleted'
                snapshot.deleted_at = now
                snapshot.save()
                
                deleted_count += 1
                self.stdout.write(
                    f'  ✓ Marked as deleted: {snapshot.snapshot_name} ({snapshot.host.name})'
                )
                
            except Exception as e:
                failed_count += 1
                logger.error(f'Error deleting snapshot {snapshot.snapshot_name}: {e}', exc_info=True)
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Failed: {snapshot.snapshot_name} - {e}')
                )
        
        # Summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'✓ Successfully deleted: {deleted_count}'))
        if failed_count > 0:
            self.stdout.write(self.style.ERROR(f'✗ Failed: {failed_count}'))
        self.stdout.write('='*60)
