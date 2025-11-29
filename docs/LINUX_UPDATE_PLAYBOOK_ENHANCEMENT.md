# Mejora del Playbook de Actualización de Linux

## Problema Identificado

El playbook original de actualización de Linux (`Update-Redhat-Host.yml`) era muy básico y **NO generaba suficiente información** antes y después de las actualizaciones, lo que dificultaba:

1. ❌ **Troubleshooting**: No había información detallada del estado del sistema antes/después
2. ❌ **Auditoría**: No se podía verificar qué actualizaciones se aplicaron exactamente
3. ❌ **Comparación**: No había forma de comparar el estado del sistema antes y después
4. ❌ **Diagnóstico**: Faltaba información crítica como kernel, servicios, memoria, disco

### Playbook Original (Básico)

```yaml
tasks:
  - Crear directorio de logs
  - Verificar actualizaciones disponibles
  - Guardar lista en log
  - Aplicar actualizaciones
  - Guardar detalle de lo actualizado
  - Mostrar log
```

**Problemas:**
- Solo mostraba lista de paquetes disponibles
- No capturaba estado del sistema
- No verificaba si se requería reinicio
- No generaba reportes separados BEFORE/AFTER
- Información insuficiente para troubleshooting

---

## Solución Implementada

### Playbook Mejorado (Completo)

El nuevo playbook genera **información detallada y completa** similar al playbook de Windows, con reportes BEFORE y AFTER.

### 📊 Estructura del Nuevo Playbook

```
┌─────────────────────────────────────────────────────────┐
│ 1. PREPARACIÓN                                          │
│    - Crear directorios (logs + reports)                 │
│    - Obtener hostname y timestamp                       │
│    - Definir nombres de archivos                        │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 2. REPORTE INICIAL (BEFORE)                             │
│    ✓ Información del sistema (OS, kernel, uptime)       │
│    ✓ Memoria y disco                                    │
│    ✓ Paquetes instalados (últimos 20)                   │
│    ✓ Kernels instalados                                 │
│    ✓ Servicios en ejecución                             │
│    ✓ Repositorios configurados                          │
│    ✓ Actualizaciones disponibles (detalladas)           │
│    ✓ Actualizaciones de seguridad                       │
│    ✓ Actualizaciones de bugfix                          │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 3. ACTUALIZACIÓN                                        │
│    - Aplicar actualizaciones con DNF                    │
│    - Guardar resultado en log                           │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 4. REINICIO (si es necesario)                           │
│    - Verificar si se requiere reinicio                  │
│    - Ejecutar reinicio con timeout de 600s              │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 5. REPORTE FINAL (AFTER)                                │
│    ✓ Información del sistema actualizada                │
│    ✓ Memoria y disco (después)                          │
│    ✓ Paquetes instalados recientemente (últimos 30)     │
│    ✓ Kernels instalados (después)                       │
│    ✓ Servicios en ejecución (después)                   │
│    ✓ Historial de actualizaciones DNF                   │
│    ✓ Verificación de actualizaciones pendientes         │
│    ✓ Resumen completo de la actualización               │
└─────────────────────────────────────────────────────────┘
```

---

## 📄 Archivos Generados

El playbook genera **3 archivos** en el servidor Linux:

### 1. Reporte ANTES (`*_BEFORE.txt`)

**Ubicación:** `/var/log/ansible_updates/reports/{hostname}_{timestamp}_BEFORE.txt`

