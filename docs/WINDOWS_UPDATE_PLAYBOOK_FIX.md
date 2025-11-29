# Corrección del Playbook de Actualización de Windows

## 🔴 Problemas Identificados

### 1. **Error "Access Denied" (0x80070005)**
```
Install-WindowsUpdate : Access is denied. (Exception from HRESULT: 0x80070005 (E_ACCESSDENIED))
```

**Causa**: El comando `Install-WindowsUpdate` requiere privilegios de administrador elevados. Aunque Ansible se conecta como Administrator, WinRM puede no estar ejecutando con privilegios elevados completos.

**Solución**: 
- Asegurar que el usuario de WinRM tenga permisos de administrador local
- Configurar WinRM para permitir ejecución con privilegios elevados
- Usar `ansible_winrm_transport: credssp` si es necesario para autenticación con credenciales

### 2. **Parámetros Inválidos de PSWindowsUpdate**
```
Get-WindowsUpdate : A positional parameter cannot be found that accepts argument '0'.
Get-WindowsUpdate : A parameter cannot be found that matches parameter name 'MaxDate'.
```

**Causa**: La sintaxis usada en el playbook original es incorrecta según la documentación oficial de PSWindowsUpdate.

**Parámetros INCORRECTOS**:
- `-IsInstalled 0` ❌ (no existe)
- `-IsInstalled 1` ❌ (no existe)
- `-MaxDate` ❌ (no existe en Get-WindowsUpdate)

**Parámetros CORRECTOS**:
- `Get-WindowsUpdate` sin parámetros → muestra actualizaciones **pendientes**
- `Get-WUHistory` → muestra historial de actualizaciones instaladas
- `Get-WUHistory -MaxDate (Get-Date).AddDays(-7)` → historial de últimos 7 días

## ✅ Soluciones Implementadas

### Playbook Corregido: `Update-Windows-Host-Fixed.yml`

#### Cambios Principales:

1. **Obtener actualizaciones pendientes** (CORRECTO):
```powershell
# Antes (INCORRECTO):
$updates = Get-WindowsUpdate -MicrosoftUpdate -IsInstalled 0

# Después (CORRECTO):
$updates = Get-WindowsUpdate -MicrosoftUpdate
```

2. **Obtener historial de actualizaciones** (CORRECTO):
```powershell
# Antes (INCORRECTO):
$installed = Get-WindowsUpdate -MicrosoftUpdate -IsInstalled 1 -MaxDate (Get-Date).AddDays(-1)

# Después (CORRECTO):
Get-WUHistory -MaxDate (Get-Date).AddDays(-7) -Last 20
```

3. **Instalación con reinicio automático**:
```powershell
Install-WindowsUpdate -MicrosoftUpdate -AcceptAll -AutoReboot -Verbose
```

4. **Verificar estado de reinicio**:
```powershell
$rebootStatus = Get-WURebootStatus
if ($rebootStatus.RebootRequired) {
    Write-Output "REINICIO PENDIENTE"
}
```

## 📊 Comparación de Playbooks

| Playbook | Estado | Descripción | Recomendación |
|----------|--------|-------------|---------------|
| `Update-Windows-Host.yml` | ❌ Con errores | Playbook original con sintaxis incorrecta | No usar |
| `Update-Windows-Host-Fixed.yml` | ✅ Corregido | Sintaxis correcta, 1 ciclo de actualización | **Usar este** |
| `Update-Windows-Host-Complete.yml` | ⚠️ Revisar | Múltiples ciclos, necesita corrección de sintaxis | Actualizar |

## 🎯 Recomendaciones

### Para Ejecutar el Playbook Corregido:

1. **Verificar configuración de WinRM** en el host Windows:
```powershell
# En el servidor Windows, verificar que WinRM permite Basic Auth
winrm get winrm/config/service/auth

# Debe mostrar:
# Basic = true
```

2. **Verificar credenciales** en el inventario de Ansible:
```yaml
[windows_hosts]
10.100.18.87

[windows_hosts:vars]
ansible_user=Administrator
ansible_password=tu_password
ansible_connection=winrm
ansible_winrm_transport=ntlm  # o credssp para mayor privilegio
ansible_winrm_server_cert_validation=ignore
ansible_port=5985
```

3. **Ejecutar el playbook corregido**:
```bash
ansible-playbook -i inventory.ini Update-Windows-Host-Fixed.yml
```

### Si Persiste "Access Denied":

**Opción A**: Configurar CredSSP (recomendado para mayor privilegio)
```powershell
# En el servidor Windows:
Enable-WSManCredSSP -Role Server -Force

# En el inventario de Ansible:
ansible_winrm_transport=credssp
```

**Opción B**: Usar el módulo `win_updates` nativo de Ansible (alternativa)
```yaml
- name: Instalar actualizaciones con módulo nativo
  ansible.windows.win_updates:
    category_names:
      - SecurityUpdates
      - CriticalUpdates
      - UpdateRollups
    reboot: yes
    reboot_timeout: 3600
```

## 📝 Comandos Útiles de PSWindowsUpdate

```powershell
# Listar actualizaciones pendientes
Get-WindowsUpdate -MicrosoftUpdate

# Listar solo actualizaciones de seguridad
Get-WindowsUpdate -MicrosoftUpdate -Category "Security Updates"

# Instalar actualizaciones sin reiniciar
Install-WindowsUpdate -MicrosoftUpdate -AcceptAll -IgnoreReboot

# Ver historial de actualizaciones
Get-WUHistory -Last 10

# Verificar si se requiere reinicio
Get-WURebootStatus

# Ocultar una actualización específica
Hide-WindowsUpdate -KBArticleID KB5010475

# Descargar sin instalar
Get-WindowsUpdate -Download -AcceptAll
```

## 🔍 Diagnóstico de Problemas

### Verificar si PSWindowsUpdate funciona correctamente:
```powershell
# Importar módulo
Import-Module PSWindowsUpdate

# Listar comandos disponibles
Get-Command -Module PSWindowsUpdate

# Verificar versión
Get-Module PSWindowsUpdate | Select-Object Name, Version

# Probar obtener actualizaciones
Get-WindowsUpdate -MicrosoftUpdate -Verbose
```

### Si Get-WindowsUpdate falla:
```powershell
# Resetear componentes de Windows Update
Reset-WUComponents -Verbose

# Registrar servicio de Microsoft Update
Add-WUServiceManager -ServiceID "7971f918-a847-4430-9279-4a52d1efe18d" -AddServiceFlag 7
```

## 📚 Referencias

- [Documentación oficial PSWindowsUpdate](https://www.powershellgallery.com/packages/PSWindowsUpdate)
- [Guía completa de PSWindowsUpdate](https://woshub.com/pswindowsupdate-module/)
- [Ansible Windows Modules](https://docs.ansible.com/ansible/latest/collections/ansible/windows/)
- [Configuración de WinRM para Ansible](https://docs.ansible.com/ansible/latest/user_guide/windows_setup.html)

## ✅ Próximos Pasos

1. Ejecutar `Update-Windows-Host-Fixed.yml` en el servidor Windows
2. Revisar los reportes generados en `C:\Ansible_Update\`
3. Si quedan actualizaciones pendientes, ejecutar el playbook nuevamente
4. Considerar programar ejecuciones periódicas para mantener el sistema actualizado
