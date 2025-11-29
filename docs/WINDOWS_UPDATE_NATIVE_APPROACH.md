# Windows Update - Enfoque Nativo con PowerShell y COM Objects

## 🚨 Problema Crítico Identificado

**PSWindowsUpdate NO estaba instalando las actualizaciones realmente**. El comando `Install-WindowsUpdate` terminaba exitosamente pero las actualizaciones seguían apareciendo como "Pending install" en Windows Update.

## 🔄 Cambio de Enfoque

### ❌ Enfoque Anterior (PSWindowsUpdate)
```powershell
Install-WindowsUpdate -MicrosoftUpdate -AcceptAll -AutoReboot
```
**Problema**: Comando terminaba exitosamente pero NO instalaba nada.

### ✅ Nuevo Enfoque (PowerShell Nativo + COM Objects)
```powershell
# Usar Microsoft.Update.Session (COM Object nativo de Windows)
$updateSession = New-Object -ComObject Microsoft.Update.Session
$updateSearcher = $updateSession.CreateUpdateSearcher()

# Buscar actualizaciones
$searchResult = $updateSearcher.Search("IsInstalled=0 and Type='Software'")

# Descargar
$downloader = $updateSession.CreateUpdateDownloader()
$downloader.Updates = $updatesToDownload
$downloadResult = $downloader.Download()

# Instalar
$installer = $updateSession.CreateUpdateInstaller()
$installer.Updates = $updatesToInstall
$installResult = $installer.Install()
```

## 🔑 Ventajas del Enfoque Nativo

1. **✅ Control Total**: Acceso directo a la API de Windows Update
2. **✅ Sin Dependencias**: No requiere PSWindowsUpdate
3. **✅ Diagnóstico Completo**: Códigos de resultado detallados por cada actualización
4. **✅ Privilegios Elevados**: Ejecución como SYSTEM garantizada
5. **✅ Transparencia**: Visibilidad completa del proceso de descarga e instalación

## 🎯 Características Implementadas

### 1. **Elevación de Privilegios Explícita**

```yaml
vars:
  ansible_become: yes
  ansible_become_method: runas
  ansible_become_user: SYSTEM

tasks:
  - name: Instalar actualizaciones
    ansible.windows.win_shell: |
      # Script aquí
    become: yes
    become_method: runas
    become_user: SYSTEM
```

**Beneficio**: Garantiza que el script se ejecute con privilegios máximos (SYSTEM).

### 2. **Búsqueda de Actualizaciones con COM Objects**

```powershell
$updateSession = New-Object -ComObject Microsoft.Update.Session
$updateSearcher = $updateSession.CreateUpdateSearcher()
$searchResult = $updateSearcher.Search("IsInstalled=0 and Type='Software'")

foreach ($update in $searchResult.Updates) {
  Write-Output "KB: $($update.KBArticleIDs -join ',')"
  Write-Output "Título: $($update.Title)"
  Write-Output "Tamaño: $([math]::Round($update.MaxDownloadSize / 1MB, 2)) MB"
  Write-Output "Descargada: $($update.IsDownloaded)"
}
```

### 3. **Descarga Explícita**

```powershell
$downloader = $updateSession.CreateUpdateDownloader()
$downloader.Updates = $updatesToDownload
$downloadResult = $downloader.Download()

# Códigos de resultado:
# 0 = NotStarted
# 1 = InProgress
# 2 = Succeeded ✓
# 3 = SucceededWithErrors
# 4 = Failed
# 5 = Aborted
```

### 4. **Instalación con Resultado Detallado**

```powershell
$installer = $updateSession.CreateUpdateInstaller()
$installer.Updates = $updatesToInstall
$installResult = $installer.Install()

# Resultado por cada actualización
for ($i = 0; $i -lt $updatesToInstall.Count; $i++) {
  $update = $updatesToInstall.Item($i)
  $result = $installResult.GetUpdateResult($i)
  
  Write-Output "Actualización: $($update.Title)"
  Write-Output "Resultado: $($result.ResultCode)"
  Write-Output "HResult: $($result.HResult)"
}
```

### 5. **Verificación de Reinicio**

```powershell
$systemInfo = New-Object -ComObject Microsoft.Update.SystemInfo
if ($systemInfo.RebootRequired) {
  Write-Output "⚠ REINICIO REQUERIDO"
  shutdown /r /t 120 /c "Reinicio para completar actualizaciones"
}
```

### 6. **Historial de Actualizaciones**

```powershell
$updateSearcher = $updateSession.CreateUpdateSearcher()
$historyCount = $updateSearcher.GetTotalHistoryCount()
$history = $updateSearcher.QueryHistory(0, [Math]::Min(20, $historyCount))

foreach ($entry in $history) {
  Write-Output "[$($entry.Date)] $($entry.Title)"
  Write-Output "Resultado: $($entry.ResultCode)"
}
```

## 📊 Códigos de Resultado

