from django.core.management.base import BaseCommand
from django.utils import timezone
from inventory.models import Host
from settings.models import GlobalSetting
from deploy.vcenter_snapshot import get_vcenter_connection, cleanup_old_snapshots, Disconnect
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Cleanup old vCenter snapshots based on retention policy'

    def handle(self, *args, **options):
        # Get retention hours from settings
        retention_setting = GlobalSetting.objects.filter(key='snapshot_retention_hours').first()
        retention_hours = int(retention_setting.value) if retention_setting else 24
        
        self.stdout.write(f'Cleaning up snapshots older than {retention_hours} hours...')
        
        # Get vCenter credentials from VCenterCredential model
        from settings.models import VCenterCredential
        
        # Get all hosts with vCenter server configured
        hosts = Host.objects.filter(vcenter_server__isnull=False, active=True).exclude(vcenter_server='')
        self.stdout.write(f'Found {hosts.count()} hosts with vCenter configured')
        
        # Group hosts by vCenter server
        vcenter_hosts = {}
        for host in hosts:
            if host.vcenter_server not in vcenter_hosts:
                vcenter_hosts[host.vcenter_server] = []
            vcenter_hosts[host.vcenter_server].append(host)
        
        self.stdout.write(f'Processing {len(vcenter_hosts)} vCenter servers')
        
        total_deleted = 0
        
        # Process each vCenter
        for vcenter_server, host_list in vcenter_hosts.items():
            try:
                # Get credentials for this specific vCenter
                vcenter_cred = VCenterCredential.objects.filter(host=vcenter_server).first()
                
                if not vcenter_cred:
                    self.stdout.write(self.style.WARNING(f'vCenter credential not found for {vcenter_server}. Skipping.'))
                    continue
                
                self.stdout.write(f'Connecting to vCenter: {vcenter_cred.name} ({vcenter_server})')
                
                si = get_vcenter_connection(
                    vcenter_server,
                    vcenter_cred.user,
                    vcenter_cred.get_password()  # Use decrypted password
                )
                
                for host in host_list:
                    self.stdout.write(f'  Processing host: {host.name} (IP: {host.ip})')
                    
                    # Try to cleanup by IP first
                    deleted = cleanup_old_snapshots(si, host.ip, retention_hours)
                    
                    # If no snapshots deleted and VM might not be found by IP, try by hostname
                    if not deleted:
                        self.stdout.write(f'    No snapshots found/deleted by IP, trying by hostname...')
                        deleted = cleanup_old_snapshots(si, host.name, retention_hours)
                    
                    if deleted:
                        total_deleted += len(deleted)
                        for snap_name in deleted:
                            self.stdout.write(self.style.SUCCESS(f'    ✓ Deleted: {snap_name}'))
                    else:
                        self.stdout.write(f'    No expired snapshots found for {host.name}')
                
                Disconnect(si)
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error processing vCenter {vcenter_server}: {e}'))
        
        self.stdout.write(self.style.SUCCESS(f'Cleanup complete. Total snapshots deleted: {total_deleted}'))