**Contenido:**
```
================================================================================
REPORTE INICIAL - DIAGNÓSTICO COMPLETO ANTES DE ACTUALIZAR
================================================================================

Servidor: oracle-linux-01
Fecha/Hora: 2025-10-13 19:10:00
Usuario ejecutando: root
Sistema: Oracle Linux Server 9.4
Kernel: 5.14.0-427.13.1.el9_4.x86_64
Arquitectura: x86_64
Último reinicio: 2025-10-10 08:30:00
Uptime: up 3 days, 10 hours, 40 minutes

--------------------------------------------------------------------------------
INFORMACIÓN DE MEMORIA:
--------------------------------------------------------------------------------
              total        used        free      shared  buff/cache   available
Mem:           7.6Gi       2.1Gi       4.2Gi        50Mi       1.3Gi       5.2Gi
Swap:          2.0Gi          0B       2.0Gi

--------------------------------------------------------------------------------
ESPACIO EN DISCO:
--------------------------------------------------------------------------------
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1        50G   15G   35G  30% /
/dev/sda2       100G   45G   55G  45% /var

--------------------------------------------------------------------------------
PAQUETES INSTALADOS ACTUALMENTE (últimos 20):
--------------------------------------------------------------------------------
kernel-5.14.0-427.13.1.el9_4.x86_64          Mon Oct  7 10:30:00 2025
systemd-252-32.0.1.el9_4.x86_64              Mon Oct  7 10:29:55 2025
...

Total de paquetes instalados: 847

--------------------------------------------------------------------------------
VERSIÓN DEL KERNEL ACTUAL:
--------------------------------------------------------------------------------
Linux oracle-linux-01 5.14.0-427.13.1.el9_4.x86_64 #1 SMP x86_64 GNU/Linux

Kernels instalados:
kernel-5.14.0-427.13.1.el9_4.x86_64
kernel-core-5.14.0-427.13.1.el9_4.x86_64
...

--------------------------------------------------------------------------------
SERVICIOS CRÍTICOS EN EJECUCIÓN:
--------------------------------------------------------------------------------
sshd.service          loaded active running OpenSSH server daemon
httpd.service         loaded active running The Apache HTTP Server
...

--------------------------------------------------------------------------------
REPOSITORIOS CONFIGURADOS:
--------------------------------------------------------------------------------
repo id                          repo name
ol9_baseos_latest                Oracle Linux 9 BaseOS Latest (x86_64)
ol9_appstream                    Oracle Linux 9 Application Stream (x86_64)
...

================================================================================
BUSCANDO ACTUALIZACIONES DISPONIBLES...
================================================================================

✗ Total: 23 ACTUALIZACIONES DISPONIBLES

Lista detallada de paquetes a actualizar:
kernel.x86_64                    5.14.0-427.16.1.el9_4
systemd.x86_64                   252-32.0.2.el9_4
...

--------------------------------------------------------------------------------
ACTUALIZACIONES DE SEGURIDAD:
--------------------------------------------------------------------------------
ELSA-2025-12345 Important/Sec. kernel-5.14.0-427.16.1.el9_4.x86_64
ELSA-2025-12346 Moderate/Sec.  systemd-252-32.0.2.el9_4.x86_64
...

--------------------------------------------------------------------------------
ACTUALIZACIONES DE BUGFIX:
--------------------------------------------------------------------------------
ELBA-2025-54321 bugfix         curl-7.76.1-29.el9_4.x86_64
...

================================================================================
FIN DEL REPORTE INICIAL
================================================================================
```

### 2. Reporte DESPUÉS (`*_AFTER.txt`)

**Ubicación:** `/var/log/ansible_updates/reports/{hostname}_{timestamp}_AFTER.txt`

**Contenido:**
```
================================================================================
REPORTE FINAL - DIAGNÓSTICO COMPLETO DESPUÉS DE ACTUALIZAR
================================================================================

Servidor: oracle-linux-01
Fecha/Hora: 2025-10-13 19:25:00
Sistema: Oracle Linux Server 9.4
Kernel: 5.14.0-427.16.1.el9_4.x86_64  ← ACTUALIZADO
Último reinicio: 2025-10-13 19:20:00  ← REINICIADO
Uptime: up 5 minutes

--------------------------------------------------------------------------------
INFORMACIÓN DE MEMORIA (DESPUÉS):
--------------------------------------------------------------------------------
...

--------------------------------------------------------------------------------
ESPACIO EN DISCO (DESPUÉS):
--------------------------------------------------------------------------------
...

--------------------------------------------------------------------------------
PAQUETES INSTALADOS RECIENTEMENTE (últimos 30):
--------------------------------------------------------------------------------
kernel-5.14.0-427.16.1.el9_4.x86_64          Sun Oct 13 19:15:00 2025  ← NUEVO
systemd-252-32.0.2.el9_4.x86_64              Sun Oct 13 19:14:55 2025  ← NUEVO
...

Total de paquetes instalados: 850  ← AUMENTÓ

--------------------------------------------------------------------------------
VERSIÓN DEL KERNEL (DESPUÉS):
--------------------------------------------------------------------------------
Linux oracle-linux-01 5.14.0-427.16.1.el9_4.x86_64  ← KERNEL ACTUALIZADO

Kernels instalados:
kernel-5.14.0-427.16.1.el9_4.x86_64  ← NUEVO
kernel-5.14.0-427.13.1.el9_4.x86_64  ← ANTERIOR
...

--------------------------------------------------------------------------------
SERVICIOS CRÍTICOS EN EJECUCIÓN (DESPUÉS):
--------------------------------------------------------------------------------
sshd.service          loaded active running OpenSSH server daemon
httpd.service         loaded active running The Apache HTTP Server
...

--------------------------------------------------------------------------------
HISTORIAL DE ACTUALIZACIONES (últimas 50):
--------------------------------------------------------------------------------
ID     | Command line                              | Date and time    | Action(s)
-------------------------------------------------------------------------------
    15 | update                                    | 2025-10-13 19:15 | U, I, E
    14 | update                                    | 2025-10-07 10:30 | Update
...

================================================================================
VERIFICACIÓN FINAL - ACTUALIZACIONES PENDIENTES
================================================================================

✓ SISTEMA COMPLETAMENTE ACTUALIZADO

No hay actualizaciones pendientes.

================================================================================
RESUMEN DE LA ACTUALIZACIÓN
================================================================================

✓ Estado: ACTUALIZACIONES APLICADAS EXITOSAMENTE
✓ Reinicio: EJECUTADO

Archivos de reporte generados:
  - Reporte ANTES:  /var/log/ansible_updates/reports/oracle-linux-01_20251013_191000_BEFORE.txt
  - Reporte DESPUÉS: /var/log/ansible_updates/reports/oracle-linux-01_20251013_191000_AFTER.txt
  - Log de actualización: /var/log/ansible_updates/update_20251013_191000.log

================================================================================
FIN DEL REPORTE FINAL
================================================================================
```

