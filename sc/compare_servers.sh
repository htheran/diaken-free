#!/bin/bash

# Script para comparar validaciones entre dos servidores
# Uso: ./compare_servers.sh validation_server1.txt validation_server2.txt

if [ "$#" -ne 2 ]; then
    echo "Uso: $0 <archivo_validacion_server1> <archivo_validacion_server2>"
    echo ""
    echo "Ejemplo:"
    echo "  $0 validation_diaken-dev.txt validation_diaken-pdn.txt"
    exit 1
fi

FILE1="$1"
FILE2="$2"

if [ ! -f "$FILE1" ]; then
    echo "❌ Error: Archivo $FILE1 no encontrado"
    exit 1
fi

if [ ! -f "$FILE2" ]; then
    echo "❌ Error: Archivo $FILE2 no encontrado"
    exit 1
fi

echo "=========================================="
echo "COMPARACIÓN DE SERVIDORES"
echo "=========================================="
echo ""

# Extraer nombres de servidores
SERVER1=$(grep "^Servidor:" "$FILE1" | awk '{print $2}')
SERVER2=$(grep "^Servidor:" "$FILE2" | awk '{print $2}')

echo "Servidor 1: $SERVER1"
echo "Servidor 2: $SERVER2"
echo ""

echo "=========================================="
echo "1. COMMITS DE GIT"
echo "=========================================="
COMMIT1=$(grep "^Commit actual:" "$FILE1" | awk '{print $3}')
COMMIT2=$(grep "^Commit actual:" "$FILE2" | awk '{print $3}')

if [ "$COMMIT1" == "$COMMIT2" ]; then
    echo "✅ Commits IGUALES: $COMMIT1"
else
    echo "❌ Commits DIFERENTES:"
    echo "   $SERVER1: $COMMIT1"
    echo "   $SERVER2: $COMMIT2"
fi
echo ""

echo "=========================================="
echo "2. CHECKSUMS DE ARCHIVOS CLAVE"
echo "=========================================="

# Función para comparar checksums
compare_checksum() {
    local file=$1
    local label=$2
    
    local sum1=$(grep "$file" "$FILE1" | awk '{print $1}')
    local sum2=$(grep "$file" "$FILE2" | awk '{print $1}')
    
    if [ -z "$sum1" ] || [ -z "$sum2" ]; then
        echo "⚠️  $label: No se pudo verificar"
        return
    fi
    
    if [ "$sum1" == "$sum2" ]; then
        echo "✅ $label: IGUAL"
    else
        echo "❌ $label: DIFERENTE"
        echo "   $SERVER1: $sum1"
        echo "   $SERVER2: $sum2"
    fi
}

echo "--- Archivos Python ---"
compare_checksum "deploy/tasks.py" "tasks.py"
compare_checksum "deploy/views_playbook_windows.py" "views_playbook_windows.py"
compare_checksum "inventory/views.py" "inventory/views.py"
echo ""

echo "--- Playbooks ---"
compare_checksum "Update-Windows-Host.yml" "Update-Windows-Host.yml"
compare_checksum "Update-Windows-Group.yml" "Update-Windows-Group.yml"
compare_checksum "Listar-Updates-Windows-Group.yml" "Listar-Updates-Windows-Group.yml"
echo ""

echo "=========================================="
echo "3. SERVICIOS"
echo "=========================================="

# Apache
APACHE1=$(grep "^Apache:" "$FILE1" | tail -1 | awk '{print $2}')
APACHE2=$(grep "^Apache:" "$FILE2" | tail -1 | awk '{print $2}')

if [ "$APACHE1" == "$APACHE2" ] && [ "$APACHE1" == "active" ]; then
    echo "✅ Apache: Ambos RUNNING"
else
    echo "⚠️  Apache:"
    echo "   $SERVER1: $APACHE1"
    echo "   $SERVER2: $APACHE2"
fi

# Celery
CELERY1=$(grep "^Celery:" "$FILE1" | tail -1 | awk '{print $2}')
CELERY2=$(grep "^Celery:" "$FILE2" | tail -1 | awk '{print $2}')

if [ "$CELERY1" == "$CELERY2" ] && [ "$CELERY1" == "active" ]; then
    echo "✅ Celery: Ambos RUNNING"
else
    echo "⚠️  Celery:"
    echo "   $SERVER1: $CELERY1"
    echo "   $SERVER2: $CELERY2"
fi
echo ""

echo "=========================================="
echo "4. TIMEOUTS DE CELERY"
echo "=========================================="

TIMEOUT1=$(grep "soft_time_limit:" "$FILE1" | grep -oP '\d+s' | head -1)
TIMEOUT2=$(grep "soft_time_limit:" "$FILE2" | grep -oP '\d+s' | head -1)

if [ "$TIMEOUT1" == "$TIMEOUT2" ]; then
    echo "✅ Timeouts IGUALES: $TIMEOUT1"
else
    echo "❌ Timeouts DIFERENTES:"
    echo "   $SERVER1: $TIMEOUT1"
    echo "   $SERVER2: $TIMEOUT2"
fi
echo ""

echo "=========================================="
echo "5. ESTRUCTURA DE ARCHIVOS"
echo "=========================================="

PLAYBOOKS1=$(grep "Playbooks (.yml):" "$FILE1" | grep -oP '\d+')
PLAYBOOKS2=$(grep "Playbooks (.yml):" "$FILE2" | grep -oP '\d+')

if [ "$PLAYBOOKS1" == "$PLAYBOOKS2" ]; then
    echo "✅ Playbooks: $PLAYBOOKS1 archivos en ambos"
else
    echo "⚠️  Playbooks:"
    echo "   $SERVER1: $PLAYBOOKS1 archivos"
    echo "   $SERVER2: $PLAYBOOKS2 archivos"
fi

PYTHON1=$(grep "Python (.py):" "$FILE1" | grep -oP '\d+')
PYTHON2=$(grep "Python (.py):" "$FILE2" | grep -oP '\d+')

if [ "$PYTHON1" == "$PYTHON2" ]; then
    echo "✅ Python: $PYTHON1 archivos en ambos"
else
    echo "⚠️  Python:"
    echo "   $SERVER1: $PYTHON1 archivos"
    echo "   $SERVER2: $PYTHON2 archivos"
fi
echo ""

echo "=========================================="
echo "RESUMEN"
echo "=========================================="

# Contar diferencias
DIFF_COUNT=0

[ "$COMMIT1" != "$COMMIT2" ] && ((DIFF_COUNT++))
[ "$APACHE1" != "$APACHE2" ] && ((DIFF_COUNT++))
[ "$CELERY1" != "$CELERY2" ] && ((DIFF_COUNT++))
[ "$TIMEOUT1" != "$TIMEOUT2" ] && ((DIFF_COUNT++))

if [ $DIFF_COUNT -eq 0 ]; then
    echo "✅ Servidores SINCRONIZADOS"
    echo ""
    echo "Ambos servidores están en el mismo estado:"
    echo "  - Mismo commit: $COMMIT1"
    echo "  - Servicios corriendo correctamente"
    echo "  - Timeouts configurados igual"
else
    echo "⚠️  Se encontraron $DIFF_COUNT diferencias"
    echo ""
    echo "Revisa las secciones anteriores para detalles"
fi

echo ""
echo "=========================================="
