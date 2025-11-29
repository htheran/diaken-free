from django.core.management.base import BaseCommand
from django.db import transaction
from history.models import DeploymentHistory
from snapshots.models import SnapshotHistory
from scheduler.models import ScheduledTask, ScheduledTaskHistory
from notifications.models import NotificationLog


class Command(BaseCommand):
    help = 'Clean all test data before production deployment (keeps configuration)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm deletion of all test data'
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(self.style.WARNING('=' * 80))
            self.stdout.write(self.style.WARNING('PRODUCTION PREPARATION - DATA CLEANUP'))
            self.stdout.write(self.style.WARNING('=' * 80))
            self.stdout.write('')
            self.stdout.write('This command will DELETE the following data:')
            self.stdout.write('')
            
            # Count records
            deployment_count = DeploymentHistory.objects.count()
            snapshot_count = SnapshotHistory.objects.count()
            task_count = ScheduledTask.objects.count()
            history_count = ScheduledTaskHistory.objects.count()
            notification_count = NotificationLog.objects.count()
            
            self.stdout.write(f'  • Deployment History: {deployment_count} records')
            self.stdout.write(f'  • Snapshot History: {snapshot_count} records')
            self.stdout.write(f'  • Scheduled Tasks: {task_count} records')
            self.stdout.write(f'  • Task History: {history_count} records')
            self.stdout.write(f'  • Notifications: {notification_count} records')
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('The following will be PRESERVED:'))
            self.stdout.write('')
            self.stdout.write('  ✓ Hosts (inventory)')
            self.stdout.write('  ✓ Groups')
            self.stdout.write('  ✓ Playbooks')
            self.stdout.write('  ✓ Global Settings')
            self.stdout.write('  ✓ Credentials (vCenter, Windows)')
            self.stdout.write('  ✓ Users and permissions')
            self.stdout.write('')
            self.stdout.write(self.style.ERROR('⚠️  THIS ACTION CANNOT BE UNDONE!'))
            self.stdout.write('')
            self.stdout.write('To proceed, run:')
            self.stdout.write(self.style.WARNING('  python manage.py prepare_production --confirm'))
            self.stdout.write('')
            return

        # Confirmed - proceed with deletion
        self.stdout.write(self.style.WARNING('=' * 80))
        self.stdout.write(self.style.WARNING('CLEANING TEST DATA...'))
        self.stdout.write(self.style.WARNING('=' * 80))
        self.stdout.write('')

        try:
            with transaction.atomic():
                # 1. Delete Deployment History
                deployment_count = DeploymentHistory.objects.count()
                self.stdout.write(f'Deleting {deployment_count} deployment history records...')
                DeploymentHistory.objects.all().delete()
                self.stdout.write(self.style.SUCCESS(f'  ✓ Deleted {deployment_count} deployment history records'))

                # 2. Delete Snapshot History
                snapshot_count = SnapshotHistory.objects.count()
                self.stdout.write(f'Deleting {snapshot_count} snapshot history records...')
                SnapshotHistory.objects.all().delete()
                self.stdout.write(self.style.SUCCESS(f'  ✓ Deleted {snapshot_count} snapshot history records'))

                # 3. Delete Task History (before ScheduledTasks due to FK)
                history_count = ScheduledTaskHistory.objects.count()
                self.stdout.write(f'Deleting {history_count} task history records...')
                ScheduledTaskHistory.objects.all().delete()
                self.stdout.write(self.style.SUCCESS(f'  ✓ Deleted {history_count} task history records'))

                # 4. Delete Scheduled Tasks
                task_count = ScheduledTask.objects.count()
                self.stdout.write(f'Deleting {task_count} scheduled task records...')
                ScheduledTask.objects.all().delete()
                self.stdout.write(self.style.SUCCESS(f'  ✓ Deleted {task_count} scheduled task records'))

                # 5. Delete Notifications
                notification_count = NotificationLog.objects.count()
                self.stdout.write(f'Deleting {notification_count} notification records...')
                NotificationLog.objects.all().delete()
                self.stdout.write(self.style.SUCCESS(f'  ✓ Deleted {notification_count} notification records'))

                self.stdout.write('')
                self.stdout.write(self.style.SUCCESS('=' * 80))
                self.stdout.write(self.style.SUCCESS('✓ PRODUCTION PREPARATION COMPLETE'))
                self.stdout.write(self.style.SUCCESS('=' * 80))
                self.stdout.write('')
                self.stdout.write('Summary:')
                self.stdout.write(f'  • {deployment_count} deployment history records deleted')
                self.stdout.write(f'  • {snapshot_count} snapshot history records deleted')
                self.stdout.write(f'  • {task_count} scheduled tasks deleted')
                self.stdout.write(f'  • {history_count} task history records deleted')
                self.stdout.write(f'  • {notification_count} notifications deleted')
                self.stdout.write('')
                self.stdout.write(self.style.SUCCESS('Configuration preserved:'))
                self.stdout.write('  ✓ Hosts, Groups, Playbooks')
                self.stdout.write('  ✓ Global Settings')
                self.stdout.write('  ✓ Credentials')
                self.stdout.write('  ✓ Users')
                self.stdout.write('')
                self.stdout.write(self.style.SUCCESS('System is ready for production!'))
                self.stdout.write('')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error during cleanup: {e}'))
            raise
