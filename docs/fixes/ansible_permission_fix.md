# Ansible Permission Fix - Oct 17, 2025

## Problem
When executing Ansible playbooks from the Django web application, the following error occurred:

```
ERROR: Unable to create local directories '/usr/share/httpd/.ansible/tmp': [Errno 13] Permission denied: b'/usr/share/httpd/.ansible'
PermissionError: [Errno 13] Permission denied: b'/usr/share/httpd/.ansible'
```

## Root Cause
The Apache user (`apache`) was running the Django application via mod_wsgi. When Ansible was invoked via `subprocess.run()`, it tried to create temporary directories in the Apache user's home directory (`/usr/share/httpd/.ansible`), which is not writable by the Apache user.

## Solution
Set environment variables for Ansible to use writable temporary directories in `/tmp` instead of the Apache user's home directory.

### Environment Variables Added
```python
ansible_env = os.environ.copy()
ansible_env['ANSIBLE_LOCAL_TEMP'] = '/tmp/ansible-local'
ansible_env['ANSIBLE_REMOTE_TEMP'] = '~/.ansible/tmp'
ansible_env['HOME'] = '/tmp'
ansible_env['ANSIBLE_SSH_CONTROL_PATH_DIR'] = '/tmp/ansible-ssh'
```

### Files Modified
1. **`/opt/www/app/diaken-pdn/deploy/views.py`**
   - Line ~427: Added environment variables to `provision_vm.yml` playbook execution
   - Line ~618: Added environment variables to additional playbooks execution

### Directories Created
```bash
sudo mkdir -p /tmp/ansible-local /tmp/ansible-ssh
sudo chmod 777 /tmp/ansible-local /tmp/ansible-ssh
```

These directories are writable by all users, including the Apache user.

## Verification
1. Apache service restarted successfully
2. Django application loads correctly
3. Ansible playbooks can now execute without permission errors

## Related Files
- `/opt/www/app/diaken-pdn/deploy/views_playbook.py` - Already had these env vars
- `/opt/www/app/diaken-pdn/deploy/views_playbook_windows.py` - Already had these env vars
- `/opt/www/app/diaken-pdn/deploy/views.py` - **FIXED** in this update

## Status
✅ **RESOLVED** - All Ansible playbook executions now use proper environment variables
