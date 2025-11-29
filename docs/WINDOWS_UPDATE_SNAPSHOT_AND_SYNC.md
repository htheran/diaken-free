# Windows Update - Snapshot Automático y Sincronización Forzada

## 🔄 Cambios Implementados

### 1. **Snapshot Automático Antes de Actualizar**

El playbook `Update-Windows-Host.yml` ahora **crea automáticamente un snapshot** antes de instalar actualizaciones.

#### Variables Requeridas

Para que el snapshot funcione, debes proporcionar las credenciales de vCenter al ejecutar el playbook:

```yaml
vcenter_hostname: "vcenter.example.com"
vcenter_username: "administrator@vsphere.local"
vcenter_password: "password"
datacenter: "Datacenter1"  # Opcional
vm_folder: "/vm/folder"     # Opcional
```

#### Cómo Ejecutar con Snapshot

**Opción 1: Desde línea de comandos**
```bash
ansible-playbook -i inventory.ini \
  /opt/www/app/media/playbooks/host/Update-Windows-Host.yml \
  -e "vcenter_hostname=vcenter.example.com" \
  -e "vcenter_username=administrator@vsphere.local" \
  -e "vcenter_password=YourPassword" \
  -e "datacenter=Datacenter1"
```

**Opción 2: Desde la interfaz web**

Necesitas modificar la vista de Django para pasar las variables de vCenter:

```python
# En deploy/views.py o donde ejecutes el playbook
extra_vars = {
    'vcenter_hostname': settings.VCENTER_HOST,
    'vcenter_username': settings.VCENTER_USER,
    'vcenter_password': settings.VCENTER_PASSWORD,
    'datacenter': 'Datacenter1',
    'vm_folder': '/vm/Production'
}
```

#### Comportamiento del Snapshot

- ✅ Se crea **antes** de instalar actualizaciones
- ✅ Nombre automático: `Pre-Update-YYYY-MM-DD-HHMMSS`
- ✅ Descripción incluye fecha y hora
- ✅ Si vCenter no está configurado, **se omite** (no falla el playbook)
- ✅ Si falla la creación, **continúa** con las actualizaciones (ignore_errors: yes)

#### Verificar Snapshot Creado

Después de ejecutar el playbook, verifica en vCenter:
1. Selecciona la VM
2. Ve a la pestaña "Snapshots"
3. Deberías ver el snapshot `Pre-Update-YYYY-MM-DD-HHMMSS`

---

### 2. **Nuevo Playbook: Force-Windows-Update-Sync.yml**

Este playbook **fuerza la sincronización** con Windows Update y muestra **exactamente** qué actualizaciones están pendientes.

#### ¿Cuándo Usar Este Playbook?

- Cuando el playbook principal reporta "No hay actualizaciones" pero Windows Update GUI muestra actualizaciones pendientes
- Para diagnosticar por qué las actualizaciones no se detectan
- Para forzar una sincronización completa con los servidores de Microsoft

#### Qué Hace Este Playbook

**Paso 1: Limpieza**
- Detiene servicios de Windows Update
- Limpia el caché de `C:\Windows\SoftwareDistribution\Download`
- Reinicia servicios

**Paso 2: Detección Forzada**
- Ejecuta `wuauclt /detectnow`
- Ejecuta `usoclient StartScan` (Windows 10/Server 2016+)
- Espera 30 segundos para completar la detección

**Paso 3: Búsqueda con COM Objects**
- Usa `Microsoft.Update.Session` con búsqueda **en línea** (sin caché)
- Muestra detalles completos de cada actualización:
  - Título y KB
  - Tipo (Software/Driver)
  - Estado de descarga e instalación
  - EULA aceptada
  - Tamaño
  - Requisitos de reinicio
- Agrupa actualizaciones por categoría

**Paso 4: Comparación con GUI**
- Busca actualizaciones **visibles** (lo que Windows Update GUI muestra)
- Busca actualizaciones **ocultas**
- Permite identificar discrepancias

#### Cómo Ejecutar

```bash
ansible-playbook -i inventory.ini \
  /opt/www/app/media/playbooks/host/Force-Windows-Update-Sync.yml
```

#### Output Esperado

