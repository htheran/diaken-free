# Verificación Pre-Movimiento de Scripts

## Fecha: 2025-10-14 15:34

## ✅ VERIFICACIÓN COMPLETADA

### 1. Crontab Activo
```bash
* * * * * /opt/www/app/run_scheduler.sh >> /var/log/scheduler.log 2>&1
*/15 * * * * /opt/www/app/cleanup_snapshots.sh >> /var/log/snapshot_cleanup.log 2>&1
*/30 * * * * /opt/www/app/cleanup_stuck_deployments.sh >> /var/log/cleanup_stuck_deployments.log 2>&1
```

**Conclusión**: ✅ Ninguno de los scripts a mover está en crontab

---

### 2. Scripts a MOVER (sin referencias activas)

#### A. `compare_winrm_configs.py`
**Referencias encontradas**:
- ❌ Ninguna referencia en código Python
- ❌ Ninguna referencia en templates HTML
- ❌ Ninguna referencia en scripts Bash
- ⚠️ Solo en documentación: `/opt/www/app/docs/WINRM_POST_DEPLOYMENT_ISSUE.md` (línea 221)

**Acción requerida**: Actualizar documentación después del movimiento

**Impacto**: ✅ NINGUNO - Script de diagnóstico manual, no usado en producción

---

#### B. `test_winrm_auth_types.sh`
**Referencias encontradas**:
- ❌ Ninguna referencia en código Python
- ❌ Ninguna referencia en templates HTML
- ❌ Ninguna referencia en scripts Bash
- ❌ Ninguna referencia en documentación

**Acción requerida**: Ninguna

**Impacto**: ✅ NINGUNO - Script de testing, no usado en producción

---

### 3. Script a ELIMINAR (duplicado obsoleto)

#### C. `test_winrm_connection.py` (RAÍZ)
**Referencias encontradas**:
- ⚠️ Solo en documentación: `/opt/www/app/docs/WINRM_POST_DEPLOYMENT_ISSUE.md` (línea 218)

**Versión activa**: `/opt/www/app/scripts/test_winrm_connection.py`

**Referencias a la versión activa (scripts/)**:
- ✅ `scripts/set_host_windows_credentials.py` (línea 77)
- ✅ `scripts/check_host_credentials.py` (línea 57)
- ✅ `scripts/test_winrm_credentials.sh` (línea 29)
- ✅ `scripts/show_windows_credential.py` (línea 65)

**Acción requerida**: Actualizar documentación después de la eliminación

**Impacto**: ✅ NINGUNO - La versión activa en scripts/ seguirá funcionando

---

### 4. Scripts CRÍTICOS que NO se mueven

| Script | Uso | Referencia |
|--------|-----|------------|
| `cleanup_snapshots.sh` | ✅ Crontab | */15 * * * * |
| `cleanup_stuck_deployments.sh` | ✅ Crontab + HTML | */30 * * * * + template |
| `run_scheduler.sh` | ✅ Crontab | * * * * * |
| `run_scheduler_daemon.sh` | ✅ Daemon | nohup process |
| `set_snapshot_retention.sh` | ✅ Admin tool | Manual |

**Impacto**: ✅ NINGUNO - Permanecen en raíz

---

## 📝 CAMBIOS A REALIZAR

### Paso 1: Mover Scripts No Usados
```bash
mv /opt/www/app/compare_winrm_configs.py /opt/www/app/scripts/
mv /opt/www/app/test_winrm_auth_types.sh /opt/www/app/scripts/
```

**Impacto**: ✅ NINGUNO en funcionalidad
**Beneficio**: Mejor organización

---

### Paso 2: Eliminar Duplicado Obsoleto
```bash
rm /opt/www/app/test_winrm_connection.py
```

**Impacto**: ✅ NINGUNO - Versión activa en scripts/ sigue funcionando
**Beneficio**: Elimina confusión y duplicación

---

### Paso 3: Actualizar Documentación

#### Archivo: `/opt/www/app/docs/WINRM_POST_DEPLOYMENT_ISSUE.md`

**Línea 218** - Cambiar:
```bash
# ANTES:
python /opt/www/app/test_winrm_connection.py test-win2

# DESPUÉS:
python /opt/www/app/scripts/test_winrm_connection.py test-win2
```

**Línea 221** - Cambiar:
```bash
# ANTES:
python /opt/www/app/compare_winrm_configs.py test-win2

# DESPUÉS:
python /opt/www/app/scripts/compare_winrm_configs.py test-win2
```

---

## ✅ VERIFICACIÓN FINAL

### Crontab
- ✅ No se modifica ningún script en crontab
- ✅ Todos los scripts críticos permanecen en raíz

### Código Python
- ✅ No hay referencias a scripts que se van a mover
- ✅ Referencias a test_winrm_connection.py apuntan a scripts/ (versión activa)

### Templates HTML
- ✅ No hay referencias a scripts que se van a mover
- ✅ cleanup_stuck_deployments.sh permanece en raíz (referenciado en template)

### Scripts Bash
- ✅ No hay referencias a scripts que se van a mover
- ✅ test_winrm_credentials.sh usa scripts/test_winrm_connection.py (correcto)

### Documentación
- ⚠️ Requiere actualización de 2 líneas en WINRM_POST_DEPLOYMENT_ISSUE.md
- ✅ Cambio simple y seguro

---

## 🎯 RESULTADO ESPERADO

### Antes:
```
/opt/www/app/
├── cleanup_snapshots.sh              (MANTENER)
├── cleanup_stuck_deployments.sh      (MANTENER)
├── compare_winrm_configs.py          (MOVER)
├── run_scheduler.sh                  (MANTENER)
├── run_scheduler_daemon.sh           (MANTENER)
├── set_snapshot_retention.sh         (MANTENER)
├── test_winrm_auth_types.sh          (MOVER)
├── test_winrm_connection.py          (ELIMINAR - duplicado)
└── scripts/ (37 archivos)
```

### Después:
```
/opt/www/app/
├── cleanup_snapshots.sh              ✅
├── cleanup_stuck_deployments.sh      ✅
├── run_scheduler.sh                  ✅
├── run_scheduler_daemon.sh           ✅
├── set_snapshot_retention.sh         ✅
└── scripts/ (40 archivos)
    ├── compare_winrm_configs.py      ← MOVIDO
    ├── test_winrm_auth_types.sh      ← MOVIDO
    ├── test_winrm_connection.py      ← YA EXISTÍA (versión activa)
    └── ... (37 archivos existentes)
```

---

## 🔒 GARANTÍAS DE SEGURIDAD

1. ✅ **Crontab**: No se toca ningún script en crontab
2. ✅ **Producción**: No se mueve ningún script usado en producción
3. ✅ **Referencias**: No hay referencias en código a scripts que se mueven
4. ✅ **Duplicado**: La versión activa permanece intacta en scripts/
5. ✅ **Reversible**: Cambios fácilmente reversibles si hay problema

---

## 🚀 EJECUCIÓN SEGURA

Los cambios son **100% seguros** porque:
- Scripts a mover NO están en uso
- Scripts críticos permanecen en raíz
- Solo requiere actualizar 2 líneas de documentación
- Duplicado obsoleto se elimina (versión activa permanece)

**APROBADO PARA EJECUCIÓN** ✅
