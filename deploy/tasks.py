"""
Celery tasks for deployment operations.
"""
from celery import shared_task
from django.utils import timezone
import logging

logger = logging.getLogger('deploy.tasks')


@shared_task(
    bind=True,
    name='deploy.tasks.execute_playbook_async',
    time_limit=3000,  # 50 minutes hard limit
    soft_time_limit=2700  # 45 minutes soft limit
)
def execute_playbook_async(self, history_id, inventory_content, execution_file, extra_vars_json, ansible_user, ssh_key_path, scheduled_task_history_id=None):
    """
    Execute a playbook asynchronously.
    
    Args:
        history_id: ID of the DeploymentHistory record (for manual executions)
        inventory_content: Ansible inventory content
        execution_file: Path to playbook/script file
        extra_vars_json: JSON string with extra variables
        ansible_user: SSH user
        ssh_key_path: Path to SSH private key
        scheduled_task_history_id: ID of ScheduledTaskHistory record (for scheduled tasks, optional)
    """
    from history.models import DeploymentHistory
    from scheduler.models import ScheduledTaskHistory
    from django.conf import settings
    import subprocess
    import os
    
    inventory_path = None
    history_record = None
    scheduled_history = None
    
    try:
        # Determine which history model to use
        if scheduled_task_history_id:
            scheduled_history = ScheduledTaskHistory.objects.get(pk=scheduled_task_history_id)
            scheduled_history.status = 'running'
            scheduled_history.save()
            target_name = scheduled_history.target_name
            playbook_name = scheduled_history.playbook_name
        else:
            history_record = DeploymentHistory.objects.get(pk=history_id)
            history_record.status = 'running'
            history_record.celery_task_id = self.request.id
            history_record.save()
            target_name = history_record.target
            playbook_name = history_record.playbook
        
        logger.info(f'[CELERY-{self.request.id}] Starting playbook execution for history ID: {history_id}')
        logger.info(f'[CELERY-{self.request.id}] Target: {target_name}, Playbook: {playbook_name}')
        logger.info(f'[CELERY-{self.request.id}] Scheduled task: {scheduled_task_history_id is not None}')
        
        # Create temporary inventory file
        inventory_path = f'/tmp/ansible_inventory_{history_id}.ini'
        with open(inventory_path, 'w') as f:
            f.write(inventory_content)
        
        logger.info(f'[CELERY-{self.request.id}] Inventory created at: {inventory_path}')
        logger.info(f'[CELERY-{self.request.id}] Executing: {execution_file}')
        
        # Build ansible-playbook command
        cmd = [
            settings.ANSIBLE_PLAYBOOK_PATH,
            '-i', inventory_path,
            execution_file,
            '--extra-vars', extra_vars_json,
            '-v'
        ]
        
        # Set environment variables for Ansible
        env = os.environ.copy()
        
        # Get virtualenv path for collections
        venv_path = str(settings.BASE_DIR / 'venv')
        collections_path = f"{venv_path}/lib/python3.12/site-packages/ansible_collections:/usr/share/ansible/collections"
        
        env.update({
            'ANSIBLE_LOCAL_TEMP': '/tmp/ansible-local',
            'ANSIBLE_REMOTE_TEMP': '~/.ansible/tmp',
            'HOME': '/tmp',
            'ANSIBLE_SSH_CONTROL_PATH_DIR': '/tmp/ansible-ssh',
            'ANSIBLE_HOME_DIR': '/tmp',
            'ANSIBLE_HOST_KEY_CHECKING': 'False',
            'ANSIBLE_COLLECTIONS_PATH': collections_path,
            'ANSIBLE_PYTHON_INTERPRETER': f"{venv_path}/bin/python3"
        })
        
        # Execute playbook with real-time output capture
        import select
        from threading import Timer
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=env
        )
        
        # Timeout handler
        timeout_seconds = 3000  # 50 minutes
        timer = Timer(timeout_seconds, lambda: process.kill())
        timer.start()
        
        output_lines = []
        try:
            # Read output line by line in real-time
            for line in iter(process.stdout.readline, ''):
                if line:
                    output_lines.append(line)
                    # Update DB every 10 lines for performance
                    if len(output_lines) % 10 == 0:
                        if scheduled_history:
                            scheduled_history.ansible_output = ''.join(output_lines)
                            scheduled_history.save(update_fields=['ansible_output'])
                        elif history_record:
                            history_record.ansible_output = ''.join(output_lines)
                            history_record.save(update_fields=['ansible_output'])
            
            # Wait for process to complete
            return_code = process.wait()
            timer.cancel()
            
        except Exception as e:
            timer.cancel()
            process.kill()
            raise e
        
        # Final output update
        output = ''.join(output_lines)
        
        logger.info(f'[CELERY-{self.request.id}] Playbook execution completed with return code: {return_code}')
        
        # Update history record
        if scheduled_history:
            scheduled_history.ansible_output = output
            scheduled_history.status = 'success' if return_code == 0 else 'failed'
            scheduled_history.completed_at = timezone.now()
            # Calculate execution duration
            duration = (timezone.now() - scheduled_history.executed_at).total_seconds()
            scheduled_history.execution_duration = int(duration)
            scheduled_history.save()
        elif history_record:
            history_record.ansible_output = output
            history_record.status = 'success' if return_code == 0 else 'failed'
            history_record.completed_at = timezone.now()
            history_record.save()
        
        # Clean up inventory file
        if inventory_path and os.path.exists(inventory_path):
            os.remove(inventory_path)
            logger.info(f'[CELERY-{self.request.id}] Inventory file removed')
        
        return {
            'status': 'success' if return_code == 0 else 'failed',
            'history_id': history_id,
            'return_code': return_code
        }
        
    except (DeploymentHistory.DoesNotExist, ScheduledTaskHistory.DoesNotExist) as e:
        logger.error(f'[CELERY-{self.request.id}] History record not found: {str(e)}')
        return {'status': 'error', 'message': 'History record not found'}
    except subprocess.TimeoutExpired:
        logger.error(f'[CELERY-{self.request.id}] Playbook execution timed out after 50 minutes')
        try:
            if scheduled_history:
                scheduled_history.status = 'failed'
                scheduled_history.ansible_output = "Error: Playbook execution timed out after 50 minutes"
                scheduled_history.error_message = "Timeout after 50 minutes"
                scheduled_history.completed_at = timezone.now()
                scheduled_history.save()
            elif history_record:
                history_record.status = 'failed'
                history_record.ansible_output = "Error: Playbook execution timed out after 50 minutes"
                history_record.completed_at = timezone.now()
                history_record.save()
        except:
            pass
        if inventory_path and os.path.exists(inventory_path):
            os.remove(inventory_path)
        return {'status': 'error', 'message': 'Timeout after 50 minutes'}
    except Exception as e:
        logger.error(f'[CELERY-{self.request.id}] Error executing playbook: {str(e)}', exc_info=True)
        try:
            if scheduled_history:
                scheduled_history.status = 'failed'
                scheduled_history.ansible_output = f"Error: {str(e)}"
                scheduled_history.error_message = str(e)
                scheduled_history.completed_at = timezone.now()
                scheduled_history.save()
            elif history_record:
                history_record.status = 'failed'
                history_record.ansible_output = f"Error: {str(e)}"
                history_record.completed_at = timezone.now()
                history_record.save()
        except:
            pass
        if inventory_path and os.path.exists(inventory_path):
            os.remove(inventory_path)
        return {'status': 'error', 'message': str(e)}


