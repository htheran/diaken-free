from django.core.management.base import BaseCommand
from inventory.models import Host

class Command(BaseCommand):
    help = 'Update /etc/hosts with all active hosts from inventory'

    def handle(self, *args, **options):
        hosts = Host.objects.filter(active=True).order_by('name')
        
        if not hosts.exists():
            self.stdout.write(self.style.WARNING('No active hosts found in inventory'))
            return
        
        # Trigger update by calling update_etc_hosts on any host
        # (it will update all hosts)
        first_host = hosts.first()
        first_host.update_etc_hosts()
        
        self.stdout.write(self.style.SUCCESS(f'Successfully updated /etc/hosts with {hosts.count()} hosts:'))
        for host in hosts:
            self.stdout.write(f'  {host.ip}\t{host.name}')
