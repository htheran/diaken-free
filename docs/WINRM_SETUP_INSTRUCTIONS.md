# WinRM Setup Instructions for Windows Server

## Problem
```
fatal: [test-win2]: UNREACHABLE! => {
  "msg": "ntlm: ('Connection aborted.', ConnectionResetError(104, 'Connection reset by peer'))"
}
```

This error means the Windows server is **rejecting** the WinRM connection.

## Solution: Configure WinRM on Windows Server

### Step 1: Connect to Windows Server (test-win2)

Use RDP, VMware console, or any other method to access the Windows server.

### Step 2: Open PowerShell as Administrator

Right-click PowerShell → Run as Administrator

### Step 3: Enable WinRM

```powershell
# Enable PowerShell Remoting
Enable-PSRemoting -Force

# Start WinRM service
Start-Service WinRM

# Set WinRM to start automatically
Set-Service WinRM -StartupType Automatic

# Configure TrustedHosts (IMPORTANT for NTLM auth)
Set-Item WSMan:\localhost\Client\TrustedHosts -Value "*" -Force

# Restart WinRM service
Restart-Service WinRM
```

### Step 4: Configure Firewall

```powershell
# Allow WinRM HTTP (port 5985)
netsh advfirewall firewall add rule name="WinRM HTTP" dir=in action=allow protocol=TCP localport=5985

# Allow WinRM HTTPS (port 5986) - optional
netsh advfirewall firewall add rule name="WinRM HTTPS" dir=in action=allow protocol=TCP localport=5986
```

### Step 5: Configure WinRM Settings

```powershell
# Set basic authentication (if needed)
Set-Item WSMan:\localhost\Service\Auth\Basic -Value $true

# Set unencrypted traffic (for HTTP - not recommended for production)
Set-Item WSMan:\localhost\Service\AllowUnencrypted -Value $true

# Increase MaxMemoryPerShellMB for large operations
Set-Item WSMan:\localhost\Shell\MaxMemoryPerShellMB -Value 1024

# Increase timeout values
Set-Item WSMan:\localhost\MaxTimeoutms -Value 60000
```

### Step 6: Verify Configuration

```powershell
# Check WinRM service status
Get-Service WinRM

# Check WinRM configuration
winrm get winrm/config

# Check listeners
winrm enumerate winrm/config/listener

# Test local connection
Test-WSMan -ComputerName localhost
```

### Step 7: Test from Ansible Server

From the Ansible/Django server, run:

```bash
cd /opt/www/app
python test_winrm_connection.py test-win2
```

Expected output:
```
✅ SUCCESS: WinRM connection working!
```

## Alternative: Use Basic Authentication

If NTLM continues to fail, try Basic authentication:

### On Windows Server:

```powershell
# Enable Basic auth
Set-Item WSMan:\localhost\Service\Auth\Basic -Value $true
Set-Item WSMan:\localhost\Service\AllowUnencrypted -Value $true
Restart-Service WinRM
```

### In Django Admin:

1. Go to: http://localhost:8001/admin/
2. Navigate to: Settings → Windows Credentials
3. Find the credential for test-win2
4. Change `Auth Type` from `ntlm` to `basic`
5. Save

### Test Again:

```bash
python test_winrm_connection.py test-win2
```

## Troubleshooting

### Check if WinRM is listening:

```powershell
netstat -an | findstr :5985
```

Should show:
```
TCP    0.0.0.0:5985    0.0.0.0:0    LISTENING
```

### Check Windows Event Logs:

```powershell
Get-EventLog -LogName "Microsoft-Windows-WinRM/Operational" -Newest 20
```

### Test WinRM locally on Windows:

```powershell
Test-WSMan -ComputerName localhost
```

### Check authentication methods enabled:

```powershell
Get-Item WSMan:\localhost\Service\Auth\*
```

Should show:
```
Basic    : true
Kerberos : true
Negotiate: true
Certificate: false
CredSSP  : false
```

## Security Notes

⚠️ **For Production:**
- Use HTTPS (port 5986) instead of HTTP
- Use CredSSP or Kerberos instead of Basic
- Don't use `AllowUnencrypted`
- Configure proper TrustedHosts (not "*")

✅ **For Testing/Lab:**
- HTTP with Basic/NTLM is acceptable
- AllowUnencrypted is OK
- TrustedHosts "*" is OK

## Quick Fix Script (Run on Windows Server)

Save this as `setup_winrm.ps1` and run as Administrator:

```powershell
# Quick WinRM Setup Script
Write-Host "Configuring WinRM..." -ForegroundColor Green

# Enable PSRemoting
Enable-PSRemoting -Force

# Configure service
Set-Service WinRM -StartupType Automatic
Start-Service WinRM

# Configure TrustedHosts
Set-Item WSMan:\localhost\Client\TrustedHosts -Value "*" -Force

# Enable Basic auth
Set-Item WSMan:\localhost\Service\Auth\Basic -Value $true
Set-Item WSMan:\localhost\Service\AllowUnencrypted -Value $true

# Configure firewall
netsh advfirewall firewall add rule name="WinRM HTTP" dir=in action=allow protocol=TCP localport=5985

# Restart service
Restart-Service WinRM

# Verify
Write-Host "`nWinRM Configuration:" -ForegroundColor Yellow
winrm get winrm/config

Write-Host "`nListeners:" -ForegroundColor Yellow
winrm enumerate winrm/config/listener

Write-Host "`nTesting local connection..." -ForegroundColor Yellow
Test-WSMan -ComputerName localhost

Write-Host "`nWinRM setup complete!" -ForegroundColor Green
Write-Host "You can now test from Ansible server." -ForegroundColor Green
```

## Contact

If issues persist after following these steps, check:
1. Network connectivity between servers
2. Windows Firewall settings
3. Antivirus/Security software blocking WinRM
4. Domain policies restricting WinRM