@shared_task(bind=True, name='deploy.tasks.execute_group_playbook_async')
def execute_group_playbook_async(self, history_id, host_ids, playbook_id):
    """
    Execute a playbook on a group of hosts asynchronously.
    
    Args:
        history_id: ID of the DeploymentHistory record
        host_ids: List of host IDs to execute on
        playbook_id: ID of the playbook to execute
    """
    from history.models import DeploymentHistory
    from playbooks.models import Playbook
    from inventory.models import Host
    from settings.models import GlobalSetting
    from django.conf import settings
    import subprocess
    import tempfile
    import os
    
    try:
        history_record = DeploymentHistory.objects.get(pk=history_id)
        history_record.status = 'running'
        history_record.save()
        
        logger.info(f'[TASK-{self.request.id}] Starting group playbook execution for history ID: {history_id}')
        logger.info(f'[TASK-{self.request.id}] Hosts: {len(host_ids)}, Playbook ID: {playbook_id}')
        
        playbook = Playbook.objects.get(pk=playbook_id)
        hosts = Host.objects.filter(pk__in=host_ids)
        
        # Create temporary inventory file
        inventory_content = "[target_hosts]\n"
        for host in hosts:
            inventory_content += f"{host.name} ansible_host={host.ip_address}\n"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as inv_file:
            inv_file.write(inventory_content)
            inventory_path = inv_file.name
        
        try:
            # Get all global settings for extra vars
            all_settings = GlobalSetting.objects.all()
            extra_vars = {}
            for setting in all_settings:
                extra_vars[setting.key] = setting.value
            
            # Build extra vars list
            extra_vars_list = []
            for key, value in extra_vars.items():
                extra_vars_list.extend(['-e', f'{key}={value}'])
            
            # Build ansible-playbook command
            cmd = [
                settings.ANSIBLE_PLAYBOOK_PATH,
                '-i', inventory_path,
                playbook.file.path,
                '-vv'
            ] + extra_vars_list
            
            logger.info(f'[TASK-{self.request.id}] Executing: {" ".join(cmd[:5])}...')
            
            # Set environment variables for Ansible
            ansible_env = os.environ.copy()
            ansible_env['ANSIBLE_LOCAL_TEMP'] = '/tmp/ansible-local'
            ansible_env['ANSIBLE_REMOTE_TEMP'] = '~/.ansible/tmp'
            ansible_env['HOME'] = '/tmp'
            ansible_env['ANSIBLE_SSH_CONTROL_PATH_DIR'] = '/tmp/ansible-ssh'
            ansible_env['ANSIBLE_HOME_DIR'] = '/tmp'
            ansible_env['ANSIBLE_HOST_KEY_CHECKING'] = 'False'
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1800,  # 30 minutes
                env=ansible_env
            )
            
            # Combine output
            full_output = f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
            
            # Determine success
            is_success = result.returncode == 0
            
            history_record.ansible_output = full_output
            history_record.status = 'success' if is_success else 'failed'
            history_record.completed_at = timezone.now()
            history_record.save()
            
            logger.info(f'[TASK-{self.request.id}] Group playbook execution completed: {history_record.status}')
            
            return {
                'status': history_record.status,
                'history_id': history_id,
                'return_code': result.returncode
            }
            
        finally:
            # Clean up inventory file
            try:
                os.remove(inventory_path)
            except:
                pass
        
    except Exception as e:
        logger.error(f'[TASK-{self.request.id}] Error executing group playbook: {str(e)}', exc_info=True)
        try:
            history_record.status = 'failed'
            history_record.ansible_output = f"Error: {str(e)}"
            history_record.completed_at = timezone.now()
            history_record.save()
        except:
            pass
        return {'status': 'error', 'message': str(e)}


