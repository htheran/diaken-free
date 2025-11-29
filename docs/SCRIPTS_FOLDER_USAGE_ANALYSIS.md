# Análisis de Uso de Scripts en /opt/www/app/scripts/

## Fecha: 2025-10-14 15:42

## 📊 RESUMEN EJECUTIVO

**Total de archivos en scripts/**: 37 archivos
- **Archivos Django (app)**: 11 archivos (admin.py, apps.py, forms.py, models.py, urls.py, views.py, etc.)
- **Scripts operacionales**: 26 archivos (.py, .sh, .ps1)

---

## 🔍 CLASIFICACIÓN POR USO

### ✅ SCRIPTS ACTIVAMENTE USADOS (11 scripts)

#### 1. Gestión de Credenciales Windows (4 scripts)

| Script | Uso | Referencias |
|--------|-----|-------------|
| `check_host_credentials.py` | ✅ ACTIVO | Referenciado por `fix_windows_host.py` |
| `set_host_windows_credentials.py` | ✅ ACTIVO | Tool de administración manual |
| `show_windows_credential.py` | ✅ ACTIVO | Tool de administración manual |
| `update_windows_credential_password.py` | ✅ ACTIVO | Tool de administración manual |

**Propósito**: Gestión de credenciales Windows en base de datos
**Uso**: Manual por administradores para configurar/verificar credenciales
**Impacto si se eliminan**: ❌ CRÍTICO - Pérdida de herramientas de administración

---

#### 2. Diagnóstico y Reparación WinRM (2 scripts)

| Script | Uso | Referencias |
|--------|-----|-------------|
| `fix_windows_host.py` | ✅ ACTIVO | Tool de reparación manual |
| `test_winrm_connection.py` | ✅ ACTIVO | Usado por 4 scripts diferentes |

**Referencias a test_winrm_connection.py**:
- ✅ `set_host_windows_credentials.py` (línea 77)
- ✅ `check_host_credentials.py` (línea 57)
- ✅ `test_winrm_credentials.sh` (línea 29)
- ✅ `show_windows_credential.py` (línea 65)

**Propósito**: Diagnóstico y reparación de conectividad WinRM
**Uso**: Manual cuando hay problemas de conectividad
**Impacto si se eliminan**: ❌ ALTO - Pérdida de herramientas de troubleshooting

---

#### 3. Configuración de Plantillas Windows (2 scripts PowerShell)

| Script | Uso | Referencias |
|--------|-----|-------------|
| `windows_template_setup.ps1` | ✅ ACTIVO | Documentado en 5 archivos MD |
| `winrm_post_provision_fix.ps1` | ✅ ACTIVO | Documentado en 3 archivos MD |

**Referencias a windows_template_setup.ps1**:
- ✅ `scripts/README.md` (9 referencias)
- ✅ `docs/WINDOWS_WINRM_IP_FIX.md` (7 referencias)
- ✅ `docs/SESSION_SUMMARY_WINDOWS_FIX.md` (6 referencias)
- ✅ `docs/WINRM_TROUBLESHOOTING.md` (3 referencias)

**Referencias a winrm_post_provision_fix.ps1**:
- ✅ `scripts/README.md` (4 referencias)
- ✅ `docs/SESSION_SUMMARY_WINDOWS_FIX.md` (3 referencias)

**Propósito**: Configuración inicial de plantillas Windows para WinRM
**Uso**: Manual al crear/actualizar plantillas Windows
**Impacto si se eliminan**: ❌ CRÍTICO - Imposible configurar nuevas plantillas

---

#### 4. Testing de Conectividad (2 scripts)

| Script | Uso | Referencias |
|--------|-----|-------------|
| `test_windows_winrm.sh` | ✅ ACTIVO | Documentado en 4 archivos MD |
| `test_winrm_credentials.sh` | ✅ ACTIVO | Usa test_winrm_connection.py |

**Referencias a test_windows_winrm.sh**:
- ✅ `scripts/README.md` (10 referencias)
- ✅ `docs/SESSION_SUMMARY_WINDOWS_FIX.md` (7 referencias)

**Propósito**: Testing rápido de conectividad WinRM
**Uso**: Manual para verificar conectividad antes de despliegues
**Impacto si se eliminan**: ⚠️ MEDIO - Pérdida de herramienta de testing

---

#### 5. Scripts Movidos Recientemente (1 script)

| Script | Uso | Referencias |
|--------|-----|-------------|
| `compare_winrm_configs.py` | ✅ ACTIVO | Documentado en WINRM_POST_DEPLOYMENT_ISSUE.md |

**Propósito**: Comparar configuraciones WinRM entre hosts
**Uso**: Manual para troubleshooting
**Impacto si se eliminan**: ⚠️ BAJO - Tool de diagnóstico avanzado

---

### ⚠️ SCRIPTS DE TESTING/DESARROLLO (13 scripts)

#### 6. Tests de Snapshots vSphere (5 scripts)

| Script | Tipo | Propósito |
|--------|------|-----------|
| `test_cleanup_windows.py` | 🧪 TEST | Test de limpieza de snapshots Windows |
| `test_create_snapshot.py` | 🧪 TEST | Test de creación de snapshots |
| `test_delete_snapshot.py` | 🧪 TEST | Test de eliminación de snapshots |
| `test_vm_snapshots.py` | 🧪 TEST | Test general de snapshots |
| `test_full_snapshot_lifecycle.py` | 🧪 TEST | Test de ciclo completo |

**Uso**: Scripts de desarrollo/testing para pyVmomi
**Referencias**: ❌ Ninguna en código de producción
**Propósito**: Validar funcionalidad de snapshots durante desarrollo
**Estado**: Probablemente obsoletos (funcionalidad ya integrada)

**Impacto si se eliminan**: ✅ NINGUNO - No usados en producción

---

#### 7. Tests de vSphere (1 script)

| Script | Tipo | Propósito |
|--------|------|-----------|
| `test_find_vm.py` | 🧪 TEST | Test de búsqueda de VMs en vCenter |

**Uso**: Script de desarrollo para pyVmomi
**Referencias**: ❌ Ninguna
**Estado**: Probablemente obsoleto

**Impacto si se eliminan**: ✅ NINGUNO - No usado en producción

---

#### 8. Tests de WinRM Avanzados (7 scripts)

| Script | Tipo | Propósito |
|--------|------|-----------|
| `test_winrm_auth_types.sh` | 🧪 TEST | Test de tipos de autenticación WinRM |
| `test_winrm_custom_headers.py` | 🧪 TEST | Test de headers HTTP personalizados |
| `test_winrm_debug.py` | 🧪 TEST | Test con debug de WinRM |
| `test_winrm_http10.py` | 🧪 TEST | Test con HTTP/1.0 |
| `test_winrm_raw.py` | 🧪 TEST | Test de conexión raw WinRM |
| `test_winrm_simple.py` | 🧪 TEST | Test simple de WinRM |

**Uso**: Scripts de desarrollo para troubleshooting WinRM
**Referencias**: ❌ Ninguna en código de producción
**Estado**: Usados durante desarrollo/debugging

**Impacto si se eliminan**: ⚠️ BAJO - Útiles para troubleshooting futuro

---

### 📋 SCRIPTS DE DIAGNÓSTICO (3 scripts PowerShell)

| Script | Tipo | Propósito |
|--------|------|-----------|
| `diagnose_winrm.ps1` | 🔍 DIAGNÓSTICO | Diagnóstico básico de WinRM |
| `diagnose_winrm_full.ps1` | 🔍 DIAGNÓSTICO | Diagnóstico completo de WinRM |
| `verify_winrm_config.ps1` | 🔍 DIAGNÓSTICO | Verificación de configuración WinRM |

**Uso**: Scripts PowerShell para ejecutar en hosts Windows
**Referencias**: Solo en documentación (SCRIPTS_ANALYSIS.md)
**Estado**: Herramientas de diagnóstico manual

**Impacto si se eliminan**: ⚠️ MEDIO - Útiles para troubleshooting

---

### 📦 ARCHIVOS DJANGO APP (11 archivos)

| Archivo | Tipo | Propósito |
|---------|------|-----------|
| `admin.py` | Django | Admin interface para scripts |
| `apps.py` | Django | App configuration |
| `forms.py` | Django | Formularios de scripts |
| `models.py` | Django | Modelo Script |
| `urls.py` | Django | URLs de scripts |
| `views.py` | Django | Vistas de scripts |
| `__init__.py` | Django | Package marker |
| `README.md` | Doc | Documentación de scripts |
| `management/` | Django | Management commands |
| `migrations/` | Django | Database migrations |
| `__pycache__/` | Python | Compiled bytecode |

**Uso**: ✅ CRÍTICO - Aplicación Django de gestión de scripts
**Impacto si se eliminan**: ❌ CRÍTICO - Rompe aplicación completa

---

## 📊 ESTADÍSTICAS

### Por Tipo de Uso

| Categoría | Cantidad | % |
|-----------|----------|---|
| **Django App** | 11 | 42% |
| **Scripts Activos** | 11 | 42% |
| **Tests/Desarrollo** | 13 | 50% |
| **Diagnóstico** | 3 | 12% |

### Por Lenguaje

| Lenguaje | Cantidad | % |
|----------|----------|---|
| **Python (.py)** | 21 | 81% |
| **Bash (.sh)** | 3 | 12% |
| **PowerShell (.ps1)** | 5 | 19% |
| **Otros** | 8 | 31% |

### Por Estado de Uso

| Estado | Cantidad | % |
|--------|----------|---|
| **Producción/Activo** | 11 | 42% |
| **Testing/Desarrollo** | 13 | 50% |
| **Diagnóstico** | 3 | 12% |
| **Django App** | 11 | 42% |

---

## 🎯 RECOMENDACIONES

### ✅ MANTENER (11 scripts + Django app)

**Scripts de Producción**:
1. `check_host_credentials.py` - Tool de admin
2. `set_host_windows_credentials.py` - Tool de admin
3. `show_windows_credential.py` - Tool de admin
4. `update_windows_credential_password.py` - Tool de admin
5. `fix_windows_host.py` - Reparación WinRM
6. `test_winrm_connection.py` - Usado por 4 scripts
7. `windows_template_setup.ps1` - Configuración plantillas
8. `winrm_post_provision_fix.ps1` - Post-provisioning
9. `test_windows_winrm.sh` - Testing conectividad
10. `test_winrm_credentials.sh` - Testing credenciales
11. `compare_winrm_configs.py` - Diagnóstico

**Django App**: Todos los archivos (11 archivos)

---

### 📁 MOVER A `/scripts/testing/` (13 scripts)

**Tests de Snapshots**:
- `test_cleanup_windows.py`
- `test_create_snapshot.py`
- `test_delete_snapshot.py`
- `test_vm_snapshots.py`
- `test_full_snapshot_lifecycle.py`
- `test_find_vm.py`

**Tests de WinRM**:
- `test_winrm_auth_types.sh`
- `test_winrm_custom_headers.py`
- `test_winrm_debug.py`
- `test_winrm_http10.py`
- `test_winrm_raw.py`
- `test_winrm_simple.py`

**Beneficio**: Organización clara entre producción y testing

---

### 📁 MOVER A `/scripts/diagnostics/` (3 scripts)

**Scripts PowerShell de Diagnóstico**:
- `diagnose_winrm.ps1`
- `diagnose_winrm_full.ps1`
- `verify_winrm_config.ps1`

**Beneficio**: Separar herramientas de diagnóstico

---

## 🗂️ ESTRUCTURA PROPUESTA

```
/opt/www/app/scripts/
├── admin.py                                    ✅ Django App
├── apps.py                                     ✅ Django App
├── forms.py                                    ✅ Django App
├── models.py                                   ✅ Django App
├── urls.py                                     ✅ Django App
├── views.py                                    ✅ Django App
├── __init__.py                                 ✅ Django App
├── README.md                                   ✅ Documentación
├── management/                                 ✅ Django App
├── migrations/                                 ✅ Django App
├── __pycache__/                                ✅ Django App
│
├── check_host_credentials.py                   ✅ PRODUCCIÓN
├── set_host_windows_credentials.py             ✅ PRODUCCIÓN
├── show_windows_credential.py                  ✅ PRODUCCIÓN
├── update_windows_credential_password.py       ✅ PRODUCCIÓN
├── fix_windows_host.py                         ✅ PRODUCCIÓN
├── test_winrm_connection.py                    ✅ PRODUCCIÓN
├── test_windows_winrm.sh                       ✅ PRODUCCIÓN
├── test_winrm_credentials.sh                   ✅ PRODUCCIÓN
├── compare_winrm_configs.py                    ✅ PRODUCCIÓN
├── windows_template_setup.ps1                  ✅ PRODUCCIÓN
├── winrm_post_provision_fix.ps1                ✅ PRODUCCIÓN
│
├── testing/                                    📁 NUEVA CARPETA
│   ├── test_cleanup_windows.py                🧪 TEST
│   ├── test_create_snapshot.py                🧪 TEST
│   ├── test_delete_snapshot.py                🧪 TEST
│   ├── test_vm_snapshots.py                   🧪 TEST
│   ├── test_full_snapshot_lifecycle.py        🧪 TEST
│   ├── test_find_vm.py                        🧪 TEST
│   ├── test_winrm_auth_types.sh               🧪 TEST
│   ├── test_winrm_custom_headers.py           🧪 TEST
│   ├── test_winrm_debug.py                    🧪 TEST
│   ├── test_winrm_http10.py                   🧪 TEST
│   ├── test_winrm_raw.py                      🧪 TEST
│   └── test_winrm_simple.py                   🧪 TEST
│
└── diagnostics/                                📁 NUEVA CARPETA
    ├── diagnose_winrm.ps1                     🔍 DIAGNÓSTICO
    ├── diagnose_winrm_full.ps1                🔍 DIAGNÓSTICO
    └── verify_winrm_config.ps1                🔍 DIAGNÓSTICO
```

---

## 📈 BENEFICIOS DE LA REORGANIZACIÓN

### Antes:
- ❌ 37 archivos mezclados en un solo directorio
- ❌ Difícil distinguir producción de testing
- ❌ Scripts de diagnóstico mezclados con operacionales

### Después:
- ✅ 11 scripts de producción en raíz (fácil acceso)
- ✅ 13 scripts de testing organizados en `/testing/`
- ✅ 3 scripts de diagnóstico en `/diagnostics/`
- ✅ 11 archivos Django App (sin cambios)
- ✅ Estructura clara y mantenible

---

## ⚠️ IMPACTO DE CAMBIOS

### Opción 1: MOVER a subcarpetas (RECOMENDADO)

**Archivos a mover**: 16 scripts (13 testing + 3 diagnostics)

**Impacto**: ✅ NINGUNO
- Scripts de testing NO están referenciados en código de producción
- Scripts de diagnóstico solo en documentación (fácil actualizar)
- Scripts de producción permanecen en raíz

**Beneficio**: Organización mejorada sin riesgo

---

### Opción 2: ELIMINAR scripts de testing

**Archivos a eliminar**: 13 scripts de testing

**Impacto**: ⚠️ BAJO
- No usados en producción
- Útiles para desarrollo futuro
- Fácilmente recuperables de Git

**Beneficio**: Limpieza agresiva

---

### Opción 3: NO HACER NADA

**Impacto**: ❌ Mantiene desorganización actual

---

## 🚀 PLAN DE ACCIÓN RECOMENDADO

### Paso 1: Crear subcarpetas
```bash
mkdir -p /opt/www/app/scripts/testing
mkdir -p /opt/www/app/scripts/diagnostics
```

### Paso 2: Mover scripts de testing (13 archivos)
```bash
mv /opt/www/app/scripts/test_cleanup_windows.py /opt/www/app/scripts/testing/
mv /opt/www/app/scripts/test_create_snapshot.py /opt/www/app/scripts/testing/
mv /opt/www/app/scripts/test_delete_snapshot.py /opt/www/app/scripts/testing/
mv /opt/www/app/scripts/test_vm_snapshots.py /opt/www/app/scripts/testing/
mv /opt/www/app/scripts/test_full_snapshot_lifecycle.py /opt/www/app/scripts/testing/
mv /opt/www/app/scripts/test_find_vm.py /opt/www/app/scripts/testing/
mv /opt/www/app/scripts/test_winrm_auth_types.sh /opt/www/app/scripts/testing/
mv /opt/www/app/scripts/test_winrm_custom_headers.py /opt/www/app/scripts/testing/
mv /opt/www/app/scripts/test_winrm_debug.py /opt/www/app/scripts/testing/
mv /opt/www/app/scripts/test_winrm_http10.py /opt/www/app/scripts/testing/
mv /opt/www/app/scripts/test_winrm_raw.py /opt/www/app/scripts/testing/
mv /opt/www/app/scripts/test_winrm_simple.py /opt/www/app/scripts/testing/
```

### Paso 3: Mover scripts de diagnóstico (3 archivos)
```bash
mv /opt/www/app/scripts/diagnose_winrm.ps1 /opt/www/app/scripts/diagnostics/
mv /opt/www/app/scripts/diagnose_winrm_full.ps1 /opt/www/app/scripts/diagnostics/
mv /opt/www/app/scripts/verify_winrm_config.ps1 /opt/www/app/scripts/diagnostics/
```

### Paso 4: Verificar
```bash
# Scripts de producción en raíz (11)
ls -1 /opt/www/app/scripts/*.py /opt/www/app/scripts/*.sh /opt/www/app/scripts/*.ps1 2>/dev/null | wc -l

# Scripts de testing (13)
ls -1 /opt/www/app/scripts/testing/* 2>/dev/null | wc -l

# Scripts de diagnóstico (3)
ls -1 /opt/www/app/scripts/diagnostics/* 2>/dev/null | wc -l
```

---

## ✅ RESULTADO ESPERADO

### Antes:
- 37 archivos en `/scripts/` (mezclados)

### Después:
- 22 archivos en `/scripts/` (11 producción + 11 Django app)
- 13 archivos en `/scripts/testing/`
- 3 archivos en `/scripts/diagnostics/`

**Total**: Mismos 37 archivos, mejor organizados

---

## 📝 CONCLUSIÓN

**Scripts en uso activo**: 11 scripts de producción
**Scripts de testing**: 13 scripts (útiles pero no en producción)
**Scripts de diagnóstico**: 3 scripts PowerShell (herramientas manuales)
**Django App**: 11 archivos (críticos)

**Recomendación**: Mover scripts de testing y diagnóstico a subcarpetas para mejor organización, SIN eliminar nada.

**Impacto**: ✅ CERO impacto en producción, mejora significativa en organización.
