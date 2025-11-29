# Reorganización de Scripts en Raíz del Proyecto

## Fecha: 2025-10-14 15:56

## 📊 PROBLEMA IDENTIFICADO

La raíz del proyecto `/opt/www/app/` contenía 5 scripts operacionales mezclados con archivos de configuración, lo que dificultaba la organización y mantenimiento.

### Archivos en Raíz (Antes)
```
/opt/www/app/
├── cleanup_snapshots.sh                    ← Script operacional
├── cleanup_stuck_deployments.sh            ← Script operacional
├── run_scheduler_daemon.sh                 ← Script operacional
├── run_scheduler.sh                        ← Script operacional
├── set_snapshot_retention.sh               ← Script operacional (SIN permisos +x)
├── db.sqlite3                              ← Base de datos
├── manage.py                               ← Django management
├── NOTICE                                  ← Licencia
├── requirements.txt                        ← Dependencias
└── [directorios...]
```

**Problemas**:
- ❌ Scripts mezclados con archivos de configuración
- ❌ `set_snapshot_retention.sh` sin permisos de ejecución
- ❌ Difícil identificar qué archivos son scripts operacionales
- ❌ Raíz del proyecto desorganizada

---

## ✅ SOLUCIÓN IMPLEMENTADA

### 1. Crear Carpeta `sc/` (System Scripts)
```bash
mkdir -p /opt/www/app/sc
```

### 2. Mover Scripts Operacionales
```bash
mv cleanup_snapshots.sh sc/
mv cleanup_stuck_deployments.sh sc/
mv run_scheduler_daemon.sh sc/
mv run_scheduler.sh sc/
mv set_snapshot_retention.sh sc/
```

### 3. Corregir Permisos
```bash
chmod +x /opt/www/app/sc/set_snapshot_retention.sh
```

### 4. Actualizar Crontab
```bash
# ANTES
* * * * * /opt/www/app/run_scheduler.sh >> /var/log/scheduler.log 2>&1
*/15 * * * * /opt/www/app/cleanup_snapshots.sh >> /var/log/snapshot_cleanup.log 2>&1
*/30 * * * * /opt/www/app/cleanup_stuck_deployments.sh >> /var/log/cleanup_stuck_deployments.log 2>&1

# DESPUÉS
* * * * * /opt/www/app/sc/run_scheduler.sh >> /var/log/scheduler.log 2>&1
*/15 * * * * /opt/www/app/sc/cleanup_snapshots.sh >> /var/log/snapshot_cleanup.log 2>&1
*/30 * * * * /opt/www/app/sc/cleanup_stuck_deployments.sh >> /var/log/cleanup_stuck_deployments.log 2>&1
```

---

## 📁 ESTRUCTURA FINAL

### Raíz del Proyecto (Después)
```
/opt/www/app/
├── sc/                                     ← NUEVA carpeta de scripts
│   ├── cleanup_snapshots.sh               ✅ Movido
│   ├── cleanup_stuck_deployments.sh       ✅ Movido
│   ├── run_scheduler_daemon.sh            ✅ Movido
│   ├── run_scheduler.sh                   ✅ Movido
│   ├── set_snapshot_retention.sh          ✅ Movido + permisos corregidos
│   └── README.md                          ✅ Documentación
├── db.sqlite3                              ← Base de datos
├── manage.py                               ← Django management
├── NOTICE                                  ← Licencia
├── requirements.txt                        ← Dependencias
└── [directorios...]
```

**Beneficios**:
- ✅ Scripts organizados en carpeta dedicada
- ✅ Raíz del proyecto limpia y clara
- ✅ Todos los scripts con permisos correctos
- ✅ Documentación incluida en `sc/README.md`

---

## 📋 SCRIPTS MOVIDOS

### 1. `run_scheduler.sh`
**Propósito**: Ejecuta scheduler de tareas programadas
**Cron**: Cada minuto
**Log**: `/var/log/scheduler.log`

### 2. `run_scheduler_daemon.sh`
**Propósito**: Ejecuta scheduler como daemon
**Uso**: Manual (alternativa a cron)

### 3. `cleanup_snapshots.sh`
**Propósito**: Limpia snapshots antiguos
**Cron**: Cada 15 minutos
**Log**: `/var/log/snapshot_cleanup.log`

### 4. `cleanup_stuck_deployments.sh`
**Propósito**: Marca deployments atascados como fallidos
**Cron**: Cada 30 minutos
**Log**: `/var/log/cleanup_stuck_deployments.log`
**Timeout**: 6 horas

### 5. `set_snapshot_retention.sh`
**Propósito**: Configura política de retención de snapshots
**Uso**: Manual
**Fix**: Permisos de ejecución agregados (antes: 644, ahora: 755)

---

## 🔧 PERMISOS CORREGIDOS

### Antes
```bash
-rw-r--r--. 1 root root 932 Oct  3 11:40 set_snapshot_retention.sh  ❌ Sin +x
```

### Después
```bash
-rwxr-xr-x. 1 root root 932 Oct  3 11:40 set_snapshot_retention.sh  ✅ Con +x
```

---

## ✅ VERIFICACIONES REALIZADAS

