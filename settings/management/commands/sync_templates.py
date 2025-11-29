from django.core.management.base import BaseCommand
from settings.models import AnsibleTemplate
from django.core.files import File
import os
import glob

class Command(BaseCommand):
    help = 'Sync Ansible templates from disk to database'

    def handle(self, *args, **options):
        from django.conf import settings
        import os
        # Template directories
        template_dirs = [
            (os.path.join(settings.BASE_DIR, 'media', 'j2', 'host'), 'host'),
            (os.path.join(settings.BASE_DIR, 'media', 'j2', 'group'), 'group'),
        ]
        
        synced_count = 0
        
        for template_dir, template_type in template_dirs:
            if not os.path.exists(template_dir):
                self.stdout.write(self.style.WARNING(f'Directory not found: {template_dir}'))
                continue
            
            # Find all .j2 files
            j2_files = glob.glob(os.path.join(template_dir, '*.j2'))
            
            for file_path in j2_files:
                filename = os.path.basename(file_path)
                name = filename.replace('.j2', '')
                
                # Check if template already exists
                existing = AnsibleTemplate.objects.filter(name=name, template_type=template_type).first()
                
                if existing:
                    self.stdout.write(f'  Exists: {name} ({template_type})')
                else:
                    # Create new template
                    template = AnsibleTemplate(
                        name=name,
                        template_type=template_type,
                        description=f'Template for {name}'
                    )
                    
                    # Open and attach the file
                    with open(file_path, 'rb') as f:
                        template.file.save(filename, File(f), save=True)
                    
                    self.stdout.write(self.style.SUCCESS(f'✓ Created: {name} ({template_type})'))
                    synced_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'\nSynced {synced_count} templates'))
