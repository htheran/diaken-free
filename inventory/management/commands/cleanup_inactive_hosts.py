"""
Django management command to clean up inactive hosts from the database.
"""
from django.core.management.base import BaseCommand
from inventory.models import Host
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = 'Clean up inactive hosts from the database to avoid saturation'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without making changes',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Delete hosts inactive for more than N days (default: 30)',
        )
        parser.add_argument(
            '--all-inactive',
            action='store_true',
            help='Delete ALL inactive hosts regardless of age',
        )
        parser.add_argument(
            '--duplicates',
            action='store_true',
            help='Delete duplicate hosts (keep only the most recent active one)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        days = options['days']
        all_inactive = options['all_inactive']
        duplicates_only = options['duplicates']
        
        self.stdout.write(self.style.WARNING('\n=== CLEANUP INACTIVE HOSTS ===\n'))
        
        # Get all hosts
        all_hosts = Host.objects.all()
        active_hosts = Host.objects.filter(active=True)
        inactive_hosts = Host.objects.filter(active=False)
        
        self.stdout.write(f'Total hosts in database: {all_hosts.count()}')
        self.stdout.write(f'Active hosts: {active_hosts.count()}')
        self.stdout.write(f'Inactive hosts: {inactive_hosts.count()}\n')
        
        # Show active hosts
        self.stdout.write(self.style.SUCCESS('\n=== ACTIVE HOSTS (will be kept) ==='))
        for host in active_hosts.order_by('name'):
            self.stdout.write(f'  ✓ {host.name} ({host.ip})')
        
        # Find duplicates
        if duplicates_only:
            self.stdout.write(self.style.WARNING('\n=== DUPLICATE HOSTS ==='))
            self._cleanup_duplicates(dry_run)
            return
        
        # Find hosts to delete
        hosts_to_delete = []
        
        if all_inactive:
            hosts_to_delete = list(inactive_hosts)
            self.stdout.write(self.style.WARNING(f'\n=== ALL INACTIVE HOSTS (to be deleted) ==='))
        else:
            # Delete hosts inactive for more than N days
            cutoff_date = timezone.now() - timedelta(days=days)
            # Note: This assumes there's a 'modified' or 'created' field
            # If not, we'll just delete all inactive hosts
            hosts_to_delete = list(inactive_hosts)
            self.stdout.write(self.style.WARNING(f'\n=== INACTIVE HOSTS (to be deleted) ==='))
        
        if not hosts_to_delete:
            self.stdout.write(self.style.SUCCESS('\n✓ No hosts to delete'))
            return
        
        # Group by name to show duplicates
        from collections import defaultdict
        hosts_by_name = defaultdict(list)
        for host in hosts_to_delete:
            hosts_by_name[host.name].append(host)
        
        total_to_delete = 0
        for name, hosts in sorted(hosts_by_name.items()):
            if len(hosts) > 1:
                self.stdout.write(f'\n  {name} (DUPLICATES: {len(hosts)}):')
            else:
                self.stdout.write(f'\n  {name}:')
            
            for host in hosts:
                self.stdout.write(f'    - ID: {host.pk}, IP: {host.ip}, Active: {host.active}')
                total_to_delete += 1
        
        self.stdout.write(f'\n{self.style.WARNING(f"Total hosts to delete: {total_to_delete}")}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n--dry-run mode: No changes made'))
            self.stdout.write(f'\nTo actually delete these hosts, run:')
            if all_inactive:
                self.stdout.write(f'  python manage.py cleanup_inactive_hosts --all-inactive')
            else:
                self.stdout.write(f'  python manage.py cleanup_inactive_hosts --days {days}')
            return
        
        # Confirm deletion
        self.stdout.write(self.style.ERROR(f'\n⚠️  WARNING: This will permanently delete {total_to_delete} hosts!'))
        confirm = input('Are you sure you want to continue? (yes/no): ')
        
        if confirm.lower() != 'yes':
            self.stdout.write(self.style.WARNING('\nCancelled. No hosts were deleted.'))
            return
        
        # Delete hosts
        self.stdout.write('\nDeleting hosts...')
        deleted_count = 0
        for host in hosts_to_delete:
            host_name = host.name
            host_ip = host.ip
            try:
                host.delete()  # This will also remove from /etc/hosts
                deleted_count += 1
                self.stdout.write(f'  ✓ Deleted: {host_name} ({host_ip})')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ Error deleting {host_name}: {e}'))
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Successfully deleted {deleted_count} hosts'))
        
        # Update /etc/hosts
        self.stdout.write('\nUpdating /etc/hosts...')
        remaining_host = Host.objects.filter(active=True).first()
        if remaining_host:
            remaining_host.update_etc_hosts()
            self.stdout.write(self.style.SUCCESS('✅ /etc/hosts updated'))
        
        # Show final stats
        final_total = Host.objects.count()
        final_active = Host.objects.filter(active=True).count()
        final_inactive = Host.objects.filter(active=False).count()
        
        self.stdout.write(self.style.SUCCESS(f'\n=== FINAL STATS ==='))
        self.stdout.write(f'Total hosts: {all_hosts.count()} → {final_total} (-{all_hosts.count() - final_total})')
        self.stdout.write(f'Active hosts: {active_hosts.count()} → {final_active}')
        self.stdout.write(f'Inactive hosts: {inactive_hosts.count()} → {final_inactive} (-{inactive_hosts.count() - final_inactive})')
    
    def _cleanup_duplicates(self, dry_run):
        """Clean up duplicate hosts, keeping only the most recent active one."""
        from collections import defaultdict
        
        # Group hosts by name
        hosts_by_name = defaultdict(list)
        for host in Host.objects.all().order_by('name', '-active', '-id'):
            hosts_by_name[host.name].append(host)
        
        # Find duplicates
        duplicates_found = False
        hosts_to_delete = []
        
        for name, hosts in sorted(hosts_by_name.items()):
            if len(hosts) > 1:
                duplicates_found = True
                self.stdout.write(f'\n  {name} ({len(hosts)} duplicates):')
                
                # Keep the first one (most recent active)
                keep_host = hosts[0]
                self.stdout.write(f'    ✓ KEEP: ID={keep_host.pk}, IP={keep_host.ip}, Active={keep_host.active}')
                
                # Delete the rest
                for host in hosts[1:]:
                    self.stdout.write(f'    ✗ DELETE: ID={host.pk}, IP={host.ip}, Active={host.active}')
                    hosts_to_delete.append(host)
        
        if not duplicates_found:
            self.stdout.write(self.style.SUCCESS('\n✓ No duplicates found'))
            return
        
        self.stdout.write(f'\n{self.style.WARNING(f"Total duplicate hosts to delete: {len(hosts_to_delete)}")}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n--dry-run mode: No changes made'))
            self.stdout.write(f'\nTo actually delete these duplicates, run:')
            self.stdout.write(f'  python manage.py cleanup_inactive_hosts --duplicates')
            return
        
        # Confirm deletion
        self.stdout.write(self.style.ERROR(f'\n⚠️  WARNING: This will permanently delete {len(hosts_to_delete)} duplicate hosts!'))
        confirm = input('Are you sure you want to continue? (yes/no): ')
        
        if confirm.lower() != 'yes':
            self.stdout.write(self.style.WARNING('\nCancelled. No hosts were deleted.'))
            return
        
        # Delete duplicates
        self.stdout.write('\nDeleting duplicate hosts...')
        deleted_count = 0
        for host in hosts_to_delete:
            try:
                host.delete()
                deleted_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ Error deleting {host.name}: {e}'))
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Successfully deleted {deleted_count} duplicate hosts'))
