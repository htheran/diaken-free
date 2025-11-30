"""
Django management command to initialize default global settings

This ensures that critical system settings exist in the database.

Usage:
    python manage.py init_default_settings
"""

from django.core.management.base import BaseCommand
from settings.models import SettingSection, GlobalSetting


class Command(BaseCommand):
    help = 'Initialize default global settings'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING(
            '\n' + '='*70 + '\n'
            'Initialize Default Global Settings\n'
            '='*70 + '\n'
        ))
        
        stats = {
            'sections_created': 0,
            'sections_existing': 0,
            'settings_created': 0,
            'settings_existing': 0
        }
        
        # Define default sections and settings
        # NOTA: Solo se crean variables mínimas del sistema
        # Las variables de deployment (vCenter, credenciales, etc.)
        # deben ser configuradas por el usuario vía interfaz web
        default_config = {
            'System': {
                'description': 'System configuration settings',
                'settings': [
                    {
                        'key': 'timezone',
                        'value': 'America/Bogota',
                        'description': 'System timezone',
                        'order': 1
                    },
                    {
                        'key': 'date_format',
                        'value': 'Y-m-d H:i:s',
                        'description': 'Default date format',
                        'order': 2
                    },
                    {
                        'key': 'language',
                        'value': 'en',
                        'description': 'System language (en/es)',
                        'order': 3
                    }
                ]
            },
            'Deployment': {
                'description': 'Deployment settings - Configure via web interface',
                'settings': []  # User must configure: vcenter_host, vcenter_user, etc.
            }
        }
        
        # Create sections and settings
        for section_name, section_data in default_config.items():
            # Create or get section
            section, created = SettingSection.objects.get_or_create(
                name=section_name,
                defaults={'description': section_data['description']}
            )
            
            if created:
                stats['sections_created'] += 1
                self.stdout.write(self.style.SUCCESS(
                    f'  ✓ Created section: {section_name}'
                ))
            else:
                stats['sections_existing'] += 1
                self.stdout.write(self.style.WARNING(
                    f'  ℹ Section already exists: {section_name}'
                ))
            
            # Create settings for this section
            for setting_data in section_data['settings']:
                setting, created = GlobalSetting.objects.get_or_create(
                    key=setting_data['key'],
                    defaults={
                        'section': section,
                        'value': setting_data['value'],
                        'description': setting_data['description'],
                        'order': setting_data['order']
                    }
                )
                
                if created:
                    stats['settings_created'] += 1
                    self.stdout.write(self.style.SUCCESS(
                        f'    ✓ Created: {setting_data["key"]} = {setting_data["value"]}'
                    ))
                else:
                    stats['settings_existing'] += 1
                    self.stdout.write(self.style.WARNING(
                        f'    ℹ Already exists: {setting_data["key"]} = {setting.value}'
                    ))
        
        # Summary
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('Summary:'))
        self.stdout.write(f'  Sections created: {stats["sections_created"]}')
        self.stdout.write(f'  Sections existing: {stats["sections_existing"]}')
        self.stdout.write(f'  Settings created: {stats["settings_created"]}')
        self.stdout.write(f'  Settings existing: {stats["settings_existing"]}')
        self.stdout.write('='*70 + '\n')
        
        if stats['sections_created'] > 0 or stats['settings_created'] > 0:
            self.stdout.write(self.style.SUCCESS(
                '✓ Default settings initialized successfully'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                '✓ All default settings already exist'
            ))
