# Análisis de Scripts en el Proyecto

## Fecha: 2025-10-14

## Scripts en la Raíz del Proyecto

### 📊 Resumen Ejecutivo

| Script | Tamaño | En Uso | Duplicado | Acción Recomendada |
|--------|--------|--------|-----------|-------------------|
| `cleanup_snapshots.sh` | 251 B | ✅ SÍ | ❌ NO | **MANTENER en raíz** |
| `cleanup_stuck_deployments.sh` | 274 B | ✅ SÍ | ❌ NO | **MANTENER en raíz** |
| `compare_winrm_configs.py` | 4.4 KB | ❌ NO | ❌ NO | **MOVER a scripts/** |
| `run_scheduler.sh` | 212 B | ✅ SÍ | ❌ NO | **MANTENER en raíz** |
| `run_scheduler_daemon.sh` | 319 B | ✅ SÍ | ❌ NO | **MANTENER en raíz** |
| `set_snapshot_retention.sh` | 932 B | ⚠️ MANUAL | ❌ NO | **MANTENER en raíz** |
| `test_winrm_auth_types.sh` | 2.0 KB | ❌ NO | ❌ NO | **MOVER a scripts/** |
| `test_winrm_connection.py` | 3.6 KB | ⚠️ PARCIAL | ✅ SÍ | **ELIMINAR (usar scripts/)** |

---

## 📝 Análisis Detallado

### ✅ Scripts en USO - MANTENER en Raíz

#### 1. `cleanup_snapshots.sh`
- **Estado**: ✅ EN USO
- **Propósito**: Limpieza automática de snapshots antiguos
- **Uso**: Crontab configurado
- **Ruta esperada**: `/opt/www/app/cleanup_snapshots.sh`
- **Recomendación**: **MANTENER en raíz** (referenciado en crontab)

#### 2. `cleanup_stuck_deployments.sh`
- **Estado**: ✅ EN USO
- **Propósito**: Limpieza de deployments atascados
- **Uso**: 
  - Crontab configurado
  - Referenciado en template HTML: `templates/history/cleanup_stuck_deployments.html`
- **Ruta esperada**: `/opt/www/app/cleanup_stuck_deployments.sh`
- **Recomendación**: **MANTENER en raíz** (referenciado en múltiples lugares)

#### 3. `run_scheduler.sh`
- **Estado**: ✅ EN USO
- **Propósito**: Ejecutar scheduler de tareas programadas
- **Uso**: Crontab configurado (cada minuto)
- **Ruta esperada**: `/opt/www/app/run_scheduler.sh`
- **Recomendación**: **MANTENER en raíz** (script crítico del sistema)

#### 4. `run_scheduler_daemon.sh`
- **Estado**: ✅ EN USO
- **Propósito**: Ejecutar scheduler como daemon
- **Uso**: Proceso en background con nohup
- **Ruta esperada**: `/opt/www/app/run_scheduler_daemon.sh`
- **Recomendación**: **MANTENER en raíz** (script crítico del sistema)

#### 5. `set_snapshot_retention.sh`
- **Estado**: ⚠️ USO MANUAL
- **Propósito**: Configurar retención de snapshots
- **Uso**: Script de utilidad manual
- **Ruta esperada**: `/opt/www/app/set_snapshot_retention.sh`
- **Recomendación**: **MANTENER en raíz** (herramienta de administración)

---

### ❌ Scripts NO en Uso - MOVER a scripts/

#### 6. `compare_winrm_configs.py`
- **Estado**: ❌ NO EN USO
- **Propósito**: Comparar configuraciones WinRM
- **Referencias**: Ninguna en el código
- **Tamaño**: 4.4 KB
- **Recomendación**: **MOVER a `/opt/www/app/scripts/`**
- **Razón**: Script de diagnóstico/testing, no usado en producción

#### 7. `test_winrm_auth_types.sh`
- **Estado**: ❌ NO EN USO
- **Propósito**: Probar diferentes tipos de autenticación WinRM
- **Referencias**: Ninguna en el código
- **Tamaño**: 2.0 KB
- **Recomendación**: **MOVER a `/opt/www/app/scripts/`**
- **Razón**: Script de testing, no usado en producción

---

### 🔄 Scripts DUPLICADOS - ELIMINAR de Raíz

#### 8. `test_winrm_connection.py` (RAÍZ)
- **Estado**: ⚠️ PARCIAL / DUPLICADO
- **Propósito**: Probar conexión WinRM
- **Duplicado en**: `/opt/www/app/scripts/test_winrm_connection.py`
- **Diferencias**: 
  - Versión raíz: Usa Django setup (más antigua)
  - Versión scripts/: Más completa, standalone (más nueva)
- **Referencias activas**: 
  - ✅ `scripts/set_host_windows_credentials.py` → usa `/scripts/test_winrm_connection.py`
  - ✅ `scripts/check_host_credentials.py` → usa `/scripts/test_winrm_connection.py`
  - ✅ `scripts/test_winrm_credentials.sh` → usa `/scripts/test_winrm_connection.py`
  - ⚠️ `compare_winrm_configs.py` (raíz) → referencia genérica
- **Recomendación**: **ELIMINAR de raíz** (usar solo la versión en scripts/)
- **Razón**: La versión en scripts/ es la activa y más completa

---

## 📋 Scripts en `/opt/www/app/scripts/` (37 archivos)

### Categorías:

#### 🔧 Scripts de Administración (EN USO)
- `check_host_credentials.py` - Verificar credenciales de hosts
- `set_host_windows_credentials.py` - Configurar credenciales Windows
- `show_windows_credential.py` - Mostrar credenciales
- `update_windows_credential_password.py` - Actualizar passwords
- `fix_windows_host.py` - Reparar configuración Windows

#### 🧪 Scripts de Testing WinRM (DESARROLLO)
- `test_winrm_connection.py` ✅ (VERSIÓN ACTIVA)
- `test_winrm_credentials.sh`
- `test_winrm_custom_headers.py`
- `test_winrm_debug.py`
- `test_winrm_http10.py`
- `test_winrm_raw.py`
- `test_winrm_simple.py`
- `test_windows_winrm.sh`

#### 📸 Scripts de Testing Snapshots (DESARROLLO)
- `test_cleanup_windows.py`
- `test_create_snapshot.py`
- `test_delete_snapshot.py`
- `test_find_vm.py`
- `test_full_snapshot_lifecycle.py`
- `test_vm_snapshots.py`

#### 🪟 Scripts PowerShell (DEPLOYMENT)
- `diagnose_winrm.ps1`
- `diagnose_winrm_full.ps1`
- `verify_winrm_config.ps1`
- `windows_template_setup.ps1`
- `winrm_post_provision_fix.ps1`

#### 🐍 Django App Files
- `__init__.py`, `admin.py`, `apps.py`, `forms.py`, `models.py`, `urls.py`, `views.py`
- `management/` - Django management commands
- `migrations/` - Django migrations

---

## 🎯 Recomendaciones Finales

### Opción 1: Limpieza Conservadora (RECOMENDADA)
```bash
# Mover scripts de testing/diagnóstico a scripts/
mv /opt/www/app/compare_winrm_configs.py /opt/www/app/scripts/
mv /opt/www/app/test_winrm_auth_types.sh /opt/www/app/scripts/

# Eliminar duplicado (mantener solo versión en scripts/)
rm /opt/www/app/test_winrm_connection.py

# Mantener en raíz (scripts críticos del sistema)
# - cleanup_snapshots.sh
# - cleanup_stuck_deployments.sh
# - run_scheduler.sh
# - run_scheduler_daemon.sh
# - set_snapshot_retention.sh
```

**Resultado**: 
- ✅ 5 scripts críticos en raíz (necesarios para crontab/sistema)
- ✅ 39 scripts en `/scripts/` (organizados)
- ✅ 0 duplicados

---

### Opción 2: Limpieza Agresiva (SOLO SI CONFIRMAS)
```bash
# Igual que Opción 1, pero además:

# Eliminar scripts de testing antiguos si no se usan
rm /opt/www/app/scripts/test_winrm_custom_headers.py
rm /opt/www/app/scripts/test_winrm_debug.py
rm /opt/www/app/scripts/test_winrm_http10.py
rm /opt/www/app/scripts/test_winrm_raw.py
rm /opt/www/app/scripts/test_winrm_simple.py

# Consolidar scripts de testing de snapshots
# (revisar si aún son necesarios)
```

**⚠️ ADVERTENCIA**: Solo hacer esto si confirmas que esos scripts de testing ya no son necesarios.

---

### Opción 3: Solo Documentar (NO CAMBIAR NADA)
- Crear este documento de análisis
- Mantener estructura actual
- Usar como referencia futura

---

## 📊 Estructura Recomendada Final

```
/opt/www/app/
├── cleanup_snapshots.sh              ← MANTENER (crontab)
├── cleanup_stuck_deployments.sh      ← MANTENER (crontab + HTML)
├── run_scheduler.sh                  ← MANTENER (crontab)
├── run_scheduler_daemon.sh           ← MANTENER (daemon)
├── set_snapshot_retention.sh         ← MANTENER (admin tool)
├── manage.py                         ← Django
├── requirements.txt                  ← Django
└── scripts/                          ← TODO LO DEMÁS
    ├── compare_winrm_configs.py      ← MOVER AQUÍ
    ├── test_winrm_auth_types.sh      ← MOVER AQUÍ
    ├── test_winrm_connection.py      ← YA EXISTE (mantener)
    └── ... (37 archivos existentes)
```

---

## 🔍 Verificación de Referencias

### Scripts con Referencias Activas:
1. ✅ `cleanup_snapshots.sh` → Crontab
2. ✅ `cleanup_stuck_deployments.sh` → Crontab + HTML template
3. ✅ `run_scheduler.sh` → Crontab
4. ✅ `run_scheduler_daemon.sh` → Daemon process
5. ✅ `scripts/test_winrm_connection.py` → 3 scripts Python + 1 script Bash

### Scripts SIN Referencias:
1. ❌ `compare_winrm_configs.py` → 0 referencias
2. ❌ `test_winrm_auth_types.sh` → 0 referencias
3. ⚠️ `test_winrm_connection.py` (raíz) → Solo referencia indirecta obsoleta

---

## ✅ Comandos para Ejecutar (Opción 1 - Recomendada)

```bash
# 1. Mover scripts de testing a carpeta scripts/
mv /opt/www/app/compare_winrm_configs.py /opt/www/app/scripts/

mv /opt/www/app/test_winrm_auth_types.sh /opt/www/app/scripts/

# 2. Eliminar duplicado obsoleto
rm /opt/www/app/test_winrm_connection.py

# 3. Verificar que todo funciona
ls -lh /opt/www/app/*.sh
ls -lh /opt/www/app/*.py
ls -lh /opt/www/app/scripts/ | grep test_winrm
```

**Total de cambios**: 3 archivos movidos/eliminados, 5 scripts críticos mantenidos en raíz.
