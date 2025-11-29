from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from playbooks.models import Playbook


class Command(BaseCommand):
    help = 'Create an example playbook for testing'

    def handle(self, *args, **options):
        # Example playbook content
        playbook_content = """---
- name: System Information Gathering
  hosts: all
  become: yes
  gather_facts: yes
  
  tasks:
    - name: Display system information
      debug:
        msg: |
          Hostname: {{ ansible_hostname }}
          OS: {{ ansible_distribution }} {{ ansible_distribution_version }}
          Kernel: {{ ansible_kernel }}
          Architecture: {{ ansible_architecture }}
          
    - name: Check disk usage
      shell: df -h
      register: disk_usage
      
    - name: Display disk usage
      debug:
        var: disk_usage.stdout_lines
        
    - name: Check memory usage
      shell: free -h
      register: memory_usage
      
    - name: Display memory usage
      debug:
        var: memory_usage.stdout_lines
        
    - name: List running services
      shell: systemctl list-units --type=service --state=running --no-pager
      register: running_services
      
    - name: Display running services
      debug:
        var: running_services.stdout_lines
        
    - name: Create report directory
      file:
        path: /tmp/system_reports
        state: directory
        mode: '0755'
        
    - name: Generate system report
      shell: |
        echo "System Report - $(date)" > /tmp/system_reports/system_info.txt
        echo "===========================================" >> /tmp/system_reports/system_info.txt
        echo "" >> /tmp/system_reports/system_info.txt
        echo "Hostname: $(hostname)" >> /tmp/system_reports/system_info.txt
        echo "OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d= -f2 | tr -d '\"')" >> /tmp/system_reports/system_info.txt
        echo "Kernel: $(uname -r)" >> /tmp/system_reports/system_info.txt
        echo "" >> /tmp/system_reports/system_info.txt
        echo "Disk Usage:" >> /tmp/system_reports/system_info.txt
        df -h >> /tmp/system_reports/system_info.txt
        echo "" >> /tmp/system_reports/system_info.txt
        echo "Memory Usage:" >> /tmp/system_reports/system_info.txt
        free -h >> /tmp/system_reports/system_info.txt
      
    - name: Display report location
      debug:
        msg: "System report saved to /tmp/system_reports/system_info.txt"
"""

        # Check if playbook already exists
        if Playbook.objects.filter(name='System-Info-Report').exists():
            self.stdout.write(
                self.style.WARNING('Playbook "System-Info-Report" already exists. Skipping.')
            )
            return

        # Create playbook
        playbook = Playbook(
            name='System-Info-Report',
            description='Gathers comprehensive system information including disk usage, memory, and running services. Creates a detailed report in /tmp/system_reports/',
            playbook_type='host',
            os_family='redhat'
        )
        
        # Save file content
        filename = f"{playbook.name}.yml"
        playbook.file.save(filename, ContentFile(playbook_content.encode('utf-8')), save=False)
        playbook.save()
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created example playbook: {playbook.name}')
        )
        self.stdout.write(
            self.style.SUCCESS(f'File location: {playbook.file.path}')
        )
