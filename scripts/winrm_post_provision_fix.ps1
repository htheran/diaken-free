# ================================================================
# WinRM Post-Provisioning Reconfiguration Script
# ================================================================
# Purpose: Reconfigure WinRM after IP/hostname change
# This should run BEFORE reboot in the provisioning playbook
# Ensures WinRM listener works with new IP address
# ================================================================

Write-Host "Reconfiguring WinRM for new IP address..." -ForegroundColor Cyan

# Remove old listeners
Get-ChildItem WSMan:\localhost\Listener | Remove-Item -Recurse -Force

# Create new listener for ALL IPs
winrm create winrm/config/Listener?Address=*+Transport=HTTP

# Ensure TrustedHosts is configured
Set-Item WSMan:\localhost\Client\TrustedHosts -Value "*" -Force

# Ensure service starts automatically
Set-Service WinRM -StartupType Automatic

# Enable authentication methods
Set-Item WSMan:\localhost\Service\Auth\Basic -Value $true
Set-Item WSMan:\localhost\Service\Auth\Negotiate -Value $true

# Allow unencrypted traffic
Set-Item WSMan:\localhost\Service\AllowUnencrypted -Value $true

# Restart WinRM service
Restart-Service WinRM

Write-Host "WinRM reconfigured successfully" -ForegroundColor Green
