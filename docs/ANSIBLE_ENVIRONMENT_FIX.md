# Ansible Environment Configuration Fix

## Problem

Ansible-playbook failed with permission error:
```
PermissionError: [Errno 13] Permission denied: b'/usr/share/httpd/.ansible'
Unable to create local directories '/usr/share/httpd/.ansible/tmp'
```

## Root Cause

- Apache runs as user `apache`
- Apache's home directory is `/usr/share/httpd`
- Ansible tries to create temp directories in user's home: `~/.ansible/tmp`
- Apache user doesn't have write permissions in `/usr/share/httpd`

## Solution

Configure Ansible to use `/tmp` for temporary files instead of home directory.

### Changes Made

**1. Environment Variables (in /etc/httpd/conf.d/diaken-env.conf):**

```apache
# Ansible Configuration
# Fix permission issues with ansible temp directories
SetEnv ANSIBLE_LOCAL_TEMP "/tmp/.ansible/tmp"
SetEnv ANSIBLE_REMOTE_TEMP "/tmp/.ansible/tmp"
SetEnv HOME "/tmp"
```

**2. Create Ansible temp directory:**

```bash
sudo mkdir -p /tmp/.ansible/tmp
sudo chmod 777 /tmp/.ansible
sudo chmod 777 /tmp/.ansible/tmp
```

**3. Restart Apache:**

```bash
sudo systemctl restart httpd
```

## Verification

After applying the fix, ansible-playbook should run without permission errors:

```bash
# Check if ansible can write to temp directory
ls -la /tmp/.ansible/

# Test deployment
# Ansible should now be able to create temp files in /tmp/.ansible/tmp
```

## Benefits

✅ Ansible can create temp directories  
✅ Deployments work correctly  
✅ No permission errors  
✅ Uses /tmp (appropriate for temporary files)  
✅ Doesn't require changing apache user permissions  

## Alternative Solutions Considered

1. **Change apache home directory** - Not recommended, may break other services
2. **Give apache write permissions to /usr/share/httpd** - Security risk
3. **Run apache as different user** - Complex, affects many services
4. **Use /tmp for ansible** - ✅ Chosen solution (best practice)

## Security Considerations

- `/tmp` has proper permissions (1777)
- Files are created with apache user ownership
- Temporary files are automatically cleaned up
- No sensitive data stored permanently in /tmp

## Related Issues

- Issue: ansible-playbook permission denied
- Fix: Configure ANSIBLE_LOCAL_TEMP and HOME environment variables
- Date: 2025-10-17
