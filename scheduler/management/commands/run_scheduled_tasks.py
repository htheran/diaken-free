from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
from scheduler.models import ScheduledTask, ScheduledTaskHistory
from inventory.models import Host
from settings.models import DeploymentCredential, GlobalSetting, WindowsCredential, VCenterCredential
import subprocess
import tempfile
import json
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Execute scheduled tasks that are due'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--daemon',
            action='store_true',
            help='Run in daemon mode (continuous loop)'
        )
        parser.add_argument(
            '--interval',
            type=int,
            default=10,
            help='Interval in seconds between checks in daemon mode (default: 10)'
        )

    def handle(self, *args, **options):
        daemon_mode = options.get('daemon', False)
        interval = options.get('interval', 10)
        
        if daemon_mode:
            self.stdout.write(self.style.SUCCESS(f'Starting scheduler in daemon mode (checking every {interval}s)'))
            import time
            while True:
                self.check_and_execute_tasks()
                time.sleep(interval)
        else:
            self.check_and_execute_tasks()
    
    def check_and_execute_tasks(self):
        """Check for due tasks and execute them"""
        now = timezone.now()
        
        # STEP 1: Create snapshots for tasks that need them (1 minute before execution)
        from datetime import timedelta
        snapshot_window = now + timedelta(minutes=1)
        
        tasks_needing_snapshot = ScheduledTask.objects.filter(
            status='pending',
            create_snapshot=True,
            snapshot_created=False,
            scheduled_datetime__lte=snapshot_window,
            scheduled_datetime__gt=now  # Not yet due for execution
        )
        
        for task in tasks_needing_snapshot:
            self.stdout.write(f'Creating snapshot for task: {task.name} (ID: {task.id}) - Scheduled for {task.scheduled_datetime}')
            self.create_snapshot_for_task(task)
        
        # STEP 2: Get all pending tasks that are due for execution
        due_tasks = ScheduledTask.objects.filter(
            status='pending',
            scheduled_datetime__lte=now
        )
        
        if not due_tasks.exists():
            if not tasks_needing_snapshot.exists():
                self.stdout.write(self.style.SUCCESS(f'[{now}] No tasks due for execution'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'[{now}] Found {due_tasks.count()} task(s) to execute'))
        
        for task in due_tasks:
            self.stdout.write(f'Executing task: {task.name} (ID: {task.id})')
            self.execute_task(task)
        
        # Cleanup expired snapshots automatically
        self.cleanup_expired_snapshots()
    
    def execute_task(self, task):
        """Execute a scheduled task"""
        from django.db import transaction
        
        start_time = timezone.now()
        
        # Use atomic transaction to prevent race conditions
        # Multiple cron jobs could try to execute the same task
        with transaction.atomic():
            # Lock the task row and re-fetch to get latest status
            task = ScheduledTask.objects.select_for_update().get(id=task.id)
            
            # Check if task is still pending (not already being executed)
            if task.status != 'pending':
                logger.warning(f'Task {task.name} (ID: {task.id}) is already {task.status}, skipping execution')
                return
            
            # Update task status to running
            task.status = 'running'
            task.execution_started_at = start_time
            task.save()
        
        # Small delay to allow UI to show running state
        import time
        time.sleep(2)
        
        try:
            if task.task_type == 'host':
                result = self.execute_host_task(task)
            elif task.task_type == 'group':
                result = self.execute_group_task(task)
            else:
                raise Exception(f'Unknown task type: {task.task_type}')
            
            # Calculate duration
            end_time = timezone.now()
            duration = int((end_time - start_time).total_seconds())
            
            # For async tasks (Celery), history is created by the task itself
            # Only create history for synchronous tasks (scripts)
            history = None
            if result.get('async', False):
                # Async task - history already created in execute_linux_host_task/execute_windows_host_task
                # Just update task status
                task.status = 'completed'
                task.execution_completed_at = end_time
                task.scheduled_task_history_id = result.get('history_id')
                task.save()
                logger.info(f'[SCHEDULED-TASK] Async task dispatched, history_id: {result.get("history_id")}')
                
                # Get history for notification (Celery will update it later)
                try:
                    history = ScheduledTaskHistory.objects.get(id=result.get('history_id'))
                except:
                    pass
            else:
                # Synchronous task - create history record here
                # Get execution name (playbook or script)
                if task.execution_type == 'script' and task.script:
                    execution_name = task.script.name
                else:
                    execution_name = task.playbook.name if task.playbook else 'Unknown'
                
                # Create history record
                history = ScheduledTaskHistory.objects.create(
                    scheduled_task=task,
                    scheduled_for=task.scheduled_datetime,
                    status='success' if result['success'] else 'failed',
                    task_type=task.task_type,
                    target_name=result['target_name'],
                    target_ip=result['target_ip'],
                    playbook_name=execution_name,
                    environment_name=task.environment.name if task.environment else '',
                    ansible_output=result['output'],
                    error_message=result.get('error', ''),
                    execution_duration=duration
                )
                
                # Update task status
                task.status = 'completed'
                task.execution_completed_at = end_time
                task.scheduled_task_history_id = history.id
                task.save()
            
            # Send notification (only for sync tasks, async tasks send their own)
            if history and not result.get('async', False):
                try:
                    from notifications.utils import send_scheduled_task_notification
                    send_scheduled_task_notification(history, task)
                except Exception as notif_error:
                    logger.warning(f'Failed to send notification: {notif_error}')
            
            self.stdout.write(self.style.SUCCESS(f'✓ Task completed: {task.name}'))
            
        except Exception as e:
            logger.error(f'Error executing task {task.id}: {e}')
            
            # Create failed history record
            end_time = timezone.now()
            duration = int((end_time - start_time).total_seconds())
            
            # Get execution name (playbook or script)
            if task.execution_type == 'script' and task.script:
                try:
                    execution_name = task.script.name
                except:
                    execution_name = 'Unknown Script'
            else:
                execution_name = task.playbook.name if task.playbook else 'Unknown'
            
            history = ScheduledTaskHistory.objects.create(
                scheduled_task=task,
                scheduled_for=task.scheduled_datetime,
                status='failed',
                task_type=task.task_type,
                target_name=task.host.name if task.host else (task.group.name if task.group else 'Unknown'),
                target_ip=task.host.ip if task.host else '',
                playbook_name=execution_name,
                environment_name=task.environment.name if task.environment else '',
                ansible_output='',
                error_message=str(e),
                execution_duration=duration
            )
            
            # Update task status
            task.status = 'failed'
            task.execution_completed_at = end_time
            task.error_message = str(e)
            task.scheduled_task_history_id = history.id
            task.save()
            
            # Send notification for failure
            try:
                from notifications.utils import send_scheduled_task_notification
                send_scheduled_task_notification(history, task)
            except Exception as notif_error:
                logger.warning(f'Failed to send notification: {notif_error}')
            
            self.stdout.write(self.style.ERROR(f'✗ Task failed: {task.name} - {str(e)}'))
    
    def create_snapshot_for_task(self, task):
        """Create snapshot(s) for a task 1 minute before execution"""
        try:
            if task.task_type == 'host':
                # Single host snapshot
                host = task.host
                execution_item = task.playbook if task.execution_type == 'playbook' else task.script
                snapshot_name, snapshot_info = self.create_host_snapshot(host, execution_item, task)
                
                if snapshot_name:
                    task.snapshot_created = True
                    task.snapshot_name = snapshot_name
                    task.save()
                    logger.info(f'[PRE-SNAPSHOT] Created snapshot for task {task.id}: {snapshot_name}')
                    self.stdout.write(self.style.SUCCESS(f'✓ Snapshot created: {snapshot_name}'))
                else:
                    logger.error(f'[PRE-SNAPSHOT] Failed to create snapshot for task {task.id}: {snapshot_info}')
                    
            elif task.task_type == 'group':
                # Multiple host snapshots
                group = task.group
                hosts = Host.objects.filter(group=group, active=True)
                execution_item = task.playbook
                snapshot_names = []
                
                for host in hosts:
                    snapshot_name, snapshot_info = self.create_host_snapshot(host, execution_item, task)
                    if snapshot_name:
                        snapshot_names.append(f"{host.name}: {snapshot_name}")
                        logger.info(f'[PRE-SNAPSHOT] Created snapshot for {host.name}: {snapshot_name}')
                    else:
                        logger.error(f'[PRE-SNAPSHOT] Failed to create snapshot for {host.name}: {snapshot_info}')
                
                if snapshot_names:
                    task.snapshot_created = True
                    task.snapshot_name = '|||'.join(snapshot_names)  # Store all snapshot names separated
                    task.save()
                    self.stdout.write(self.style.SUCCESS(f'✓ Created {len(snapshot_names)} snapshots for group {group.name}'))
                    
        except Exception as e:
            logger.error(f'[PRE-SNAPSHOT] Error creating snapshot for task {task.id}: {e}')
            self.stdout.write(self.style.ERROR(f'✗ Failed to create snapshot: {str(e)}'))
    
    def execute_host_task(self, task):
        """Execute playbook or script on a single host (supports both Linux and Windows)"""
        host = task.host
        playbook = task.playbook
        script = task.script
        
        # Use snapshot if it was already created (1 minute before)
        snapshot_name = task.snapshot_name if task.snapshot_created else None
        snapshot_info = f"Using pre-created snapshot: {snapshot_name}" if snapshot_name else "No snapshot"
        
        # If snapshot was requested but not created yet (shouldn't happen with new logic)
        if task.create_snapshot and not task.snapshot_created:
            logger.warning(f'Snapshot was requested but not created beforehand for task {task.id}. Creating now...')
            execution_item = playbook if task.execution_type == 'playbook' else script
            snapshot_name, snapshot_info = self.create_host_snapshot(host, execution_item, task)
            logger.info(snapshot_info)
        
        # Check execution type
        if task.execution_type == 'script':
            # Script execution
            if task.os_family == 'windows':
                logger.info(f'[Scheduler] Executing PowerShell script on {host.name}')
                result = self.execute_windows_script_on_host(task, host)
            else:
                logger.info(f'[Scheduler] Executing bash script on {host.name} (OS: {task.os_family})')
                result = self.execute_script_on_host(task, host)
        else:
            # Playbook execution
            # Detect host OS and create appropriate inventory
            if host.operating_system == 'windows':
                # Windows host - use WinRM
                logger.info(f'[Scheduler] Executing Windows playbook on {host.name}')
                result = self.execute_windows_host_task(task, host, playbook)
            else:
                # Linux host - use SSH
                logger.info(f'[Scheduler] Executing Linux playbook on {host.name}')
                result = self.execute_linux_host_task(task, host, playbook)
        
        # Add snapshot name to result
        result['snapshot_name'] = snapshot_name
        return result
    
    def execute_linux_host_task(self, task, host, playbook):
        """Execute playbook on a Linux host using SSH via Celery"""
        from deploy.tasks import execute_playbook_async
        from scheduler.models import ScheduledTaskHistory
        
        # Get SSH credentials
        ssh_cred = DeploymentCredential.objects.first()
        if not ssh_cred:
            raise Exception('No SSH credentials configured')
        
        # Create inventory with Python interpreter
        python_interp = host.ansible_python_interpreter if host.ansible_python_interpreter else '/usr/bin/python3'
        inventory_content = f"""[target_host]
{host.ip} ansible_user={ssh_cred.user} ansible_ssh_private_key_file={ssh_cred.ssh_key_file_path} ansible_ssh_common_args='-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null' ansible_python_interpreter={python_interp}
"""
        
        # Get global settings
        global_settings = GlobalSetting.objects.all()
        extra_vars = {
            'hostname': host.name,
            'ip': host.ip,
            'inventory_hostname': host.name,
            'target_host': host.ip  # For playbooks that use target_host variable
        }
        for setting in global_settings:
            extra_vars[setting.key] = setting.value
        
        # Add log_dir alias
        if 'log_dir_update' in extra_vars and 'log_dir' not in extra_vars:
            extra_vars['log_dir'] = extra_vars['log_dir_update']
        
        extra_vars_json = json.dumps(extra_vars)
        
        # Create ScheduledTaskHistory record (NOT DeploymentHistory)
        scheduled_history = ScheduledTaskHistory.objects.create(
            scheduled_task=task,
            scheduled_for=task.scheduled_datetime,
            status='running',
            task_type='host',
            target_name=host.name,
            target_ip=host.ip,
            playbook_name=playbook.name,
            environment_name=task.environment.name if task.environment else 'N/A'
        )
        
        # Dispatch to Celery with scheduled_task_history_id
        celery_task = execute_playbook_async.delay(
            history_id=scheduled_history.id,  # Pass scheduled history ID
            inventory_content=inventory_content,
            execution_file=playbook.file.path,
            extra_vars_json=extra_vars_json,
            ansible_user=ssh_cred.user,
            ssh_key_path=ssh_cred.ssh_key_file_path,
            scheduled_task_history_id=scheduled_history.id  # Pass as scheduled task
        )
        
        logger.info(f'[SCHEDULED-TASK] Dispatched to Celery: task_id={celery_task.id}, scheduled_history_id={scheduled_history.id}')
        
        # Return immediately (async execution)
        return {
            'success': True,
            'target_name': host.name,
            'target_ip': host.ip,
            'output': f'Task dispatched to Celery (task_id: {celery_task.id})',
            'async': True,
            'celery_task_id': celery_task.id,
            'history_id': scheduled_history.id
        }
    
    def execute_script_on_host(self, task, host):
        """Execute script on a Linux host using SSH"""
        # Get script
        if not task.script:
            raise Exception('No script associated with this task')
        script = task.script
        
        # Get SSH credentials
        ssh_cred = host.deployment_credential if host.deployment_credential else DeploymentCredential.objects.first()
        if not ssh_cred:
            raise Exception('No SSH credentials configured')
        
        # Get SSH user and key
        ansible_user = host.ansible_user if host.ansible_user else ssh_cred.user
        ssh_key_path = host.ansible_ssh_private_key_file if host.ansible_ssh_private_key_file else ssh_cred.ssh_key_file_path
        
        logger.info(f'[SCRIPT-SCHEDULER] Executing script: {script.name}')
        logger.info(f'[SCRIPT-SCHEDULER] Target host: {host.ip}')
        logger.info(f'[SCRIPT-SCHEDULER] Using user: {ansible_user}')
        
        # Check if ssh command is available
        import shutil
        ssh_path = shutil.which('ssh')
        if not ssh_path:
            # Try common paths
            for path in ['/usr/bin/ssh', '/bin/ssh']:
                if os.path.exists(path):
                    ssh_path = path
                    break
        
        if not ssh_path:
            error_msg = 'ssh command not found. Install openssh-clients package: sudo dnf install -y openssh-clients'
            logger.error(f'[SCRIPT-SCHEDULER] {error_msg}')
            raise Exception(error_msg)
        
        # Execute script via SSH
        cmd = [
            ssh_path,
            '-i', ssh_key_path,
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            f'{ansible_user}@{host.ip}',
            'bash -s'
        ]
        
        # Read script content
        with open(script.file_path, 'r') as f:
            script_content = f.read()
        
        try:
            result = subprocess.run(
                cmd,
                input=script_content,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout
            )
            
            # Format output
            full_output = f"Script: {script.name}\n"
            full_output += f"Target: {host.name} ({host.ip})\n"
            full_output += f"OS Family: {task.os_family}\n"
            full_output += "="*60 + "\n\n"
            full_output += "STDOUT:\n" + result.stdout + "\n\n"
            if result.stderr:
                full_output += "STDERR:\n" + result.stderr + "\n"
            full_output += "\n" + "="*60 + "\n"
            full_output += f"Exit Code: {result.returncode}\n"
            
            is_success = (result.returncode == 0)
            
            return {
                'success': is_success,
                'output': full_output,
                'target_name': host.name,
                'target_ip': host.ip,
                'error': '' if is_success else f'Script execution failed with exit code {result.returncode}'
            }
            
        except subprocess.TimeoutExpired:
            raise Exception('Script execution timed out after 10 minutes')
    
    def execute_windows_script_on_host(self, task, host):
        """Execute PowerShell script on a Windows host using WinRM"""
        # Get script
        if not task.script:
            raise Exception('No script associated with this task')
        script = task.script
        
        # Get Windows credentials - prioritize direct fields over credential object
        if host.windows_user and host.windows_password:
            windows_user = host.windows_user
            windows_password = host.windows_password
            windows_auth_type = 'ntlm'
            windows_port = 5985
        elif host.windows_credential:
            windows_user = host.windows_credential.username
            windows_password = host.windows_credential.password
            windows_auth_type = host.windows_credential.auth_type
            windows_port = host.windows_credential.get_port()
        else:
            raise Exception(f'No Windows credentials configured for host {host.name}')
        
        logger.info(f'[SCRIPT-SCHEDULER-WIN] Executing script: {script.name}')
        logger.info(f'[SCRIPT-SCHEDULER-WIN] Target host: {host.ip}')
        logger.info(f'[SCRIPT-SCHEDULER-WIN] Using user: {windows_user}')
        
        # Create temporary inventory for WinRM
        inventory_content = f'''[windows_hosts]
{host.ip}

[windows_hosts:vars]
ansible_user={windows_user}
ansible_password={windows_password}
ansible_connection=winrm
ansible_winrm_transport={windows_auth_type}
ansible_winrm_server_cert_validation=ignore
ansible_port={windows_port}
ansible_winrm_read_timeout_sec=60
ansible_winrm_operation_timeout_sec=50
'''
        
        inventory_path = f'/tmp/ansible_inventory_script_win_{task.id}.ini'
        with open(inventory_path, 'w') as f:
            f.write(inventory_content)
        
        # Create temporary playbook to execute the script
        playbook_content = f'''---
- name: Execute PowerShell Script
  hosts: windows_hosts
  gather_facts: no
  tasks:
    - name: Execute {script.name}
      win_shell: |
'''
        
        # Read script content and indent it
        with open(script.file_path, 'r') as f:
            script_lines = f.readlines()
            for line in script_lines:
                playbook_content += f'        {line}'
        
        playbook_content += '''
      register: script_output
    
    - name: Display output
      debug:
        var: script_output
'''
        
        playbook_path = f'/tmp/ansible_playbook_script_win_{task.id}.yml'
        with open(playbook_path, 'w') as f:
            f.write(playbook_content)
        
        try:
            # Execute playbook
            cmd = [
                settings.ANSIBLE_PLAYBOOK_PATH,
                '-vv',
                '-i', inventory_path,
                playbook_path,
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout
            )
            
            # Format output
            full_output = f"Script: {script.name}\n"
            full_output += f"Target: {host.name} ({host.ip})\n"
            full_output += f"OS Family: Windows\n"
            full_output += "="*60 + "\n\n"
            full_output += result.stdout + "\n"
            if result.stderr:
                full_output += "\nSTDERR:\n" + result.stderr + "\n"
            full_output += "\n" + "="*60 + "\n"
            
            # Check for success in Ansible output
            is_success = self.check_ansible_success(full_output, result.returncode)
            
            return {
                'success': is_success,
                'output': full_output,
                'target_name': host.name,
                'target_ip': host.ip,
                'error': '' if is_success else f'Script execution failed'
            }
            
        except subprocess.TimeoutExpired:
            raise Exception('Script execution timed out after 10 minutes')
        finally:
            # Clean up temporary files
            try:
                os.remove(inventory_path)
                os.remove(playbook_path)
            except:
                pass
    
    def execute_windows_host_task(self, task, host, playbook):
        """Execute playbook on a Windows host using WinRM via Celery"""
        from deploy.tasks import execute_windows_playbook_async
        from scheduler.models import ScheduledTaskHistory
        
        # Get Windows credentials
        windows_cred = host.windows_credential
        if not windows_cred:
            raise Exception(f'No Windows credentials configured for host {host.name}')
        
        # Create Windows inventory with WinRM settings
        inventory_content = f'''[windows_hosts]
{host.ip}

[windows_hosts:vars]
ansible_user={windows_cred.username}
ansible_password={windows_cred.get_password()}
ansible_connection=winrm
ansible_winrm_transport={windows_cred.auth_type}
ansible_winrm_server_cert_validation=ignore
ansible_port={windows_cred.get_port()}
ansible_winrm_read_timeout_sec=60
ansible_winrm_operation_timeout_sec=50
'''
        
        logger.info(f'[Scheduler-Windows] Creating ScheduledTaskHistory record for {host.name}')
        
        # Create ScheduledTaskHistory record (NOT DeploymentHistory)
        scheduled_history = ScheduledTaskHistory.objects.create(
            scheduled_task=task,
            scheduled_for=task.scheduled_datetime,
            status='running',
            task_type='host',
            target_name=host.name,
            target_ip=host.ip,
            playbook_name=playbook.name,
            environment_name=task.environment.name if task.environment else 'N/A'
        )
        
        # Dispatch to Celery with scheduled_task_history_id
        celery_task = execute_windows_playbook_async.delay(
            history_id=scheduled_history.id,  # Pass scheduled history ID
            inventory_content=inventory_content,
            execution_file=playbook.file.path,
            windows_user=windows_cred.username,
            windows_password=windows_cred.get_password(),
            auth_type=windows_cred.auth_type,
            port=windows_cred.get_port(),
            scheduled_task_history_id=scheduled_history.id  # Pass as scheduled task
        )
        
        logger.info(f'[SCHEDULED-TASK-WINDOWS] Dispatched to Celery: task_id={celery_task.id}, scheduled_history_id={scheduled_history.id}')
        
        # Return immediately (async execution)
        return {
            'success': True,
            'target_name': host.name,
            'target_ip': host.ip,
            'output': f'Windows task dispatched to Celery (task_id: {celery_task.id})',
            'async': True,
            'celery_task_id': celery_task.id,
            'history_id': scheduled_history.id
        }
    
    def execute_group_task(self, task):
        """Execute playbook on all hosts in a group"""
        group = task.group
        playbook = task.playbook
        
        # Get all active hosts in the group
        hosts = Host.objects.filter(group=group, active=True)
        
        if not hosts.exists():
            raise Exception(f'No active hosts found in group {group.name}')
        
        # Use snapshots if they were already created (1 minute before)
        snapshot_names = []
        if task.snapshot_created and task.snapshot_name:
            # Snapshots were already created, parse the names
            snapshot_names = task.snapshot_name.split('|||') if task.snapshot_name else []
            logger.info(f'Using pre-created snapshots for group {group.name}: {len(snapshot_names)} snapshots')
        elif task.create_snapshot and not task.snapshot_created:
            # Shouldn't happen with new logic, but create them now as fallback
            logger.warning(f'Snapshots were requested but not created beforehand for task {task.id}. Creating now...')
            for host in hosts:
                snapshot_name, snapshot_info = self.create_host_snapshot(host, playbook, task)
                if snapshot_name:
                    snapshot_names.append(f"{host.name}: {snapshot_name}")
                logger.info(snapshot_info)
        
        # Get SSH credentials
        ssh_cred = DeploymentCredential.objects.first()
        if not ssh_cred:
            raise Exception('No SSH credentials configured')
        
        # Create inventory
        inventory_lines = ['[target_group]']
        
        for host in hosts:
            inventory_vars = [
                f"ansible_host={host.ip}",
                f"ansible_user={ssh_cred.user}",
                f"ansible_ssh_private_key_file={ssh_cred.ssh_key_file_path}",
                "ansible_ssh_common_args='-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'"
            ]
            
            if host.ansible_python_interpreter:
                inventory_vars.append(f"ansible_python_interpreter={host.ansible_python_interpreter}")
            
            inventory_lines.append(f"{host.name} {' '.join(inventory_vars)}")
        
        # Add group variables
        inventory_lines.append('')
        inventory_lines.append('[target_group:vars]')
        inventory_lines.append(f'group_name={group.name}')
        inventory_lines.append(f'target_environment={group.environment.name if group.environment else ""}')
        
        inventory_content = '\n'.join(inventory_lines)
        inventory_path = f'/tmp/ansible_inventory_scheduled_{task.id}.ini'
        
        with open(inventory_path, 'w') as f:
            f.write(inventory_content)
        
        # Get global settings
        global_settings = GlobalSetting.objects.all()
        extra_vars = {
            'group_name': group.name,
            'target_environment': group.environment.name if group.environment else '',
            'host_count': hosts.count()
        }
        for setting in global_settings:
            extra_vars[setting.key] = setting.value
        
        # Add log_dir alias
        if 'log_dir_update' in extra_vars and 'log_dir' not in extra_vars:
            extra_vars['log_dir'] = extra_vars['log_dir_update']
        
        extra_vars_json = json.dumps(extra_vars)
        
        # Execute playbook
        cmd = [
            settings.ANSIBLE_PLAYBOOK_PATH,
            '-i', inventory_path,
            playbook.file.path,
            '--extra-vars', extra_vars_json,
            '-v'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        # Clean up
        try:
            os.remove(inventory_path)
        except:
            pass
        
        # Determine success
        full_output = result.stdout + '\n' + result.stderr
        is_success = self.check_ansible_success(full_output, result.returncode)
        
        # Get IPs for history
        host_ips = ', '.join([h.ip for h in hosts[:3]])
        if hosts.count() > 3:
            host_ips += '...'
        
        return {
            'success': is_success,
            'output': full_output,
            'target_name': f'{group.name} ({hosts.count()} hosts)',
            'target_ip': host_ips,
            'error': '' if is_success else 'Playbook execution failed',
            'snapshot_names': ', '.join(snapshot_names) if snapshot_names else None
        }
    
    def check_ansible_success(self, output, returncode):
        """Check if Ansible playbook succeeded"""
        if 'PLAY RECAP' in output:
            import re
            failed_match = re.findall(r'failed=(\d+)', output)
            unreachable_match = re.findall(r'unreachable=(\d+)', output)
            
            total_failed = sum(int(x) for x in failed_match)
            total_unreachable = sum(int(x) for x in unreachable_match)
            
            return (total_failed == 0 and total_unreachable == 0)
        else:
            return (returncode == 0)
    
    def create_host_snapshot(self, host, execution_item, task=None):
        """Create snapshot for a host before playbook/script execution and save to SnapshotHistory
        
        Args:
            host: Host object
            execution_item: Playbook or Script object
            task: ScheduledTask object (optional, for getting user info)
        """
        from deploy.vcenter_snapshot import get_vcenter_connection, create_snapshot, Disconnect
        from settings.models import VCenterCredential
        from snapshots.models import SnapshotHistory
        
        if not host.vcenter_server:
            return None, f"Warning: No vCenter server configured for {host.name}"
        
        try:
            # Get vCenter credentials
            vcenter_cred = VCenterCredential.objects.filter(host=host.vcenter_server).first()
            
            if not vcenter_cred:
                return None, f"vCenter credential not found for {host.vcenter_server}"
            
            # Create snapshot name with local time
            local_time = timezone.localtime(timezone.now())
            execution_name = execution_item.name if execution_item else 'Unknown'
            snapshot_name = f"Before executing {execution_name} - {local_time.strftime('%Y-%m-%d %H:%M:%S')}"
            
            logger.info(f"Creating snapshot for {host.name} ({host.ip})")
            
            si = get_vcenter_connection(
                host.vcenter_server,
                vcenter_cred.user,
                vcenter_cred.get_password()  # Use decrypted password
            )
            
            # Try to find and snapshot VM by IP first, then by hostname
            vm_identifier = host.ip  # Try IP first
            logger.info(f'[SCHEDULED-SNAPSHOT] ═══════════════════════════════════════')
            logger.info(f'[SCHEDULED-SNAPSHOT] Creating snapshot for HOST: {host.name}')
            logger.info(f'[SCHEDULED-SNAPSHOT] Host IP in database: {host.ip}')
            logger.info(f'[SCHEDULED-SNAPSHOT] Host vCenter: {host.vcenter_server}')
            logger.info(f'[SCHEDULED-SNAPSHOT] ═══════════════════════════════════════')
            logger.info(f'[SCHEDULED-SNAPSHOT] Attempt 1: Searching VM by IP: {vm_identifier}')
            success, message, snap_id = create_snapshot(
                si, vm_identifier, snapshot_name,
                f"Safety snapshot before {execution_name} (scheduled task)"
            )
            
            logger.info(f'[SCHEDULED-SNAPSHOT] First attempt (by IP) - Success: {success}, Message: {message}, Snap ID: {snap_id}')
            
            # If VM not found by IP, try by hostname
            if not success and "not found" in message.lower():
                logger.warning(f'[SCHEDULED-SNAPSHOT] ✗ VM not found by IP {host.ip}')
                logger.info(f'[SCHEDULED-SNAPSHOT] Attempt 2: Searching VM by hostname: {host.name}')
                success, message, snap_id = create_snapshot(
                    si, host.name,  # Try hostname
                    snapshot_name,
                    f"Safety snapshot before {execution_name} (scheduled task)"
                )
                logger.info(f'[SCHEDULED-SNAPSHOT] Second attempt (by hostname) - Success: {success}, Message: {message}, Snap ID: {snap_id}')
            else:
                if success:
                    logger.info(f'[SCHEDULED-SNAPSHOT] ✓ Snapshot created successfully on first attempt (by IP)')
                else:
                    logger.error(f'[SCHEDULED-SNAPSHOT] ✗ First attempt failed but not a "not found" error: {message}')
            
            Disconnect(si)
            
            if success:
                # Get retention hours from settings
                from settings.models import GlobalSetting
                retention_setting = GlobalSetting.objects.filter(key='snapshot_retention_hours').first()
                retention_hours = int(retention_setting.value) if retention_setting and retention_setting.value else 24
                
                # Save snapshot to SnapshotHistory
                # Note: expires_at is calculated automatically by the model's save() method
                # Only set playbook if execution_item is a Playbook (not a Script)
                from playbooks.models import Playbook
                playbook_obj = execution_item if isinstance(execution_item, Playbook) else None
                
                snapshot_record = SnapshotHistory.objects.create(
                    host=host,
                    playbook=playbook_obj,
                    snapshot_name=snapshot_name,
                    vcenter_snapshot_id=snap_id,
                    description=f"Safety snapshot before {execution_name} (scheduled task)",
                    retention_hours=retention_hours,
                    status='active',
                    size_mb=0,  # Size will be updated by cleanup task
                    user=task.created_by  # Use the user who created the scheduled task
                )
                logger.info(f"[SCHEDULED-SNAPSHOT] Snapshot saved to history: {snapshot_name} (ID: {snapshot_record.id}, retention: {retention_hours}h)")
                return snapshot_name, f"Snapshot created successfully: {snapshot_name}"
            else:
                return None, f"Failed to create snapshot: {message}"
                
        except Exception as e:
            logger.error(f"Exception creating snapshot for {host.name}: {e}")
            return None, f"Exception creating snapshot: {str(e)}"
    
    def cleanup_expired_snapshots(self):
        """Cleanup expired snapshots from database and vCenter"""
        from snapshots.models import SnapshotHistory
        from deploy.vcenter_snapshot import get_vcenter_connection, delete_snapshot, Disconnect
        
        now = timezone.now()
        expired_snapshots = SnapshotHistory.objects.filter(
            status='active',
            expires_at__lte=now
        )
        
        count = expired_snapshots.count()
        if count == 0:
            return
        
        logger.info(f'[SNAPSHOT-CLEANUP] Found {count} expired snapshots to cleanup')
        
        deleted_count = 0
        vcenter_deleted_count = 0
        
        for snapshot in expired_snapshots:
            try:
                # Try to delete from vCenter first
                if snapshot.host.vcenter_server:
                    try:
                        vcenter_cred = VCenterCredential.objects.filter(
                            host=snapshot.host.vcenter_server
                        ).first()
                        
                        if vcenter_cred:
                            si = get_vcenter_connection(
                                snapshot.host.vcenter_server,
                                vcenter_cred.user,
                                vcenter_cred.get_password()  # Use decrypted password
                            )
                            
                            success = delete_snapshot(
                                si,
                                snapshot.host.ip,
                                snapshot.snapshot_name
                            )
                            
                            Disconnect(si)
                            
                            if success:
                                vcenter_deleted_count += 1
                                logger.info(f'[SNAPSHOT-CLEANUP] Deleted from vCenter: {snapshot.snapshot_name}')
                            else:
                                logger.warning(f'[SNAPSHOT-CLEANUP] Could not delete from vCenter: {snapshot.snapshot_name}')
                    except Exception as e:
                        logger.error(f'[SNAPSHOT-CLEANUP] Error deleting from vCenter: {snapshot.snapshot_name} - {e}')
                
                # Mark as deleted in database
                snapshot.status = 'deleted'
                snapshot.deleted_at = now
                snapshot.save()
                deleted_count += 1
                logger.info(f'[SNAPSHOT-CLEANUP] Marked as deleted in DB: {snapshot.snapshot_name} ({snapshot.host.name})')
                
            except Exception as e:
                logger.error(f'[SNAPSHOT-CLEANUP] Error deleting snapshot {snapshot.snapshot_name}: {e}')
        
        logger.info(f'[SNAPSHOT-CLEANUP] Successfully marked {deleted_count}/{count} snapshots as deleted in DB')
        logger.info(f'[SNAPSHOT-CLEANUP] Successfully deleted {vcenter_deleted_count}/{count} snapshots from vCenter')
