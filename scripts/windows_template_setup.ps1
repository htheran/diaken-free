# ================================================================
# Windows Template WinRM Configuration Script
# ================================================================
# Purpose: Prepare Windows template for Ansible automation
# Run this on the Windows template BEFORE converting to template
# Ensures WinRM works regardless of IP address changes
# ================================================================

Write-Host "=======================================" -ForegroundColor Cyan
Write-Host "Windows Template WinRM Setup" -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host ""

# 1. Enable PowerShell Remoting
Write-Host "[1/10] Enabling PowerShell Remoting..." -ForegroundColor Yellow
Enable-PSRemoting -Force -SkipNetworkProfileCheck
Write-Host "✓ PowerShell Remoting enabled" -ForegroundColor Green
Write-Host ""

# 2. Start WinRM service and set to automatic
Write-Host "[2/10] Configuring WinRM service..." -ForegroundColor Yellow
Set-Service WinRM -StartupType Automatic
Start-Service WinRM
Write-Host "✓ WinRM service configured for automatic startup" -ForegroundColor Green
Write-Host ""

# 3. Check if listener with Address=* already exists
Write-Host "[3/10] Checking existing WinRM listeners..." -ForegroundColor Yellow
$existingListener = winrm enumerate winrm/config/listener | Select-String -Pattern "Address = \*" -Quiet

if ($existingListener) {
    Write-Host "✓ WinRM listener with Address=* already exists - skipping recreation" -ForegroundColor Green
    Write-Host "  (This is the correct configuration for dynamic IP support)" -ForegroundColor Cyan
} else {
    Write-Host "  No Address=* listener found - will create it" -ForegroundColor Yellow
    
    # Remove existing listeners (clean slate)
    Write-Host "  Removing existing WinRM listeners..." -ForegroundColor Yellow
    Get-ChildItem WSMan:\localhost\Listener | Where-Object { $_.Keys -contains "Transport=HTTP" } | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Get-ChildItem WSMan:\localhost\Listener | Where-Object { $_.Keys -contains "Transport=HTTPS" } | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "  ✓ Existing listeners removed" -ForegroundColor Green
    
    # Create listener for ALL IP addresses (Address=*)
    Write-Host "  Creating WinRM listener for ALL IP addresses..." -ForegroundColor Yellow
    winrm create winrm/config/Listener?Address=*+Transport=HTTP
    Write-Host "  ✓ WinRM listener created for Address=* (all IPs)" -ForegroundColor Green
}
Write-Host ""

# 4. Verify listener configuration
Write-Host "[4/10] Verifying WinRM listener configuration..." -ForegroundColor Yellow
$listeners = winrm enumerate winrm/config/listener
if ($listeners -match "Address = \*") {
    Write-Host "✓ Confirmed: WinRM listener is configured for Address=* (all IPs)" -ForegroundColor Green
} else {
    Write-Host "⚠ Warning: Could not confirm Address=* configuration" -ForegroundColor Red
}
Write-Host ""

# 5. Configure TrustedHosts (allow connections from any IP)
Write-Host "[5/10] Configuring TrustedHosts..." -ForegroundColor Yellow
Set-Item WSMan:\localhost\Client\TrustedHosts -Value "*" -Force
Write-Host "✓ TrustedHosts configured to accept all connections" -ForegroundColor Green
Write-Host ""

# 6. Enable authentication methods
Write-Host "[6/10] Enabling authentication methods..." -ForegroundColor Yellow
Set-Item WSMan:\localhost\Service\Auth\Basic -Value $true
Set-Item WSMan:\localhost\Service\Auth\Negotiate -Value $true
Set-Item WSMan:\localhost\Service\Auth\CredSSP -Value $true
Write-Host "✓ Basic, Negotiate, and CredSSP authentication enabled" -ForegroundColor Green
Write-Host ""

# 7. Allow unencrypted traffic (for HTTP - port 5985)
Write-Host "[7/10] Allowing unencrypted traffic..." -ForegroundColor Yellow
Set-Item WSMan:\localhost\Service\AllowUnencrypted -Value $true
Write-Host "✓ Unencrypted traffic allowed (HTTP on port 5985)" -ForegroundColor Green
Write-Host ""

# 8. Increase memory and timeout limits
Write-Host "[8/10] Configuring memory and timeout limits..." -ForegroundColor Yellow
Set-Item WSMan:\localhost\Shell\MaxMemoryPerShellMB -Value 2048
Set-Item WSMan:\localhost\MaxTimeoutms -Value 180000
Write-Host "✓ Memory and timeout limits increased" -ForegroundColor Green
Write-Host ""

# 9. Configure Windows Firewall
Write-Host "[9/10] Configuring Windows Firewall..." -ForegroundColor Yellow
# Remove existing rules if present
netsh advfirewall firewall delete rule name="WinRM HTTP" 2>$null
netsh advfirewall firewall delete rule name="WinRM HTTPS" 2>$null

# Add new rules
netsh advfirewall firewall add rule name="WinRM HTTP" dir=in action=allow protocol=TCP localport=5985 profile=any
netsh advfirewall firewall add rule name="WinRM HTTPS" dir=in action=allow protocol=TCP localport=5986 profile=any
Write-Host "✓ Firewall rules configured for WinRM (ports 5985, 5986)" -ForegroundColor Green
Write-Host ""

# 10. Restart WinRM service
Write-Host "[10/10] Restarting WinRM service..." -ForegroundColor Yellow
Restart-Service WinRM
Start-Sleep -Seconds 3
Write-Host "✓ WinRM service restarted" -ForegroundColor Green
Write-Host ""

# Verify configuration
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host "Verification" -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "WinRM Service Status:" -ForegroundColor Yellow
Get-Service WinRM | Format-Table Name, Status, StartType -AutoSize
Write-Host ""

Write-Host "WinRM Listeners:" -ForegroundColor Yellow
winrm enumerate winrm/config/listener
Write-Host ""

Write-Host "Testing local connection..." -ForegroundColor Yellow
try {
    Test-WSMan -ComputerName localhost -ErrorAction Stop | Out-Null
    Write-Host "✓ WinRM local connection test PASSED" -ForegroundColor Green
} catch {
    Write-Host "✗ WinRM local connection test FAILED: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

Write-Host "=======================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "IMPORTANT: This template is now ready for cloning." -ForegroundColor Yellow
Write-Host "WinRM will work on ANY IP address after VM deployment." -ForegroundColor Yellow
Write-Host ""
Write-Host "Key Configuration:" -ForegroundColor Cyan
Write-Host "  • Listener Address: * (all IPs)" -ForegroundColor White
Write-Host "  • TrustedHosts: * (all sources)" -ForegroundColor White
Write-Host "  • HTTP Port: 5985" -ForegroundColor White
Write-Host "  • HTTPS Port: 5986" -ForegroundColor White
Write-Host "  • Authentication: Basic, Negotiate, CredSSP" -ForegroundColor White
Write-Host "  • Service Startup: Automatic" -ForegroundColor White
Write-Host ""
