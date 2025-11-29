# WinRM Post-Deployment Connection Issue

## Problem Summary

**Symptom:** VM deployed successfully from Windows deployment form, but playbook execution fails with:
```
fatal: [10.100.5.89]: UNREACHABLE! => {
  "msg": "ntlm: ('Connection aborted.', ConnectionResetError(104, 'Connection reset by peer'))"
}
```

**Key Facts:**
- ✅ VM was deployed successfully using WinRM
- ✅ Network connectivity is OK (ping works, port 5985 open)
- ✅ Credentials are correct (same as deployment)
- ❌ WinRM connection fails after deployment

## Root Cause Analysis

### What Happens During Deployment:

1. VM cloned from template with **template IP** (e.g., 10.100.18.80)
2. Ansible connects to **template IP** via WinRM ✅
3. Playbook changes hostname and IP to **final IP** (e.g., 10.100.5.89)
4. Playbook schedules reboot in 40 seconds
5. VM reboots with new hostname and IP
6. **After reboot, WinRM may not start properly on new IP**

### Why WinRM Fails After Reboot:

1. **WinRM Listener bound to old IP**
   - WinRM listener was configured for template IP
   - After IP change, listener may not bind to new IP

2. **TrustedHosts not configured**
   - NTLM auth requires TrustedHosts configuration
   - May be reset or not applied to new IP

3. **WinRM service not auto-starting**
   - Service may not be set to automatic startup
   - May fail to start after network reconfiguration

4. **Firewall rules for new IP**
   - Firewall rules may be tied to old IP
   - New IP may not have WinRM allowed

## Solution

### Option 1: Fix WinRM on Deployed VM (Recommended)

Connect to the Windows VM (10.100.5.89) via RDP or console and run:

```powershell
# 1. Ensure WinRM service is running and set to automatic
Set-Service WinRM -StartupType Automatic
Start-Service WinRM

# 2. Remove old listeners
Get-ChildItem WSMan:\localhost\Listener | Remove-Item -Recurse -Force

# 3. Create new listener for all IPs
winrm quickconfig -force

# 4. Configure TrustedHosts
Set-Item WSMan:\localhost\Client\TrustedHosts -Value "*" -Force

# 5. Enable authentication methods
Set-Item WSMan:\localhost\Service\Auth\Basic -Value $true
Set-Item WSMan:\localhost\Service\Auth\Negotiate -Value $true

# 6. Allow unencrypted (for HTTP)
Set-Item WSMan:\localhost\Service\AllowUnencrypted -Value $true

# 7. Configure firewall
netsh advfirewall firewall add rule name="WinRM HTTP" dir=in action=allow protocol=TCP localport=5985

# 8. Restart WinRM
Restart-Service WinRM

# 9. Verify
Test-WSMan -ComputerName localhost
winrm enumerate winrm/config/listener
```

### Option 2: Modify Deployment Playbook (Preventive)

Add WinRM reconfiguration BEFORE reboot in `provision_windows_vm.yml`:

```yaml
- name: Reconfigure WinRM for new IP
  win_shell: |
    # Remove old listeners
    Get-ChildItem WSMan:\localhost\Listener | Remove-Item -Recurse -Force
    
    # Create new listener for all IPs
    winrm quickconfig -force -quiet
    
    # Configure TrustedHosts
    Set-Item WSMan:\localhost\Client\TrustedHosts -Value "*" -Force
    
    # Ensure service starts automatically
    Set-Service WinRM -StartupType Automatic
    
    Write-Output "WinRM reconfigured for new IP"
  register: winrm_reconfig
  ignore_errors: yes

- name: Display WinRM reconfiguration result
  debug:
    msg: "{{ winrm_reconfig.stdout }}"
```

Insert this task AFTER network configuration but BEFORE the reboot.

### Option 3: Use Basic Authentication

If NTLM continues to fail, switch to Basic authentication:

**On Windows VM:**
```powershell
Set-Item WSMan:\localhost\Service\Auth\Basic -Value $true
Set-Item WSMan:\localhost\Service\AllowUnencrypted -Value $true
Restart-Service WinRM
```

**In Django Admin:**
1. Go to Settings → Windows Credentials
2. Change `Auth Type` from `ntlm` to `basic`
3. Save

## Testing

After applying the fix, test the connection:

```bash
# Test 1: Direct ansible test
cd /opt/www/app
python test_winrm_connection.py test-win2

# Expected output:
# ✅ SUCCESS: WinRM connection working!

# Test 2: Execute playbook from web
# http://localhost:8001/deploy/playbook/windows/
# Select host: test-win2
# Select playbook: Update-Windows-Host
# Execute

# Should now work successfully
```

## Prevention for Future Deployments

### Add to Windows Template:

Before creating the template, configure WinRM properly:

```powershell
# Run on Windows template VM before converting to template

# 1. Enable PSRemoting
Enable-PSRemoting -Force

# 2. Configure WinRM to listen on all IPs
winrm quickconfig -force

# 3. Set TrustedHosts
Set-Item WSMan:\localhost\Client\TrustedHosts -Value "*" -Force

# 4. Enable all auth methods
Set-Item WSMan:\localhost\Service\Auth\Basic -Value $true
Set-Item WSMan:\localhost\Service\Auth\Negotiate -Value $true
Set-Item WSMan:\localhost\Service\AllowUnencrypted -Value $true

# 5. Set service to automatic
Set-Service WinRM -StartupType Automatic

# 6. Configure firewall
netsh advfirewall firewall add rule name="WinRM HTTP" dir=in action=allow protocol=TCP localport=5985

# 7. Create listener for 0.0.0.0 (all IPs)
winrm create winrm/config/Listener?Address=*+Transport=HTTP

# 8. Verify
winrm enumerate winrm/config/listener
```

This ensures WinRM works regardless of IP changes.

## Quick Diagnostic Commands

### On Windows VM:

```powershell
# Check WinRM service
Get-Service WinRM

# Check listeners
winrm enumerate winrm/config/listener

# Check TrustedHosts
Get-Item WSMan:\localhost\Client\TrustedHosts

# Test local connection
Test-WSMan -ComputerName localhost

# Check firewall rules
netsh advfirewall firewall show rule name="WinRM HTTP"
```

### From Ansible Server:

```bash
# Test port
timeout 3 bash -c "echo > /dev/tcp/10.100.5.89/5985" && echo "Port OPEN" || echo "Port CLOSED"

# Test WinRM connection
python /opt/www/app/scripts/test_winrm_connection.py test-win2

# Compare configurations
python /opt/www/app/scripts/compare_winrm_configs.py test-win2
```

## Summary

**The issue is NOT with the code or credentials.**

The issue is that **WinRM configuration on the Windows VM needs to be updated after the IP change during deployment.**

**Immediate fix:** Run the PowerShell commands in Option 1 on the Windows VM.

**Long-term fix:** Update the Windows template and/or deployment playbook to properly configure WinRM for IP changes.