```
================================================================================
PASO 1: DETENER SERVICIOS Y LIMPIAR CACHÉ
================================================================================

Deteniendo servicio: wuauserv
  ✓ Detenido
Deteniendo servicio: bits
  ✓ Detenido

Limpiando caché de Windows Update...
  ✓ Caché limpiado: C:\Windows\SoftwareDistribution\Download

Iniciando servicio: wuauserv
  ✓ Iniciado
Iniciando servicio: bits
  ✓ Iniciado

================================================================================
PASO 2: FORZAR DETECCIÓN DE ACTUALIZACIONES
================================================================================

Método 1: wuauclt /detectnow
  ✓ Ejecutado

Método 2: usoclient StartScan
  ✓ Ejecutado

✓ Detección completada

================================================================================
PASO 3: BÚSQUEDA CON COM OBJECTS
================================================================================

Buscando actualizaciones en línea (sin caché)...
Criterio: IsInstalled=0

================================================================================
RESULTADO DE LA BÚSQUEDA
================================================================================
Total encontradas: 6

--------------------------------------------------------------------------------
DETALLES DE CADA ACTUALIZACIÓN:
--------------------------------------------------------------------------------

[1] Security Intelligence Update for Microsoft Defender Antivirus
    KB: 2267602
    Tipo: 1 (1=Software, 2=Driver)
    Descargada: True
    Instalada: False
    Oculta: False
    EULA Aceptada: True
    Tamaño: 50.5 MB
    Requiere reinicio: False
    Puede pedir input: False

[2] Update for Microsoft Defender Antivirus antimalware platform
    KB: 4052623
    Tipo: 1 (1=Software, 2=Driver)
    Descargada: True
    Instalada: False
    Oculta: False
    EULA Aceptada: True
    Tamaño: 12.3 MB
    Requiere reinicio: True
    Puede pedir input: False

...

================================================================================
RESUMEN POR CATEGORÍA
================================================================================

Definition Updates : 2 actualizaciones
Security Updates : 3 actualizaciones
Drivers : 1 actualizaciones

================================================================================
PASO 4: VERIFICACIÓN CON WUA API (lo que ve Windows Update GUI)
================================================================================

Buscando actualizaciones visibles (no ocultas)...
Actualizaciones visibles en GUI: 6

  - Security Intelligence Update for Microsoft Defender Antivirus
  - Update for Microsoft Defender Antivirus antimalware platform
  - 2025-09 Cumulative Update for .NET Framework
  - 2025-09 Cumulative Update for Microsoft server operating system
  - Windows Malicious Software Removal Tool
  - Broadcom Inc. - Net - 1.9.20.0

Buscando actualizaciones ocultas...
Actualizaciones ocultas: 0
```

---

## 🎯 Flujo de Trabajo Recomendado

### Escenario 1: Actualización Normal con Snapshot

```bash
# 1. Ejecutar playbook principal con snapshot
ansible-playbook -i inventory.ini \
  /opt/www/app/media/playbooks/host/Update-Windows-Host.yml \
  -e "vcenter_hostname=vcenter.example.com" \
  -e "vcenter_username=admin@vsphere.local" \
  -e "vcenter_password=pass"

# 2. Verificar en vCenter que el snapshot se creó

# 3. Si todo va bien, eliminar el snapshot después de validar
```

### Escenario 2: Diagnóstico de Actualizaciones No Detectadas

```bash
# 1. Ejecutar sincronización forzada
ansible-playbook -i inventory.ini \
  /opt/www/app/media/playbooks/host/Force-Windows-Update-Sync.yml

# 2. Revisar el output para ver qué actualizaciones se detectan

# 3. Si ahora se detectan actualizaciones, ejecutar el playbook principal
ansible-playbook -i inventory.ini \
  /opt/www/app/media/playbooks/host/Update-Windows-Host.yml \
  -e "vcenter_hostname=vcenter.example.com" \
  -e "vcenter_username=admin@vsphere.local" \
  -e "vcenter_password=pass"
```

### Escenario 3: Actualizaciones Persistentemente Pendientes

