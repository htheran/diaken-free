#!/bin/bash

# Script de validación de sincronización entre servidores
# Ejecutar en ambos servidores y comparar resultados

echo "=========================================="
echo "VALIDACIÓN DE SINCRONIZACIÓN - DIAKEN-PDN"
echo "=========================================="
echo ""
echo "Servidor: $(hostname)"
echo "Fecha: $(date)"
echo "Usuario: $(whoami)"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR" || exit 1

echo "=========================================="
echo "1. INFORMACIÓN DE GIT"
echo "=========================================="
echo "Branch actual:"
git branch --show-current
echo ""
echo "Último commit:"
git log -1 --oneline
echo ""
echo "Commit hash completo:"
git rev-parse HEAD
echo ""
echo "Estado del repositorio:"
git status --short
echo ""

echo "=========================================="
echo "2. ARCHIVOS CLAVE - CHECKSUMS"
echo "=========================================="
echo "Calculando MD5 de archivos importantes..."
echo ""

# Archivos Python principales
echo "--- Archivos Python ---"
md5sum deploy/tasks.py 2>/dev/null || echo "ERROR: deploy/tasks.py no encontrado"
md5sum deploy/views_playbook_windows.py 2>/dev/null || echo "ERROR: deploy/views_playbook_windows.py no encontrado"
md5sum inventory/views.py 2>/dev/null || echo "ERROR: inventory/views.py no encontrado"
echo ""

# Playbooks principales
echo "--- Playbooks Windows ---"
md5sum media/playbooks/host/Update-Windows-Host.yml 2>/dev/null || echo "ERROR: Update-Windows-Host.yml no encontrado"
md5sum media/playbooks/group/Update-Windows-Group.yml 2>/dev/null || echo "ERROR: Update-Windows-Group.yml no encontrado"
md5sum media/playbooks/group/Listar-Updates-Windows-Group.yml 2>/dev/null || echo "ERROR: Listar-Updates-Windows-Group.yml no encontrado"
echo ""

# Documentación
echo "--- Documentación ---"
md5sum docs/WINDOWS_GROUP_UPDATES_RECOMMENDATIONS.md 2>/dev/null || echo "ERROR: WINDOWS_GROUP_UPDATES_RECOMMENDATIONS.md no encontrado"
md5sum DATABASE_SCHEMA.md 2>/dev/null || echo "ERROR: DATABASE_SCHEMA.md no encontrado"
echo ""

echo "=========================================="
echo "3. PERMISOS DE ARCHIVOS CLAVE"
echo "=========================================="
echo "--- Playbooks ---"
ls -l media/playbooks/host/Update-Windows-Host.yml 2>/dev/null || echo "ERROR: Update-Windows-Host.yml no encontrado"
ls -l media/playbooks/group/Update-Windows-Group.yml 2>/dev/null || echo "ERROR: Update-Windows-Group.yml no encontrado"
ls -l media/playbooks/group/Listar-Updates-Windows-Group.yml 2>/dev/null || echo "ERROR: Listar-Updates-Windows-Group.yml no encontrado"
echo ""

echo "--- Python ---"
ls -l deploy/tasks.py 2>/dev/null || echo "ERROR: deploy/tasks.py no encontrado"
ls -l deploy/views_playbook_windows.py 2>/dev/null || echo "ERROR: deploy/views_playbook_windows.py no encontrado"
ls -l inventory/views.py 2>/dev/null || echo "ERROR: inventory/views.py no encontrado"
echo ""

echo "=========================================="
echo "4. PROPIETARIOS Y GRUPOS"
echo "=========================================="
echo "Directorio principal:"
ls -ld "$SCRIPT_DIR"
echo ""
echo "Subdirectorios clave:"
ls -ld "$SCRIPT_DIR/deploy"
ls -ld "$SCRIPT_DIR/inventory"
ls -ld "$SCRIPT_DIR/media/playbooks"
echo ""

