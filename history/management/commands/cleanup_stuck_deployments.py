from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from history.models import DeploymentHistory
from scheduler.models import ScheduledTaskHistory


class Command(BaseCommand):
    help = 'Clean up stuck deployments and scheduled tasks that have been running for too long'

    def add_arguments(self, parser):
        parser.add_argument(
            '--timeout-hours',
            type=int,
            default=6,
            help='Number of hours after which a running deployment is considered stuck (default: 6)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually doing it'
        )

    def handle(self, *args, **options):
        timeout_hours = options['timeout_hours']
        dry_run = options['dry_run']
        
        # Calculate cutoff time
        cutoff_time = timezone.now() - timedelta(hours=timeout_hours)
        
        self.stdout.write(self.style.WARNING(
            f'\n{"=" * 70}'
        ))
        self.stdout.write(self.style.WARNING(
            f'Cleaning up deployments running for more than {timeout_hours} hours'
        ))
        self.stdout.write(self.style.WARNING(
            f'Cutoff time: {cutoff_time}'
        ))
        self.stdout.write(self.style.WARNING(
            f'Current time: {timezone.now()}'
        ))
        self.stdout.write(self.style.WARNING(
            f'{"=" * 70}\n'
        ))
        
        # Find stuck deployments
        stuck_deployments = DeploymentHistory.objects.filter(
            status='running',
            created_at__lt=cutoff_time
        ).order_by('created_at')
        
        deployment_count = stuck_deployments.count()
        
        if deployment_count == 0:
            self.stdout.write(self.style.SUCCESS(
                '✓ No stuck deployments found'
            ))
        else:
            self.stdout.write(self.style.WARNING(
                f'Found {deployment_count} stuck deployment(s):\n'
            ))
            
            for dep in stuck_deployments:
                running_time = timezone.now() - dep.created_at
                hours = running_time.total_seconds() / 3600
                
                self.stdout.write(
                    f'  • ID {dep.id}: {dep.target} - {dep.playbook}'
                )
                self.stdout.write(
                    f'    Started: {dep.created_at}'
                )
                self.stdout.write(
                    f'    Running for: {hours:.1f} hours\n'
                )
                
                if not dry_run:
                    dep.status = 'failed'
                    dep.completed_at = timezone.now()
                    if not dep.ansible_output:
                        dep.ansible_output = f'Deployment automatically marked as failed after running for {hours:.1f} hours (timeout: {timeout_hours}h)'
                    else:
                        dep.ansible_output += f'\n\n[SYSTEM] Deployment automatically marked as failed after running for {hours:.1f} hours (timeout: {timeout_hours}h)'
                    dep.save()
            
            if dry_run:
                self.stdout.write(self.style.WARNING(
                    f'\n[DRY RUN] Would have marked {deployment_count} deployment(s) as failed'
                ))
            else:
                self.stdout.write(self.style.SUCCESS(
                    f'\n✓ Marked {deployment_count} deployment(s) as failed'
                ))
        
        # Find stuck scheduled tasks
        stuck_tasks = ScheduledTaskHistory.objects.filter(
            status='running',
            executed_at__lt=cutoff_time
        ).order_by('executed_at')
        
        task_count = stuck_tasks.count()
        
        if task_count == 0:
            self.stdout.write(self.style.SUCCESS(
                '✓ No stuck scheduled tasks found'
            ))
        else:
            self.stdout.write(self.style.WARNING(
                f'\nFound {task_count} stuck scheduled task(s):\n'
            ))
            
            for task in stuck_tasks:
                running_time = timezone.now() - task.executed_at
                hours = running_time.total_seconds() / 3600
                
                self.stdout.write(
                    f'  • ID {task.id}: {task.target_name} - {task.playbook_name}'
                )
                self.stdout.write(
                    f'    Started: {task.executed_at}'
                )
                self.stdout.write(
                    f'    Running for: {hours:.1f} hours\n'
                )
                
                if not dry_run:
                    task.status = 'failed'
                    task.completed_at = timezone.now()
                    if not task.ansible_output:
                        task.ansible_output = f'Task automatically marked as failed after running for {hours:.1f} hours (timeout: {timeout_hours}h)'
                    else:
                        task.ansible_output += f'\n\n[SYSTEM] Task automatically marked as failed after running for {hours:.1f} hours (timeout: {timeout_hours}h)'
                    task.save()
            
            if dry_run:
                self.stdout.write(self.style.WARNING(
                    f'\n[DRY RUN] Would have marked {task_count} task(s) as failed'
                ))
            else:
                self.stdout.write(self.style.SUCCESS(
                    f'\n✓ Marked {task_count} task(s) as failed'
                ))
        
        # Summary
        total = deployment_count + task_count
        if total > 0:
            self.stdout.write(self.style.WARNING(
                f'\n{"=" * 70}'
            ))
            if dry_run:
                self.stdout.write(self.style.WARNING(
                    f'[DRY RUN] Would have cleaned up {total} stuck item(s)'
                ))
            else:
                self.stdout.write(self.style.SUCCESS(
                    f'✓ Successfully cleaned up {total} stuck item(s)'
                ))
            self.stdout.write(self.style.WARNING(
                f'{"=" * 70}\n'
            ))