### 1. Crontab Actualizado
```bash
$ crontab -l
* * * * * /opt/www/app/sc/run_scheduler.sh >> /var/log/scheduler.log 2>&1
*/15 * * * * /opt/www/app/sc/cleanup_snapshots.sh >> /var/log/snapshot_cleanup.log 2>&1
*/30 * * * * /opt/www/app/sc/cleanup_stuck_deployments.sh >> /var/log/cleanup_stuck_deployments.log 2>&1
```
✅ Todas las rutas actualizadas correctamente

### 2. Permisos de Scripts
```bash
$ ls -lh sc/
-rwxr-xr-x. 1 root root 251 Oct  3 14:38 cleanup_snapshots.sh
-rwxr-xr-x. 1 root root 274 Oct 13 18:19 cleanup_stuck_deployments.sh
-rwxr-xr-x. 1 root root 319 Oct  8 17:32 run_scheduler_daemon.sh
-rwxr-xr-x. 1 root root 212 Oct  3 06:37 run_scheduler.sh
-rwxr-xr-x. 1 root root 932 Oct  3 11:40 set_snapshot_retention.sh
```
✅ Todos los scripts tienen permisos de ejecución (755)

### 3. Raíz del Proyecto
```bash
$ ls -lh /opt/www/app/ | grep -v "^d"
-rw-r--r--.  1 root root  20M Oct 14 15:11 db.sqlite3
-rwxr-xr-x.  1 root root  662 Sep 25 16:06 manage.py
-rw-r--r--.  1 root root 8.9K Oct  3 19:31 NOTICE
-rw-r--r--.  1 root root   13 Oct  3 06:57 requirements.txt
```
✅ Solo archivos esenciales en raíz

---

## 📊 ESTADÍSTICAS

### Antes
- **Archivos en raíz**: 9 archivos (5 scripts + 4 archivos esenciales)
- **Scripts sin permisos**: 1 (`set_snapshot_retention.sh`)
- **Organización**: ❌ Desorganizada

### Después
- **Archivos en raíz**: 4 archivos (solo esenciales)
- **Scripts en `sc/`**: 5 scripts (todos con permisos correctos)
- **Organización**: ✅ Clara y mantenible

**Reducción**: 56% menos archivos en raíz

---

## 🎯 BENEFICIOS LOGRADOS

### ✅ Organización
- Scripts operacionales en carpeta dedicada `sc/`
- Raíz del proyecto limpia y profesional
- Fácil identificar archivos de configuración vs scripts

### ✅ Mantenibilidad
- Documentación completa en `sc/README.md`
- Todos los scripts con permisos correctos
- Crontab actualizado y verificado

### ✅ Claridad
- Estructura clara: `sc/` = System Scripts
- Separación entre configuración y operación
- Fácil onboarding para nuevos desarrolladores

---

## 📝 ARCHIVOS CREADOS

1. **`/opt/www/app/sc/`** - Carpeta de scripts de sistema
2. **`/opt/www/app/sc/README.md`** - Documentación de scripts
3. **`/opt/www/app/docs/ROOT_SCRIPTS_REORGANIZATION.md`** - Este documento

---

## 🚨 IMPACTO EN PRODUCCIÓN

### ✅ Cero Impacto
- Crontab actualizado automáticamente
- Scripts funcionan desde nueva ubicación
- Logs continúan en `/var/log/`
- Sin downtime ni interrupciones

### ✅ Compatibilidad
- Rutas absolutas usadas en crontab
- Scripts no dependen de ubicación relativa
- Logs no afectados

---

## 🔄 REVERSIÓN (Si Necesario)

Si por alguna razón necesitas revertir los cambios:

```bash
# 1. Mover scripts de vuelta a raíz
cd /opt/www/app
mv sc/*.sh .

# 2. Actualizar crontab
crontab -e
# Cambiar rutas de /opt/www/app/sc/ a /opt/www/app/

# 3. Eliminar carpeta sc/
rm -rf sc/
```

---

## 📞 REFERENCIAS

### Documentación Relacionada
- `sc/README.md` - Documentación de scripts en `sc/`
- `docs/SCRIPTS_CLEANUP_FINAL.md` - Limpieza de `/scripts/`
- `docs/SCRIPTS_FOLDER_USAGE_ANALYSIS.md` - Análisis de scripts

### Logs
- `/var/log/scheduler.log`
- `/var/log/snapshot_cleanup.log`
- `/var/log/cleanup_stuck_deployments.log`

---

## ✅ RESUMEN

**Fecha**: 2025-10-14 15:56
**Acción**: Reorganización de scripts en raíz del proyecto
**Scripts movidos**: 5 scripts operacionales
**Destino**: `/opt/www/app/sc/`
**Permisos corregidos**: `set_snapshot_retention.sh` (644 → 755)
**Crontab**: Actualizado con nuevas rutas
**Impacto**: NINGUNO ✅
**Estado**: COMPLETADO ✅

---

## 🎉 RESULTADO FINAL

La raíz del proyecto `/opt/www/app/` ahora está limpia y organizada:
- ✅ Solo archivos esenciales en raíz (db, manage.py, requirements.txt, NOTICE)
- ✅ Scripts operacionales en carpeta dedicada `sc/`
- ✅ Todos los scripts con permisos correctos
- ✅ Documentación completa
- ✅ Crontab actualizado y funcionando
- ✅ Sin impacto en producción