### 3. Log de Actualización (`update_*.log`)

**Ubicación:** `/var/log/ansible_updates/update_{timestamp}.log`

**Contenido:**
```
================================================================================
RESULTADO DE LA ACTUALIZACIÓN
================================================================================
Fecha/Hora: 2025-10-13 19:15:30

✓ ACTUALIZACIONES APLICADAS EXITOSAMENTE

Paquetes actualizados:
{'installed': ['kernel-5.14.0-427.16.1.el9_4.x86_64'], 
 'updated': ['systemd-252-32.0.2.el9_4.x86_64', ...]}

================================================================================
```

---

## 🔍 Comparación: Antes vs Después

### Playbook Original

| Aspecto | Original |
|---------|----------|
| Información del sistema | ❌ No |
| Estado de memoria/disco | ❌ No |
| Kernels instalados | ❌ No |
| Servicios en ejecución | ❌ No |
| Actualizaciones de seguridad | ❌ No |
| Reporte BEFORE | ❌ No |
| Reporte AFTER | ❌ No |
| Verificación de reinicio | ❌ No |
| Reinicio automático | ❌ No |
| Historial DNF | ❌ No |
| Verificación final | ❌ No |
| **Archivos generados** | **1** |

### Playbook Mejorado

| Aspecto | Mejorado |
|---------|----------|
| Información del sistema | ✅ Sí (completa) |
| Estado de memoria/disco | ✅ Sí (antes y después) |
| Kernels instalados | ✅ Sí (antes y después) |
| Servicios en ejecución | ✅ Sí (antes y después) |
| Actualizaciones de seguridad | ✅ Sí (separadas) |
| Reporte BEFORE | ✅ Sí (detallado) |
| Reporte AFTER | ✅ Sí (detallado) |
| Verificación de reinicio | ✅ Sí (needs-restarting) |
| Reinicio automático | ✅ Sí (si es necesario) |
| Historial DNF | ✅ Sí (últimas 50) |
| Verificación final | ✅ Sí (actualizaciones pendientes) |
| **Archivos generados** | **3** |

---

## 🎯 Beneficios de la Mejora

### 1. **Troubleshooting Mejorado**
- ✅ Información completa del sistema antes y después
- ✅ Comparación fácil de kernels, paquetes, servicios
- ✅ Identificación rápida de cambios

### 2. **Auditoría Completa**
- ✅ Registro detallado de qué se actualizó
- ✅ Timestamp preciso de cada operación
- ✅ Historial de actualizaciones DNF

### 3. **Seguridad**
- ✅ Identificación de actualizaciones de seguridad
- ✅ Verificación de que se aplicaron correctamente
- ✅ Detección de actualizaciones pendientes

### 4. **Automatización**
- ✅ Reinicio automático si es necesario
- ✅ Verificación automática de needs-restarting
- ✅ Generación automática de reportes

### 5. **Consistencia con Windows**
- ✅ Mismo nivel de detalle que playbook de Windows
- ✅ Formato similar de reportes
- ✅ Experiencia uniforme para administradores

---

## 📝 Información Capturada

### Reporte BEFORE

| Categoría | Información |
|-----------|-------------|
| **Sistema** | Hostname, OS, Kernel, Arquitectura, Uptime |
| **Recursos** | Memoria (total/usado/libre), Disco (uso por filesystem) |
| **Paquetes** | Últimos 20 instalados, Total de paquetes |
| **Kernel** | Versión actual, Todos los kernels instalados |
| **Servicios** | Servicios en estado running |
| **Repositorios** | Repos configurados y habilitados |
| **Actualizaciones** | Total disponibles, Lista detallada |
| **Seguridad** | Actualizaciones de seguridad (ELSA) |
| **Bugfix** | Actualizaciones de bugfix (ELBA) |

### Reporte AFTER