@shared_task(
    bind=True,
    name='deploy.tasks.execute_script_async',
    time_limit=900,  # 15 minutes hard limit
    soft_time_limit=840  # 14 minutes soft limit
)
def execute_script_async(self, history_id, script_content, hosts_data, ansible_user, ssh_key_path):
    """
    Execute a script on multiple hosts asynchronously with real-time output.
    
    Args:
        history_id: ID of the DeploymentHistory record
        script_content: Script content to execute
        hosts_data: List of dicts with host info: [{'name': 'host1', 'ip': '10.0.0.1', 'ansible_user': 'user', 'ssh_key': '/path'}, ...]
        ansible_user: Default SSH user
        ssh_key_path: Default SSH key path
    """
    from history.models import DeploymentHistory
    import subprocess
    import os
    import shutil
    
    history_record = None
    
    try:
        history_record = DeploymentHistory.objects.get(pk=history_id)
        history_record.status = 'running'
        history_record.celery_task_id = self.request.id
        history_record.save()
        
        logger.info(f'[SCRIPT-ASYNC] Starting script execution on {len(hosts_data)} host(s)')
        
        # Build output
        full_output = f"Script Execution\n"
        full_output += f"Hosts: {len(hosts_data)}\n"
        full_output += "="*60 + "\n\n"
        
        # Update initial output
        history_record.output = full_output
        history_record.save()
        
        all_success = True
        
        # Find ssh command
        ssh_path = shutil.which('ssh')
        if not ssh_path:
            for path in ['/usr/bin/ssh', '/bin/ssh']:
                if os.path.exists(path):
                    ssh_path = path
                    break
        
        if not ssh_path:
            raise Exception('ssh command not found')
        
        # Execute on each host
        for idx, host_data in enumerate(hosts_data, 1):
            host_name = host_data['name']
            host_ip = host_data['ip']
            host_user = host_data.get('ansible_user', ansible_user)
            host_key = host_data.get('ssh_key', ssh_key_path)
            
            logger.info(f'[SCRIPT-ASYNC] Executing on host {idx}/{len(hosts_data)}: {host_name} ({host_ip})')
            
            full_output += f"[{idx}/{len(hosts_data)}] Host: {host_name} ({host_ip})\n"
            full_output += "-"*60 + "\n"
            
            # Update output in real-time
            history_record.output = full_output
            history_record.save()
            
            try:
                cmd = [
                    ssh_path,
                    '-i', host_key,
                    '-o', 'StrictHostKeyChecking=no',
                    '-o', 'UserKnownHostsFile=/dev/null',
                    f'{host_user}@{host_ip}',
                    'sudo bash -s'
                ]
                
                result = subprocess.run(
                    cmd,
                    input=script_content,
                    capture_output=True,
                    text=True,
                    timeout=600
                )
                
                if result.stdout:
                    full_output += "STDOUT:\n" + result.stdout + "\n"
                if result.stderr:
                    full_output += "STDERR:\n" + result.stderr + "\n"
                full_output += f"Exit Code: {result.returncode}\n"
                
                if result.returncode != 0:
                    all_success = False
                    full_output += f"❌ ERROR: Script failed on {host_name}\n"
                else:
                    full_output += f"✅ SUCCESS on {host_name}\n"
                
            except subprocess.TimeoutExpired:
                all_success = False
                full_output += f"❌ ERROR: Timeout on {host_name}\n"
            except Exception as e:
                all_success = False
                full_output += f"❌ ERROR on {host_name}: {str(e)}\n"
            
            full_output += "\n"
            
            # Update output after each host
            history_record.output = full_output
            history_record.save()
        
        # Final update
        full_output += "="*60 + "\n"
        if all_success:
            full_output += "✅ All hosts completed successfully\n"
            history_record.status = 'success'
        else:
            full_output += "❌ Some hosts failed\n"
            history_record.status = 'failed'
        
        history_record.output = full_output
        history_record.completed_at = timezone.now()
        history_record.save()
        
        logger.info(f'[SCRIPT-ASYNC] Completed with status: {history_record.status}')
        return {'status': 'success', 'output': full_output}
        
    except Exception as e:
        logger.error(f'[SCRIPT-ASYNC] Error: {str(e)}', exc_info=True)
        if history_record:
            history_record.status = 'failed'
            history_record.output = f"Error: {str(e)}\n" + (history_record.output or '')
            history_record.completed_at = timezone.now()
            history_record.save()
        return {'status': 'error', 'message': str(e)}


