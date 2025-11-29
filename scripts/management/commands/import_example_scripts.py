from django.core.management.base import BaseCommand
from scripts.models import Script
import os


class Command(BaseCommand):
    help = 'Import example scripts into the database'

    def handle(self, *args, **options):
        scripts_to_import = [
            {
                'name': 'system_info',
                'description': 'Collect comprehensive system information including OS, CPU, memory, disk, network, and services',
                'target_type': 'host',
                'os_family': 'redhat',
            },
            {
                'name': 'system_info',
                'description': 'Collect comprehensive system information including OS, CPU, memory, disk, network, and services',
                'target_type': 'host',
                'os_family': 'debian',
            },
            {
                'name': 'system_info',
                'description': 'Collect comprehensive system information including OS, CPU, memory, disk, network, and services',
                'target_type': 'host',
                'os_family': 'windows',
            },
        ]

        imported = 0
        skipped = 0

        for script_data in scripts_to_import:
            # Check if script already exists
            exists = Script.objects.filter(
                name=script_data['name'],
                target_type=script_data['target_type'],
                os_family=script_data['os_family']
            ).exists()

            if exists:
                self.stdout.write(
                    self.style.WARNING(
                        f"Script '{script_data['name']}' ({script_data['os_family']}/{script_data['target_type']}) already exists, skipping..."
                    )
                )
                skipped += 1
                continue

            # Create script object
            script = Script(**script_data)
            
            # Check if file exists
            if os.path.exists(script.get_full_path()):
                script.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ Imported: {script.name} ({script.get_os_family_display()}/{script.get_target_type_display()})"
                    )
                )
                imported += 1
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"✗ File not found: {script.get_full_path()}"
                    )
                )
                skipped += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\n{'='*60}\nImport Summary:\n{'='*60}"
            )
        )
        self.stdout.write(f"Imported: {imported}")
        self.stdout.write(f"Skipped: {skipped}")
        self.stdout.write(f"Total: {imported + skipped}")