| Categoría | Información |
|-----------|-------------|
| **Sistema** | Estado actualizado del sistema |
| **Recursos** | Memoria y disco después de actualizar |
| **Paquetes** | Últimos 30 instalados (muestra los nuevos) |
| **Kernel** | Versión nueva del kernel |
| **Servicios** | Servicios después del reinicio |
| **Historial** | Últimas 50 transacciones DNF |
| **Verificación** | Actualizaciones pendientes (si quedan) |
| **Resumen** | Estado final, reinicio ejecutado, archivos generados |

---

## 🚀 Uso del Playbook

### Ejecución Manual

```bash
ansible-playbook -i inventory.ini Update-Redhat-Host.yml
```

### Ejecución desde Django

1. Ir a `/deploy/playbook/`
2. Seleccionar **Target Type:** Host
3. Seleccionar **OS Family:** Linux
4. Seleccionar **Playbook:** Update-Redhat-Host
5. Seleccionar **Host:** (servidor a actualizar)
6. Click **Execute Playbook**

### Salida en Consola Ansible

El playbook muestra en tiempo real:
- ✅ Reporte inicial completo
- ✅ Progreso de la actualización
- ✅ Notificación de reinicio (si aplica)
- ✅ Reporte final completo
- ✅ Ubicación de archivos generados

---

## 📂 Ubicación de Archivos

### Directorios en el Servidor Linux

```
/var/log/ansible_updates/
├── reports/
│   ├── oracle-linux-01_20251013_191000_BEFORE.txt
│   ├── oracle-linux-01_20251013_191000_AFTER.txt
│   ├── oracle-linux-02_20251013_140000_BEFORE.txt
│   └── oracle-linux-02_20251013_140000_AFTER.txt
└── update_20251013_191000.log
```

### Formato de Nombres

```
{hostname}_{timestamp}_BEFORE.txt
{hostname}_{timestamp}_AFTER.txt
update_{timestamp}.log
```

**Ejemplo:**
```
oracle-linux-01_20251013_191000_BEFORE.txt
oracle-linux-01_20251013_191000_AFTER.txt
update_20251013_191000.log
```

---

## 🔧 Reinicio Automático

### Detección de Necesidad de Reinicio

El playbook verifica **2 condiciones**:

1. **Archivo `/var/run/reboot-required`** (si existe)
2. **Comando `needs-restarting -r`** (RC=1 significa reinicio requerido)

### Proceso de Reinicio

```yaml
- Verificar si se requiere reinicio
- Notificar al usuario (30 segundos de espera)
- Ejecutar reinicio
- Esperar 30 segundos post-reinicio
- Timeout de 600 segundos (10 minutos)
- Continuar con reporte final
```

### Casos que Requieren Reinicio

- ✅ Actualización de kernel
- ✅ Actualización de systemd
- ✅ Actualización de glibc
- ✅ Actualización de servicios críticos

---

## 🎓 Lecciones Aprendidas

### 1. **Información es Poder**
- Más información = mejor troubleshooting
- Reportes separados BEFORE/AFTER facilitan comparación
- Timestamps precisos son críticos

### 2. **Automatización Inteligente**
- Reinicio automático solo si es necesario
- Verificación de needs-restarting evita reinicios innecesarios
- Timeout de 600s previene bloqueos

### 3. **Consistencia**
- Mismo nivel de detalle que Windows
- Formato uniforme de reportes
- Experiencia consistente para administradores

### 4. **Seguridad Primero**
- Separar actualizaciones de seguridad
- Verificar que se aplicaron correctamente
- Alertar si quedan actualizaciones pendientes

---

## 📊 Estadísticas

### Playbook Original
- **Tareas:** 8
- **Archivos generados:** 1
- **Información capturada:** Básica
- **Tiempo estimado:** 5-10 minutos

### Playbook Mejorado
- **Tareas:** 25
- **Archivos generados:** 3
- **Información capturada:** Completa
- **Tiempo estimado:** 10-20 minutos (incluye reinicio)

---

## 🔮 Próximas Mejoras

1. **Comparación Automática:**
   - Script para comparar BEFORE vs AFTER
   - Resaltar diferencias automáticamente

2. **Notificaciones:**
   - Email con resumen de actualización
   - Slack/Teams notification

3. **Rollback:**
   - Snapshot automático antes de actualizar
   - Procedimiento de rollback si falla

4. **Métricas:**
   - Tiempo de actualización
   - Cantidad de paquetes actualizados
   - Tamaño de descarga

---

## 📚 Referencias

- **Playbook:** `/opt/www/app/media/playbooks/host/Update-Redhat-Host.yml`
- **Documentación DNF:** https://dnf.readthedocs.io/
- **needs-restarting:** https://man7.org/linux/man-pages/man1/needs-restarting.1.html
- **Playbook Windows (referencia):** `/opt/www/app/media/playbooks/host/Update-Windows-Host.yml`

---

**Fecha de creación:** 2025-10-13  
**Autor:** Sistema Diaken  
**Versión:** 1.0