```bash
# 1. Ejecutar sincronización forzada para identificar actualizaciones
ansible-playbook -i inventory.ini \
  /opt/www/app/media/playbooks/host/Force-Windows-Update-Sync.yml

# 2. Si son solo actualizaciones de antivirus, ocultarlas
ansible-playbook -i inventory.ini \
  /opt/www/app/media/playbooks/host/Hide-Problematic-Updates.yml

# 3. Si son actualizaciones críticas, ejecutar reset
ansible-playbook -i inventory.ini \
  /opt/www/app/media/playbooks/host/Reset-Windows-Update.yml

# 4. Ejecutar playbook principal nuevamente
ansible-playbook -i inventory.ini \
  /opt/www/app/media/playbooks/host/Update-Windows-Host.yml \
  -e "vcenter_hostname=vcenter.example.com" \
  -e "vcenter_username=admin@vsphere.local" \
  -e "vcenter_password=pass"
```

---

## 🔧 Integración con Django

Para integrar el snapshot en la interfaz web, modifica la vista que ejecuta el playbook:

### Ejemplo de Integración

```python
# En deploy/views.py o tu vista correspondiente

from django.conf import settings
import subprocess
import json

def execute_windows_update_playbook(request):
    # Obtener credenciales de vCenter desde settings
    vcenter_host = settings.VCENTER_HOST
    vcenter_user = settings.VCENTER_USER
    vcenter_password = settings.VCENTER_PASSWORD
    
    # Preparar variables extra para Ansible
    extra_vars = {
        'vcenter_hostname': vcenter_host,
        'vcenter_username': vcenter_user,
        'vcenter_password': vcenter_password,
        'datacenter': 'Datacenter1',  # Ajustar según tu entorno
        'vm_folder': '/vm/Production'  # Ajustar según tu entorno
    }
    
    # Construir comando ansible-playbook
    cmd = [
        'ansible-playbook',
        '-i', '/path/to/inventory.ini',
        '/opt/www/app/media/playbooks/host/Update-Windows-Host.yml',
        '-e', json.dumps(extra_vars)
    ]
    
    # Ejecutar playbook
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Procesar resultado
    if result.returncode == 0:
        return JsonResponse({
            'status': 'success',
            'message': 'Actualizaciones instaladas y snapshot creado',
            'output': result.stdout
        })
    else:
        return JsonResponse({
            'status': 'error',
            'message': 'Error al ejecutar playbook',
            'error': result.stderr
        }, status=500)
```

### Configuración en settings.py

```python
# En diaken/settings.py

# Credenciales de vCenter para snapshots
VCENTER_HOST = os.environ.get('VCENTER_HOST', 'vcenter.example.com')
VCENTER_USER = os.environ.get('VCENTER_USER', 'administrator@vsphere.local')
VCENTER_PASSWORD = os.environ.get('VCENTER_PASSWORD', '')
```

---

## 📝 Notas Importantes

### Sobre el Snapshot

1. **Requisitos:**
   - Módulo `community.vmware` instalado: `ansible-galaxy collection install community.vmware`
   - Credenciales de vCenter válidas
   - Permisos en vCenter para crear snapshots

2. **Limitaciones:**
   - El snapshot se crea en el **host de Ansible** (delegate_to: localhost)
   - Requiere conectividad desde el host de Ansible a vCenter
   - No funciona si la VM no está en vCenter (VMs físicas o en otros hypervisors)

3. **Gestión de Snapshots:**
   - Los snapshots **consumen espacio en disco**
   - Recuerda **eliminar snapshots antiguos** después de validar las actualizaciones
   - Considera implementar una política de retención de snapshots

### Sobre la Sincronización Forzada

1. **Búsqueda en Línea:**
   - El playbook usa `$updateSearcher.Online = $true` para forzar búsqueda en servidores de Microsoft
   - Esto **ignora el caché local** y obtiene el estado más actualizado

2. **Tiempo de Ejecución:**
   - La sincronización forzada puede tardar **2-3 minutos**
   - Incluye esperas de 15-30 segundos para que Windows Update complete la detección

3. **Interpretación de Resultados:**
   - Si el Paso 3 muestra actualizaciones pero el playbook principal no las detecta, hay un problema de caché
   - Si el Paso 4 muestra actualizaciones visibles diferentes a las del Paso 3, algunas están ocultas

---

## 🎓 Referencias

- [Ansible vmware_guest_snapshot Module](https://docs.ansible.com/ansible/latest/collections/community/vmware/vmware_guest_snapshot_module.html)
- [Windows Update Agent API](https://docs.microsoft.com/en-us/windows/win32/api/_wua/)
- [IUpdateSearcher.Online Property](https://docs.microsoft.com/en-us/windows/win32/api/wuapi/nf-wuapi-iupdatesearcher-get_online)