@shared_task(
    bind=True,
    name='deploy.tasks.execute_windows_playbook_async',
    time_limit=50400,  # 14 hours hard limit (for large groups)
    soft_time_limit=48600  # 13.5 hours soft limit
)
def execute_windows_playbook_async(self, history_id, inventory_content, execution_file, windows_user, windows_password, auth_type='ntlm', port=5985, playbook_content=None, scheduled_task_history_id=None):
    """
    Execute a Windows playbook asynchronously using WinRM.
    
    Args:
        history_id: ID of the DeploymentHistory record (for manual executions)
        inventory_content: Ansible inventory content for Windows
        execution_file: Path to playbook file (None if playbook_content is provided)
        windows_user: Windows username
        windows_password: Windows password
        auth_type: WinRM auth type (ntlm, basic, kerberos)
        port: WinRM port (5985 for HTTP, 5986 for HTTPS)
        playbook_content: Playbook YAML content (for scripts, instead of execution_file)
        scheduled_task_history_id: ID of ScheduledTaskHistory record (for scheduled tasks, optional)
    """
    from history.models import DeploymentHistory
    from scheduler.models import ScheduledTaskHistory
    from django.conf import settings
    import subprocess
    import os
    import tempfile
    
    inventory_path = None
    playbook_path = None
    history_record = None
    scheduled_history = None
    
    try:
        # Determine which history model to use
        if scheduled_task_history_id:
            scheduled_history = ScheduledTaskHistory.objects.get(pk=scheduled_task_history_id)
            scheduled_history.status = 'running'
            scheduled_history.save()
            target_name = scheduled_history.target_name
            playbook_name = scheduled_history.playbook_name
        else:
            history_record = DeploymentHistory.objects.get(pk=history_id)
            history_record.status = 'running'
            history_record.celery_task_id = self.request.id
            history_record.save()
            target_name = history_record.target
            playbook_name = history_record.playbook
        
        logger.info(f'[CELERY-WINDOWS-{self.request.id}] Starting Windows playbook execution for history ID: {history_id}')
        logger.info(f'[CELERY-WINDOWS-{self.request.id}] Target: {target_name}, Playbook: {playbook_name}')
        logger.info(f'[CELERY-WINDOWS-{self.request.id}] Scheduled task: {scheduled_task_history_id is not None}')
        
        # Create temporary inventory file
        inventory_path = f'/tmp/ansible_inventory_windows_{history_id}.ini'
        with open(inventory_path, 'w') as f:
            f.write(inventory_content)
        
        logger.info(f'[CELERY-WINDOWS-{self.request.id}] Inventory created at: {inventory_path}')
        logger.info(f'[CELERY-WINDOWS-{self.request.id}] Inventory content:\n{inventory_content}')
        
        # Create temporary playbook file if playbook_content is provided (for scripts)
        if playbook_content:
            playbook_path = f'/tmp/ansible_playbook_windows_{history_id}_{self.request.id}.yml'
            with open(playbook_path, 'w') as f:
                f.write(playbook_content)
            logger.info(f'[CELERY-WINDOWS-{self.request.id}] Temporary playbook created at: {playbook_path}')
            execution_file_to_use = playbook_path
        else:
            execution_file_to_use = execution_file
            logger.info(f'[CELERY-WINDOWS-{self.request.id}] Using playbook file: {execution_file}')
        
        # Build ansible-playbook command with extra vars from GlobalSetting
        from settings.models import GlobalSetting
        
        def get_setting(key, default):
            try:
                setting = GlobalSetting.objects.filter(key=key).first()
                return int(setting.value) if setting else default
            except:
                return default
        
        extra_vars = {
            'windows_update_max_cycles': get_setting('windows_update_max_cycles', 5),
            'windows_update_install_timeout': get_setting('windows_update_install_timeout', 5400),
            'windows_update_reboot_timeout': get_setting('windows_update_reboot_timeout', 600),
            'windows_update_post_reboot_delay': get_setting('windows_update_post_reboot_delay', 30),
            'windows_update_wsus_sync_wait': get_setting('windows_update_wsus_sync_wait', 30),
        }
        
        cmd = [
            settings.ANSIBLE_PLAYBOOK_PATH,
            '-vv',
            '-i', inventory_path,
            '-e', f'windows_update_max_cycles={extra_vars["windows_update_max_cycles"]}',
            '-e', f'windows_update_install_timeout={extra_vars["windows_update_install_timeout"]}',
            '-e', f'windows_update_reboot_timeout={extra_vars["windows_update_reboot_timeout"]}',
            '-e', f'windows_update_post_reboot_delay={extra_vars["windows_update_post_reboot_delay"]}',
            '-e', f'windows_update_wsus_sync_wait={extra_vars["windows_update_wsus_sync_wait"]}',
            execution_file_to_use,
        ]
        
        logger.info(f'[CELERY-WINDOWS-{self.request.id}] Extra vars: {extra_vars}')
        
        # Set environment variables for Ansible
        env = os.environ.copy()
        
        # Get virtualenv path for collections
        venv_path = str(settings.BASE_DIR / 'venv')
        collections_path = f"{venv_path}/lib/python3.12/site-packages/ansible_collections:/usr/share/ansible/collections"
        
        env.update({
            'ANSIBLE_LOCAL_TEMP': '/tmp/ansible-local',
            'ANSIBLE_REMOTE_TEMP': '~/.ansible/tmp',
            'HOME': '/tmp',
            'ANSIBLE_HOST_KEY_CHECKING': 'False',
            'ANSIBLE_COLLECTIONS_PATH': collections_path,
            'ANSIBLE_PYTHON_INTERPRETER': f"{venv_path}/bin/python3"
        })
        
        # Execute playbook with real-time output capture (90 minutes)
        from threading import Timer
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=env
        )
        
        # Timeout handler
        timeout_seconds = 5400  # 90 minutes
        timer = Timer(timeout_seconds, lambda: process.kill())
        timer.start()
        
        output_lines = []
        try:
            # Read output line by line in real-time
            for line in iter(process.stdout.readline, ''):
                if line:
                    output_lines.append(line)
                    # Update DB every 10 lines for performance
                    if len(output_lines) % 10 == 0:
                        if scheduled_history:
                            scheduled_history.ansible_output = ''.join(output_lines)
                            scheduled_history.save(update_fields=['ansible_output'])
                        elif history_record:
                            history_record.ansible_output = ''.join(output_lines)
                            history_record.save(update_fields=['ansible_output'])
            
            # Wait for process to complete
            return_code = process.wait()
            timer.cancel()
            
        except Exception as e:
            timer.cancel()
            process.kill()
            raise e
        
        # Final output update
        output = ''.join(output_lines)
        
        logger.info(f'[CELERY-WINDOWS-{self.request.id}] Playbook execution completed with return code: {return_code}')
        
        # Update history record
        if scheduled_history:
            scheduled_history.ansible_output = output
            scheduled_history.status = 'success' if return_code == 0 else 'failed'
            scheduled_history.completed_at = timezone.now()
            duration = (timezone.now() - scheduled_history.executed_at).total_seconds()
            scheduled_history.execution_duration = int(duration)
            scheduled_history.save()
        elif history_record:
            history_record.ansible_output = output
            history_record.status = 'success' if return_code == 0 else 'failed'
            history_record.completed_at = timezone.now()
            history_record.save()
        
        # Send notification
        try:
            from notifications.utils import send_playbook_notification
            from django.contrib.auth.models import User
            
            # Get user from history record
            user = history_record.user if history_record.user else User.objects.filter(is_superuser=True).first()
            
            # Build target info
            target_info = {
                'type': history_record.target_type or 'host',
                'name': history_record.target or 'Unknown'
            }
            
            send_playbook_notification(history_record, user, target_info, os_type='windows')
            logger.info(f'[CELERY-WINDOWS-{self.request.id}] Notification sent successfully')
        except Exception as notif_error:
            logger.warning(f'[CELERY-WINDOWS-{self.request.id}] Failed to send notification: {notif_error}')
        
        # Clean up inventory file
        if inventory_path and os.path.exists(inventory_path):
            os.remove(inventory_path)
            logger.info(f'[CELERY-WINDOWS-{self.request.id}] Inventory file removed')
        
        # Clean up temporary playbook file if it was created
        if playbook_path and os.path.exists(playbook_path):
            os.remove(playbook_path)
            logger.info(f'[CELERY-WINDOWS-{self.request.id}] Temporary playbook file removed')
        
        return {
            'status': 'success' if return_code == 0 else 'failed',
            'history_id': history_id,
            'return_code': return_code
        }
        
    except DeploymentHistory.DoesNotExist:
        logger.error(f'[CELERY-WINDOWS-{self.request.id}] DeploymentHistory with ID {history_id} not found')
        return {'status': 'error', 'message': 'History record not found'}
    except subprocess.TimeoutExpired:
        logger.error(f'[CELERY-WINDOWS-{self.request.id}] Playbook execution timed out after 90 minutes')
        try:
            history_record.status = 'failed'
            history_record.ansible_output = "Error: Playbook execution timed out after 90 minutes"
            history_record.completed_at = timezone.now()
            history_record.save()
            
            # Send notification for timeout
            try:
                from notifications.utils import send_playbook_notification
                from django.contrib.auth.models import User
                user = history_record.user if history_record.user else User.objects.filter(is_superuser=True).first()
                target_info = {
                    'type': history_record.target_type or 'host',
                    'name': history_record.target or 'Unknown'
                }
                send_playbook_notification(history_record, user, target_info, os_type='windows')
                logger.info(f'[CELERY-WINDOWS-{self.request.id}] Timeout notification sent')
            except Exception as notif_error:
                logger.warning(f'[CELERY-WINDOWS-{self.request.id}] Failed to send notification: {notif_error}')
        except:
            pass
        if inventory_path and os.path.exists(inventory_path):
            os.remove(inventory_path)
        if playbook_path and os.path.exists(playbook_path):
            os.remove(playbook_path)
        return {'status': 'error', 'message': 'Timeout after 90 minutes'}
    except Exception as e:
        logger.error(f'[CELERY-WINDOWS-{self.request.id}] Error executing playbook: {str(e)}', exc_info=True)
        try:
            history_record.status = 'failed'
            history_record.ansible_output = f"Error: {str(e)}"
            history_record.completed_at = timezone.now()
            history_record.save()
            
            # Send notification for error
            try:
                from notifications.utils import send_playbook_notification
                from django.contrib.auth.models import User
                user = history_record.user if history_record.user else User.objects.filter(is_superuser=True).first()
                target_info = {
                    'type': history_record.target_type or 'host',
                    'name': history_record.target or 'Unknown'
                }
                send_playbook_notification(history_record, user, target_info, os_type='windows')
                logger.info(f'[CELERY-WINDOWS-{self.request.id}] Error notification sent')
            except Exception as notif_error:
                logger.warning(f'[CELERY-WINDOWS-{self.request.id}] Failed to send notification: {notif_error}')
        except:
            pass
        if inventory_path and os.path.exists(inventory_path):
            os.remove(inventory_path)
        if playbook_path and os.path.exists(playbook_path):
            os.remove(playbook_path)
        return {'status': 'error', 'message': str(e)}