echo "=========================================="
echo "5. SERVICIOS Y PROCESOS"
echo "=========================================="
echo "--- Apache ---"
systemctl is-active httpd && echo "✅ Apache: RUNNING" || echo "❌ Apache: STOPPED"
systemctl is-enabled httpd && echo "✅ Apache: ENABLED" || echo "⚠️  Apache: DISABLED"
echo ""

echo "--- Celery ---"
if systemctl is-active celery-diaken &>/dev/null; then
    echo "✅ Celery: RUNNING (celery-diaken)"
    systemctl is-enabled celery-diaken && echo "✅ Celery: ENABLED" || echo "⚠️  Celery: DISABLED"
elif systemctl is-active celery-worker &>/dev/null; then
    echo "✅ Celery: RUNNING (celery-worker)"
    systemctl is-enabled celery-worker && echo "✅ Celery: ENABLED" || echo "⚠️  Celery: DISABLED"
else
    echo "❌ Celery: STOPPED"
fi
echo ""

echo "Workers de Celery activos:"
ps aux | grep "celery.*worker" | grep -v grep | wc -l
echo ""

echo "=========================================="
echo "6. CONFIGURACIÓN DE CELERY"
echo "=========================================="
echo "Verificando timeouts de Celery..."
cd "$SCRIPT_DIR"
source venv/bin/activate 2>/dev/null
python3 << 'PYEOF'
try:
    from deploy.tasks import execute_windows_playbook_async
    print(f"✅ Tarea: execute_windows_playbook_async")
    print(f"   soft_time_limit: {execute_windows_playbook_async.soft_time_limit}s ({execute_windows_playbook_async.soft_time_limit/3600:.1f}h)")
    print(f"   time_limit: {execute_windows_playbook_async.time_limit}s ({execute_windows_playbook_async.time_limit/3600:.1f}h)")
except Exception as e:
    print(f"❌ Error al verificar timeouts: {e}")
PYEOF
echo ""

echo "=========================================="
echo "7. ESTRUCTURA DE DIRECTORIOS"
echo "=========================================="
echo "Conteo de archivos por tipo:"
echo "  Playbooks (.yml): $(find media/playbooks -name "*.yml" 2>/dev/null | wc -l)"
echo "  Python (.py): $(find . -name "*.py" -not -path "./venv/*" -not -path "./__pycache__/*" 2>/dev/null | wc -l)"
echo "  Templates (.html): $(find templates -name "*.html" 2>/dev/null | wc -l)"
echo ""

echo "=========================================="
echo "8. ARCHIVOS RECIENTES (últimas 24h)"
echo "=========================================="
echo "Archivos modificados en las últimas 24 horas:"
find "$SCRIPT_DIR" -type f -mtime -1 -not -path "*/venv/*" -not -path "*/__pycache__/*" -not -path "*/.git/*" 2>/dev/null | head -20
echo ""

echo "=========================================="
echo "9. LOGS Y ERRORES RECIENTES"
echo "=========================================="
echo "Últimas líneas del log de Apache:"
sudo tail -5 /var/log/httpd/error_log 2>/dev/null || echo "No se puede acceder al log de Apache"
echo ""

echo "Últimas líneas del log de Celery:"
sudo tail -5 /var/log/celery/diaken-worker.log 2>/dev/null || echo "No se puede acceder al log de Celery"
echo ""

echo "=========================================="
echo "10. RESUMEN DE VALIDACIÓN"
echo "=========================================="
echo "Commit actual: $(git rev-parse --short HEAD)"
echo "Branch: $(git branch --show-current)"
echo "Archivos sin commit: $(git status --short | wc -l)"
echo "Apache: $(systemctl is-active httpd)"
echo "Celery: $(systemctl is-active celery-diaken 2>/dev/null || systemctl is-active celery-worker 2>/dev/null || echo 'inactive')"
echo ""
echo "=========================================="
echo "VALIDACIÓN COMPLETADA"
echo "=========================================="