### ResultCode (Descarga e Instalación)
- `0` = **NotStarted** - No iniciado
- `1` = **InProgress** - En progreso
- `2` = **Succeeded** ✓ - Éxito
- `3` = **SucceededWithErrors** ⚠ - Éxito con errores
- `4` = **Failed** ✗ - Falló
- `5` = **Aborted** - Abortado

### HResult (Código de Error)
Si `ResultCode != 2`, el campo `HResult` contiene el código de error específico de Windows.

Ejemplos comunes:
- `0x80070005` = Access Denied
- `0x80240022` = Update not found
- `0x8024402C` = Connection timeout

## 🔍 Diagnóstico Mejorado

El playbook ahora muestra:

### Al Inicio:
- ✅ Usuario ejecutando el script
- ✅ Si tiene privilegios de administrador
- ✅ Estado del servicio Windows Update
- ✅ Lista detallada de actualizaciones pendientes con tamaño

### Durante Instalación:
- ✅ Actualizaciones ya descargadas vs. a descargar
- ✅ Resultado de descarga con código
- ✅ Resultado de instalación por cada actualización
- ✅ HResult si hay errores

### Al Final:
- ✅ Actualizaciones pendientes (si quedan)
- ✅ Historial completo de actualizaciones
- ✅ Estado de reinicio requerido
- ✅ Tiempo de uptime del servidor

## 🚀 Ejecución

### Ejecutar el Playbook

1. Desde la interfaz web de Django
2. Seleccionar el host Windows
3. Ejecutar "Update-Windows-Host"
4. Revisar el output detallado

### Interpretar Resultados

#### ✅ Éxito Total
```
✓✓✓ DESCARGA COMPLETADA EXITOSAMENTE
✓ ÉXITO - [Nombre de actualización]
✓ ÉXITO - [Nombre de actualización]
Código de resultado: 2
```

#### ⚠️ Éxito Parcial
```
⚠ ÉXITO CON ERRORES - [Nombre de actualización]
HResult: 0x80070005
Código de resultado: 3
```

#### ❌ Fallo
```
✗ FALLÓ - [Nombre de actualización]
HResult: 0x80240022
Código de resultado: 4
```

## 🔧 Troubleshooting

### Problema: "Access Denied" (0x80070005)

**Causa**: Falta de privilegios elevados

**Solución**:
1. Verificar que el playbook use `become: yes` y `become_user: SYSTEM`
2. Configurar CredSSP en Windows:
   ```powershell
   Enable-WSManCredSSP -Role Server -Force
   ```
3. Actualizar inventario de Ansible:
   ```yaml
   ansible_winrm_transport=credssp
   ```

### Problema: Actualizaciones No Se Descargan

**Causa**: Servicio Windows Update detenido o sin acceso a internet

**Solución**:
1. Verificar servicio:
   ```powershell
   Get-Service wuauserv
   Start-Service wuauserv
   ```
2. Verificar conectividad:
   ```powershell
   Test-NetConnection update.microsoft.com -Port 443
   ```

### Problema: Instalación Falla con Código 4

**Causa**: Error específico durante instalación

**Solución**:
1. Revisar el `HResult` en el output
2. Buscar el código de error en Microsoft Docs
3. Revisar Event Viewer en Windows:
   ```
   Event Viewer > Windows Logs > System
   Filtrar por fuente: WindowsUpdateClient
   ```

## 📚 Referencias

- [IUpdateSession Interface](https://docs.microsoft.com/en-us/windows/win32/api/wuapi/nn-wuapi-iupdatesession)
- [IUpdateSearcher Interface](https://docs.microsoft.com/en-us/windows/win32/api/wuapi/nn-wuapi-iupdatesearcher)
- [IUpdateDownloader Interface](https://docs.microsoft.com/en-us/windows/win32/api/wuapi/nn-wuapi-iupdatedownloader)
- [IUpdateInstaller Interface](https://docs.microsoft.com/en-us/windows/win32/api/wuapi/nn-wuapi-iupdateinstaller)
- [Windows Update Error Codes](https://docs.microsoft.com/en-us/windows/deployment/update/windows-update-error-reference)

## ✅ Ventajas vs PSWindowsUpdate

| Característica | PSWindowsUpdate | PowerShell Nativo |
|----------------|-----------------|-------------------|
| Requiere instalación | ✗ Sí | ✓ No |
| Control de descarga | ✗ Limitado | ✓ Total |
| Códigos de error detallados | ✗ No | ✓ Sí |
| Resultado por actualización | ✗ No | ✓ Sí |
| Privilegios garantizados | ✗ No | ✓ Sí (SYSTEM) |
| Transparencia del proceso | ✗ Baja | ✓ Alta |
| **INSTALA REALMENTE** | ❌ **NO** | ✅ **SÍ** |

## 🎯 Conclusión

El enfoque nativo con COM Objects proporciona:
- ✅ **Control total** sobre el proceso de actualización
- ✅ **Diagnóstico completo** con códigos de error detallados
- ✅ **Privilegios elevados** garantizados (SYSTEM)
- ✅ **Instalación real** de actualizaciones (no solo simulación)
- ✅ **Sin dependencias** externas

Este es el método **recomendado y probado** para actualizar Windows Server con Ansible.