@shared_task(
    bind=True,
    name='deploy.tasks.provision_linux_vm_async',
    time_limit=1900,  # 31 minutes hard limit
    soft_time_limit=1800  # 30 minutes soft limit (increased for Ubuntu support)
)
def provision_linux_vm_async(self, history_id, template_ip, new_ip, new_hostname, gateway, interface, os_family, 
                             ssh_user, ssh_key_path, python_interpreter, vcenter_host, vcenter_user, 
                             vcenter_password, network_name, deploy_env, deploy_group, template, datacenter, cluster,
                             additional_playbooks=None):
    """
    Provision a Linux VM asynchronously: run Ansible playbook, change network in vCenter, verify SSH, add to inventory.
    
    Args:
        history_id: ID of the DeploymentHistory record
        template_ip: IP of the template for initial SSH connection
        new_ip: New IP address for the VM
        new_hostname: New hostname for the VM
        gateway: Gateway IP address
        interface: Network interface name (e.g. ens192)
        os_family: OS family (debian or redhat)
        ssh_user: SSH username
        ssh_key_path: Path to SSH private key
        python_interpreter: Path to Python interpreter on target
        vcenter_host: vCenter hostname/IP
        vcenter_user: vCenter username
        vcenter_password: vCenter password
        network_name: Target network name in vCenter
        deploy_env: Environment name for inventory
        deploy_group: Group name for inventory
        template: Template name used for deployment
        datacenter: vCenter datacenter name
        cluster: vCenter cluster name
    """
    from history.models import DeploymentHistory
    from django.conf import settings
    from deploy.govc_helper import change_vm_network_govc
    import subprocess
    import os
    import time
    import socket
    
    try:
        history_record = DeploymentHistory.objects.get(pk=history_id)
        history_record.status = 'running'
        history_record.celery_task_id = self.request.id
        history_record.save()
        
        logger.info(f'[CELERY-LINUX-{self.request.id}] Starting Linux VM provisioning for history ID: {history_id}')
        logger.info(f'[CELERY-LINUX-{self.request.id}] VM: {new_hostname}, Template IP: {template_ip}, New IP: {new_ip}')
        
        # STEP 0: Wait for VM to boot and SSH to be ready
        logger.info(f'[CELERY-LINUX-{self.request.id}] Waiting for SSH to be ready on {template_ip}...')
        ssh_ready = False
        max_wait_boot = 120  # 2 minutes
        wait_interval_boot = 5
        elapsed_boot = 0
        
        logger.info(f'[CELERY-LINUX-{self.request.id}] Waiting for SSH on {template_ip}:22 (max {max_wait_boot}s)...')
        
        while elapsed_boot < max_wait_boot and not ssh_ready:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result_sock = sock.connect_ex((template_ip, 22))
                sock.close()
                if result_sock == 0:
                    ssh_ready = True
                    logger.info(f'[CELERY-LINUX-{self.request.id}] ✓ SSH ready on {template_ip}:22 after {elapsed_boot}s')
                else:
                    if elapsed_boot % 15 == 0:  # Log every 15 seconds
                        logger.info(f'[CELERY-LINUX-{self.request.id}] Still waiting for SSH... ({elapsed_boot}s/{max_wait_boot}s)')
                    time.sleep(wait_interval_boot)
                    elapsed_boot += wait_interval_boot
            except Exception as e:
                if elapsed_boot % 15 == 0:  # Log every 15 seconds
                    logger.warning(f'[CELERY-LINUX-{self.request.id}] SSH check error: {e} ({elapsed_boot}s/{max_wait_boot}s)')
                time.sleep(wait_interval_boot)
                elapsed_boot += wait_interval_boot
        
        if not ssh_ready:
            error_msg = f'SSH not ready on {template_ip} after {max_wait_boot}s. VM may not have booted properly.'
            logger.error(f'[CELERY-LINUX-{self.request.id}] {error_msg}')
            history_record.ansible_output = f"ERROR: {error_msg}"
            history_record.completed_at = timezone.now()
            history_record.status = 'failed'
            history_record.save()
            return {'status': 'failed', 'history_id': history_id, 'message': error_msg}
        
        # STEP 1: Execute Ansible playbook to configure hostname and IP
        # Selecciona playbook según OS
        import os
        import stat
        
        # Verify SSH key exists and has correct permissions
        if not os.path.exists(ssh_key_path):
            error_msg = f'SSH key not found: {ssh_key_path}'
            logger.error(f'[CELERY-LINUX-{self.request.id}] {error_msg}')
            history_record.ansible_output = f"ERROR: {error_msg}"
            history_record.completed_at = timezone.now()
            history_record.status = 'failed'
            history_record.save()
            return {'status': 'failed', 'history_id': history_id, 'message': error_msg}
        
        # Check and fix SSH key permissions (must be 600)
        try:
            current_perms = stat.S_IMODE(os.lstat(ssh_key_path).st_mode)
            if current_perms != 0o600:
                logger.warning(f'[CELERY-LINUX-{self.request.id}] SSH key has incorrect permissions: {oct(current_perms)}. Fixing to 600...')
                os.chmod(ssh_key_path, 0o600)
                logger.info(f'[CELERY-LINUX-{self.request.id}] SSH key permissions fixed to 600')
            else:
                logger.info(f'[CELERY-LINUX-{self.request.id}] SSH key permissions are correct: 600')
        except Exception as e:
            logger.warning(f'[CELERY-LINUX-{self.request.id}] Could not check/fix SSH key permissions: {e}')
        
        logger.info(f'[CELERY-LINUX-{self.request.id}] Using SSH key: {ssh_key_path}')
        logger.info(f'[CELERY-LINUX-{self.request.id}] SSH user: {ssh_user}')
        logger.info(f'[CELERY-LINUX-{self.request.id}] Target IP: {template_ip}')
        
        if os_family and os_family.lower() == 'debian':
            ansible_playbook = os.path.join(settings.BASE_DIR, 'ansible', 'provision_debian_vm.yml')
            logger.info(f'[CELERY-LINUX-{self.request.id}] Using Debian playbook: {ansible_playbook}')
        else:
            ansible_playbook = os.path.join(settings.BASE_DIR, 'ansible', 'provision_vm.yml')
            logger.info(f'[CELERY-LINUX-{self.request.id}] Using RedHat playbook: {ansible_playbook}')
        
        cmd = [
            settings.ANSIBLE_PLAYBOOK_PATH,
            '-i', f'{template_ip},',
            '-u', ssh_user,
            '--private-key', ssh_key_path,
            ansible_playbook,
            '-e', f'hostname={new_hostname}',
            '-e', f'ip={new_ip}',
            '-e', f'gateway={gateway}',
            '-e', f'interface={interface}',
            '-e', f'os_family={os_family}',
            '-e', f'ansible_python_interpreter={python_interpreter}',
            "-e", "ansible_ssh_common_args='-o StrictHostKeyChecking=no'",
            '-vvv'
        ]
        
        logger.info(f'[CELERY-LINUX-{self.request.id}] Executing Ansible command: {" ".join(cmd)}')
        
        # Set environment variables for Ansible
        ansible_env = os.environ.copy()
        ansible_env['ANSIBLE_LOCAL_TEMP'] = '/tmp/ansible-local'
        ansible_env['ANSIBLE_REMOTE_TEMP'] = '~/.ansible/tmp'
        ansible_env['HOME'] = '/tmp'
        ansible_env['ANSIBLE_SSH_CONTROL_PATH_DIR'] = '/tmp/ansible-ssh'
        ansible_env['ANSIBLE_HOME_DIR'] = '/tmp'
        ansible_env['ANSIBLE_HOST_KEY_CHECKING'] = 'False'
        
        # Execute with Popen for real-time output capture
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=ansible_env
        )
        
        output_lines = []
        line_count = 0
        
        # Read output line by line
        for line in process.stdout:
            output_lines.append(line)
            line_count += 1
            
            # Update database every 10 lines for performance
            if line_count % 10 == 0:
                history_record.ansible_output = ''.join(output_lines)
                history_record.save(update_fields=['ansible_output'])
        
        # Wait for process to complete
        return_code = process.wait(timeout=600)
        
        # Final update with all output
        output = ''.join(output_lines)
        provision_output = f"=== PROVISIONING PLAYBOOK (provision_vm.yml) ===\n\n{output}"
        
        logger.info(f'[CELERY-LINUX-{self.request.id}] Ansible return code: {return_code}')
        
        if return_code != 0:
            logger.error(f'[CELERY-LINUX-{self.request.id}] Ansible playbook failed with return code: {return_code}')
            history_record.ansible_output = provision_output
            history_record.completed_at = timezone.now()
            history_record.status = 'failed'
            history_record.save()
            
            # Send notification
            try:
                from notifications.utils import send_deployment_notification
                send_deployment_notification(history_record, history_record.user)
            except Exception as notif_error:
                logger.warning(f'[CELERY-LINUX-{self.request.id}] Failed to send notification: {notif_error}')
            
            return {'status': 'failed', 'history_id': history_id, 'return_code': return_code}
        
        logger.info(f'[CELERY-LINUX-{self.request.id}] Ansible playbook completed successfully')
        
        # STEP 2: Change network in vCenter using govc
        logger.info(f'[CELERY-LINUX-{self.request.id}] Changing network in vCenter to: {network_name}')
        
        network_change_success, message = change_vm_network_govc(
            vcenter_host=vcenter_host,
            vcenter_user=vcenter_user,
            vcenter_password=vcenter_password,
            vm_name=new_hostname,
            network_name=network_name
        )
        
        logger.info(f'[CELERY-LINUX-{self.request.id}] Network change result: {"SUCCESS" if network_change_success else "FAILED"}')
        logger.info(f'[CELERY-LINUX-{self.request.id}] Message: {message}')
        
        if network_change_success:
            provision_output += f"\n\n{'='*80}\n=== NETWORK CHANGE IN VCENTER ===\n{'='*80}\n✅ SUCCESS: {message}\nNetwork changed to '{network_name}'\n"
        else:
            provision_output += f"\n\n{'='*80}\n=== NETWORK CHANGE IN VCENTER ===\n{'='*80}\n❌ ERROR: {message}\n\n⚠️ WARNING: VM remains on original network.\nVerify network manually in vCenter.\n"
        
        # STEP 3: Wait for VM to reboot (scheduled in playbook)
        logger.info(f'[CELERY-LINUX-{self.request.id}] Waiting 60 seconds for VM to reboot...')
        time.sleep(60)
        
        # STEP 4: Verify SSH on new IP
        logger.info(f'[CELERY-LINUX-{self.request.id}] Verifying SSH connectivity on new IP: {new_ip}')
        
        ssh_ready = False
        max_wait = 60
        wait_interval = 5
        elapsed = 0
        
        while elapsed < max_wait and not ssh_ready:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result_sock = sock.connect_ex((new_ip, 22))
                sock.close()
                if result_sock == 0:
                    ssh_ready = True
                    logger.info(f'[CELERY-LINUX-{self.request.id}] SSH available on {new_ip}:22')
                else:
                    time.sleep(wait_interval)
                    elapsed += wait_interval
            except Exception as e:
                time.sleep(wait_interval)
                elapsed += wait_interval
        
        if ssh_ready:
            logger.info(f'[CELERY-LINUX-{self.request.id}] ✅ Provisioning completed successfully')
            
            # Accept SSH fingerprint for new IP
            logger.info(f'[CELERY-LINUX-{self.request.id}] Accepting SSH fingerprint for {new_ip}...')
            try:
                accept_cmd = ['ssh-keyscan', '-H', new_ip]
                keyscan_result = subprocess.run(accept_cmd, capture_output=True, text=True, timeout=30)
                if keyscan_result.returncode == 0 and keyscan_result.stdout:
                    known_hosts_path = os.path.expanduser('~/.ssh/known_hosts')
                    with open(known_hosts_path, 'a') as kh:
                        kh.write(keyscan_result.stdout)
                    logger.info(f'[CELERY-LINUX-{self.request.id}] ✅ SSH fingerprint accepted for {new_ip}')
                else:
                    logger.warning(f'[CELERY-LINUX-{self.request.id}] Could not get SSH fingerprint for {new_ip}')
            except Exception as e:
                logger.warning(f'[CELERY-LINUX-{self.request.id}] Error accepting SSH fingerprint: {e}')
            
            # Register VM in inventory
            logger.info(f'[CELERY-LINUX-{self.request.id}] Registering VM in inventory...')
            try:
                from inventory.models import Host, Environment, Group
                
                # Get or create environment and group
                env, created = Environment.objects.get_or_create(
                    name=deploy_env if deploy_env else 'Default',
                    defaults={'description': 'Auto-created environment'}
                )
                if created:
                    logger.info(f'[CELERY-LINUX-{self.request.id}] Created new environment: {env.name}')
                
                group, created = Group.objects.get_or_create(
                    name=deploy_group if deploy_group else 'Default',
                    environment=env,
                    defaults={'description': 'Auto-created group'}
                )
                if created:
                    logger.info(f'[CELERY-LINUX-{self.request.id}] Created new group: {group.name}')
                
                Host.objects.create(
                    name=new_hostname,
                    ip=new_ip,
                    vcenter_server=vcenter_host,
                    environment=env,
                    group=group,
                    operating_system=os_family,
                    ansible_python_interpreter=python_interpreter,
                    description=f'Deployed from template {template} (Datacenter: {datacenter}, Cluster: {cluster})',
                    active=True
                )
                
                logger.info(f'[CELERY-LINUX-{self.request.id}] ✅ VM registered in inventory: {new_hostname} ({new_ip})')
                provision_output += f"\n\n{'='*80}\n=== INVENTORY REGISTRATION ===\n{'='*80}\n✅ SUCCESS: VM registered in inventory\nHostname: {new_hostname}\nIP: {new_ip}\nEnvironment: {deploy_env}\nGroup: {deploy_group}\n"
            except Exception as e:
                logger.error(f'[CELERY-LINUX-{self.request.id}] ❌ Failed to register VM in inventory: {e}')
                provision_output += f"\n\n{'='*80}\n=== INVENTORY REGISTRATION ===\n{'='*80}\n❌ ERROR: Failed to register VM in inventory\n{str(e)}\n\n⚠️ WARNING: VM was provisioned successfully but not added to inventory.\nAdd manually if needed.\n"
            
            # STEP 7: Execute additional playbooks if selected
            if additional_playbooks and len(additional_playbooks) > 0:
                logger.info(f'[CELERY-LINUX-{self.request.id}] Executing {len(additional_playbooks)} additional playbooks...')
                provision_output += f"\n\n{'='*80}\n=== ADDITIONAL PLAYBOOKS ===\n{'='*80}\n"
                
                for playbook_name in additional_playbooks:
                    logger.info(f'[CELERY-LINUX-{self.request.id}] Executing playbook: {playbook_name}')
                    provision_output += f"\n\n--- Executing: {playbook_name} ---\n\n"
                    
                    # Find playbook file
                    playbook_path = os.path.join(settings.BASE_DIR, 'media', 'playbooks', 'host', f'{playbook_name}.yml')
                    playbook_relative = os.path.join('media', 'playbooks', 'host', f'{playbook_name}.yml')
                    
                    if not os.path.exists(playbook_path):
                        logger.error(f'[CELERY-LINUX-{self.request.id}] Playbook not found: {playbook_relative}')
                        provision_output += f"⚠️ WARNING: Playbook '{playbook_name}' not found at {playbook_relative}\n"
                        provision_output += f"   Create the playbook file or remove it from the deployment configuration.\n"
                        continue
                    
                    # Execute playbook
                    try:
                        # Create temporary inventory file with [target_host] group
                        import tempfile
                        # Use hostname as inventory name but connect via IP using ansible_host
                        inventory_content = f"""[target_host]
{new_hostname} ansible_host={new_ip} ansible_user={ssh_user} ansible_ssh_private_key_file={ssh_key_path} ansible_python_interpreter={python_interpreter} ansible_ssh_common_args='-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'
"""
                        
                        # Create temp file
                        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False, dir='/tmp') as inv_file:
                            inv_file.write(inventory_content)
                            inventory_path = inv_file.name
                        
                        logger.info(f'[CELERY-LINUX-{self.request.id}] Created inventory: {inventory_path}')
                        logger.info(f'[CELERY-LINUX-{self.request.id}] Inventory content:\n{inventory_content}')
                        
                        # Prepare extra vars
                        extra_vars = {
                            'target_host': new_ip,
                            'inventory_hostname': new_hostname
                        }
                        
                        # Add all global settings as extra vars
                        from settings.models import GlobalSetting
                        global_settings = GlobalSetting.objects.all()
                        for setting in global_settings:
                            extra_vars[setting.key] = setting.value
                        
                        logger.info(f'[CELERY-LINUX-{self.request.id}] Extra vars: {list(extra_vars.keys())}')
                        
                        import json
                        extra_vars_json = json.dumps(extra_vars)
                        
                        ansible_cmd = [
                            os.path.join(settings.BASE_DIR, 'venv', 'bin', 'ansible-playbook'),
                            '-i', inventory_path,
                            playbook_path,
                            '-e', extra_vars_json,
                            '-vvv'
                        ]
                        
                        logger.info(f'[CELERY-LINUX-{self.request.id}] Ansible command: {" ".join(ansible_cmd)}')
                        
                        result = subprocess.run(
                            ansible_cmd,
                            capture_output=True,
                            text=True,
                            timeout=600  # 10 minutes per playbook
                        )
                        
                        provision_output += f"STDOUT:\n{result.stdout}\n\n"
                        if result.stderr:
                            provision_output += f"STDERR:\n{result.stderr}\n\n"
                        
                        if result.returncode == 0:
                            logger.info(f'[CELERY-LINUX-{self.request.id}] ✅ Playbook {playbook_name} completed successfully')
                            provision_output += f"✅ SUCCESS: {playbook_name} completed\n"
                        else:
                            logger.error(f'[CELERY-LINUX-{self.request.id}] ❌ Playbook {playbook_name} failed with return code {result.returncode}')
                            provision_output += f"❌ ERROR: {playbook_name} failed (return code {result.returncode})\n"
                        
                        # Clean up temporary inventory file
                        try:
                            os.remove(inventory_path)
                            logger.info(f'[CELERY-LINUX-{self.request.id}] Cleaned up inventory file: {inventory_path}')
                        except Exception as cleanup_error:
                            logger.warning(f'[CELERY-LINUX-{self.request.id}] Failed to cleanup inventory: {cleanup_error}')
                    
                    except subprocess.TimeoutExpired:
                        logger.error(f'[CELERY-LINUX-{self.request.id}] ❌ Playbook {playbook_name} timeout')
                        provision_output += f"❌ ERROR: {playbook_name} timeout (>10 minutes)\n"
                        # Clean up inventory file on timeout
                        try:
                            os.remove(inventory_path)
                        except:
                            pass
                    except Exception as e:
                        logger.error(f'[CELERY-LINUX-{self.request.id}] ❌ Playbook {playbook_name} exception: {e}')
                        provision_output += f"❌ ERROR: {playbook_name} exception: {str(e)}\n"
                        # Clean up inventory file on exception
                        try:
                            if 'inventory_path' in locals():
                                os.remove(inventory_path)
                        except:
                            pass
            
            history_record.ansible_output = provision_output
            history_record.completed_at = timezone.now()
            history_record.status = 'success'
            history_record.save()
            
            # Send success notification
            try:
                from notifications.utils import send_deployment_notification
                send_deployment_notification(history_record, history_record.user)
            except Exception as notif_error:
                logger.warning(f'[CELERY-LINUX-{self.request.id}] Failed to send notification: {notif_error}')
            
            return {'status': 'success', 'history_id': history_id, 'return_code': 0}
        else:
            logger.error(f'[CELERY-LINUX-{self.request.id}] ❌ SSH verification failed on new IP: {new_ip}')
            history_record.ansible_output = provision_output + f"\n\n❌ ERROR: Could not establish SSH connection to {new_ip} after reboot.\nVM may not be on the correct network or IP was not applied correctly."
            history_record.completed_at = timezone.now()
            history_record.status = 'failed'
            history_record.save()
            
            # Send failure notification
            try:
                from notifications.utils import send_deployment_notification
                send_deployment_notification(history_record, history_record.user)
            except Exception as notif_error:
                logger.warning(f'[CELERY-LINUX-{self.request.id}] Failed to send notification: {notif_error}')
            
            return {'status': 'failed', 'history_id': history_id, 'message': 'SSH verification failed'}
        
    except subprocess.TimeoutExpired:
        logger.error(f'[CELERY-LINUX-{self.request.id}] ❌ Ansible playbook timeout (>600s)')
        history_record = DeploymentHistory.objects.get(pk=history_id)
        history_record.ansible_output = "ERROR: Ansible playbook execution timeout (>10 minutes)"
        history_record.completed_at = timezone.now()
        history_record.status = 'failed'
        history_record.save()
        
        # Send timeout notification
        try:
            from notifications.utils import send_deployment_notification
            send_deployment_notification(history_record, history_record.user)
        except Exception as notif_error:
            logger.warning(f'[CELERY-LINUX-{self.request.id}] Failed to send notification: {notif_error}')
        
        return {'status': 'timeout', 'history_id': history_id}
        
    except Exception as e:
        logger.error(f'[CELERY-LINUX-{self.request.id}] ❌ Exception: {str(e)}')
        try:
            history_record = DeploymentHistory.objects.get(pk=history_id)
            history_record.ansible_output = f"Exception: {str(e)}"
            history_record.completed_at = timezone.now()
            history_record.status = 'failed'
            history_record.save()
            
            # Send error notification
            try:
                from notifications.utils import send_deployment_notification
                send_deployment_notification(history_record, history_record.user)
            except Exception as notif_error:
                logger.warning(f'[CELERY-LINUX-{self.request.id}] Failed to send notification: {notif_error}')
        except:
            pass
        
        return {'status': 'error', 'message': str(e)}
