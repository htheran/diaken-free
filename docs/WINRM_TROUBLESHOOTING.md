# WinRM Troubleshooting Guide

## Error: "Connection reset by peer" con Ansible

### Síntomas
```
fatal: [10.100.5.87]: UNREACHABLE! => {
  "msg": "ntlm: ('Connection aborted.', ConnectionResetError(104, 'Connection reset by peer'))"
}
```

---

## Causas Comunes y Soluciones

### 1. **Inventario sin credenciales WinRM**

**Problema:** El playbook no tiene las variables de conexión WinRM.

**Solución:** Crear un inventario con las credenciales:

```ini
[windows_hosts]
10.100.5.87

[windows_hosts:vars]
ansible_connection=winrm
ansible_user=Administrator
ansible_password=TuPassword
ansible_winrm_transport=ntlm
ansible_winrm_server_cert_validation=ignore
ansible_port=5985
```

**Ejecutar playbook con inventario:**
```bash
ansible-playbook -i inventory.ini playbook.yml
```

---

### 2. **Tipo de autenticación incorrecto**

**Problema:** El servidor no acepta el tipo de autenticación configurado.

**Solución:** Probar diferentes tipos de autenticación:

```bash
# Probar NTLM (más común)
ansible_winrm_transport=ntlm

# Probar Basic (requiere AllowUnencrypted=true en servidor)
ansible_winrm_transport=basic

# Probar Negotiate (Kerberos/NTLM)
ansible_winrm_transport=negotiate

# Probar CredSSP (más seguro, requiere configuración)
ansible_winrm_transport=credssp
```

**Script de prueba:**
```bash
python /opt/www/app/scripts/test_winrm_connection.py 10.100.5.87 Administrator 'Password' all
```

---

### 3. **WinRM Listener no configurado para Address=***

**Problema:** El listener está atado a una IP específica, no a todas las IPs.

**Verificar en Windows:**
```powershell
winrm enumerate winrm/config/listener
```

**Debe mostrar:**
```
Address = *
```

**Si muestra una IP específica, corregir:**
```powershell
# Eliminar listeners existentes
Get-ChildItem WSMan:\localhost\Listener | Remove-Item -Recurse -Force

# Crear listener para todas las IPs
winrm create winrm/config/Listener?Address=*+Transport=HTTP

# Verificar
winrm enumerate winrm/config/listener
```

**O usar el script de configuración:**
```powershell
# En la VM Windows
C:\scripts\windows_template_setup.ps1
```

---

### 4. **Autenticación Basic no habilitada**

**Problema:** El servidor no acepta autenticación Basic.

**Verificar en Windows:**
```powershell
winrm get winrm/config/service/auth
```

**Debe mostrar:**
```
Basic = true
```

**Si está en false, habilitar:**
```powershell
Set-Item WSMan:\localhost\Service\Auth\Basic -Value $true
```

---

### 5. **AllowUnencrypted no habilitado**

**Problema:** El servidor no acepta tráfico HTTP sin encriptar.

**Verificar en Windows:**
```powershell
winrm get winrm/config/service
```

**Debe mostrar:**
```
AllowUnencrypted = true
```

**Si está en false, habilitar:**
```powershell
Set-Item WSMan:\localhost\Service\AllowUnencrypted -Value $true
```

---

### 6. **Firewall bloqueando puerto 5985**

**Problema:** El firewall de Windows bloquea el puerto WinRM.

**Verificar regla de firewall:**
```powershell
Get-NetFirewallRule -DisplayName "*WinRM*" | Select-Object DisplayName, Enabled
```

**Habilitar regla:**
```powershell
Enable-NetFirewallRule -DisplayName "Windows Remote Management (HTTP-In)"
```

**O crear regla manualmente:**
```powershell
New-NetFirewallRule -DisplayName "WinRM HTTP" -Direction Inbound -LocalPort 5985 -Protocol TCP -Action Allow
```

---

### 7. **Servicio WinRM no iniciado**

**Problema:** El servicio WinRM no está corriendo.

