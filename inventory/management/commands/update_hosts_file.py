"""
Django management command to update /etc/hosts with all hosts from inventory.
"""
from django.core.management.base import BaseCommand
from inventory.models import Host


class Command(BaseCommand):
    help = 'Update /etc/hosts file with all active hosts from inventory'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Get all active hosts
        hosts = Host.objects.filter(active=True).order_by('name')
        
        self.stdout.write(self.style.SUCCESS(f'Found {hosts.count()} active hosts in inventory:'))
        
        for host in hosts:
            self.stdout.write(f'  - {host.ip}\t{host.name}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n--dry-run mode: No changes made to /etc/hosts'))
            return
        
        # Update /etc/hosts
        self.stdout.write('\nUpdating /etc/hosts...')
        
        try:
            # Use the first host to trigger update (it updates all hosts)
            if hosts.exists():
                first_host = hosts.first()
                first_host.update_etc_hosts()
                self.stdout.write(self.style.SUCCESS(f'\n✅ Successfully updated /etc/hosts with {hosts.count()} hosts'))
            else:
                self.stdout.write(self.style.WARNING('No active hosts found in inventory'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Error updating /etc/hosts: {str(e)}'))
            raise