**Verificar en Windows:**
```powershell
Get-Service WinRM
```

**Iniciar servicio:**
```powershell
Start-Service WinRM
Set-Service WinRM -StartupType Automatic
```

---

### 8. **TrustedHosts no configurado**

**Problema:** El servidor no confía en el cliente.

**Verificar en Windows:**
```powershell
Get-Item WSMan:\localhost\Client\TrustedHosts
```

**Configurar para aceptar todos:**
```powershell
Set-Item WSMan:\localhost\Client\TrustedHosts -Value "*" -Force
```

---

## Diagnóstico Rápido

### Desde el servidor Ansible (Linux):

**1. Verificar conectividad de red:**
```bash
ping 10.100.5.87
telnet 10.100.5.87 5985
```

**2. Probar conexión WinRM con Python:**
```bash
python /opt/www/app/scripts/test_winrm_connection.py 10.100.5.87 Administrator 'Password' all
```

**3. Probar con Ansible directamente:**
```bash
ansible windows_hosts -i inventory.ini -m win_ping
```

---

### Desde el servidor Windows:

**1. Verificar configuración completa:**
```powershell
# Ejecutar script de configuración
C:\scripts\windows_template_setup.ps1

# O verificar manualmente
winrm quickconfig
winrm enumerate winrm/config/listener
winrm get winrm/config/service
winrm get winrm/config/service/auth
```

**2. Ver logs de WinRM:**
```powershell
Get-EventLog -LogName Microsoft-Windows-WinRM/Operational -Newest 20
```

---

## Configuración Completa Recomendada (Windows)

**Script completo para configurar WinRM:**

```powershell
# 1. Habilitar WinRM
Enable-PSRemoting -Force

# 2. Configurar servicio
Set-Service WinRM -StartupType Automatic
Start-Service WinRM

# 3. Eliminar listeners existentes
Get-ChildItem WSMan:\localhost\Listener | Remove-Item -Recurse -Force

# 4. Crear listener para todas las IPs
winrm create winrm/config/Listener?Address=*+Transport=HTTP

# 5. Configurar autenticación
Set-Item WSMan:\localhost\Service\Auth\Basic -Value $true
Set-Item WSMan:\localhost\Service\Auth\Negotiate -Value $true

# 6. Permitir tráfico sin encriptar
Set-Item WSMan:\localhost\Service\AllowUnencrypted -Value $true

# 7. Configurar TrustedHosts
Set-Item WSMan:\localhost\Client\TrustedHosts -Value "*" -Force

# 8. Configurar firewall
Enable-NetFirewallRule -DisplayName "Windows Remote Management (HTTP-In)"

# 9. Reiniciar servicio
Restart-Service WinRM

# 10. Verificar
winrm enumerate winrm/config/listener
Write-Host "WinRM configurado correctamente" -ForegroundColor Green
```

---

## Checklist de Verificación

- [ ] Servicio WinRM iniciado y en automático
- [ ] Listener configurado con `Address = *`
- [ ] Autenticación Basic habilitada
- [ ] AllowUnencrypted = true
- [ ] TrustedHosts configurado
- [ ] Firewall permite puerto 5985
- [ ] Credenciales correctas en inventario
- [ ] Tipo de autenticación correcto (ntlm/basic/negotiate)
- [ ] Red accesible (ping funciona)
- [ ] Puerto 5985 accesible (telnet funciona)

---

## Archivos de Referencia

- **Inventario de ejemplo:** `/opt/www/app/ansible/inventory_windows_example.ini`
- **Script de prueba:** `/opt/www/app/scripts/test_winrm_connection.py`
- **Script de configuración Windows:** `/opt/www/app/scripts/windows_template_setup.ps1`
- **Playbook de aprovisionamiento:** `/opt/www/app/ansible/provision_windows_vm.yml`

---

## Contacto y Soporte

Si después de seguir esta guía el problema persiste:

1. Revisar logs de WinRM en Windows
2. Revisar logs de Ansible con `-vvv`
3. Verificar políticas de grupo de Windows
4. Consultar documentación oficial de Ansible WinRM
