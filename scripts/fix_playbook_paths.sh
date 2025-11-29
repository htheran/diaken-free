#!/bin/bash
# Script para mover playbooks a las rutas correctas y actualizar la base de datos
# Uso: ./fix_playbook_paths.sh

set -e

echo "========================================"
echo "CORRECCIÓN DE RUTAS DE PLAYBOOKS"
echo "========================================"

# Get script directory and navigate to project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
cd "$PROJECT_DIR"

# Crear directorios si no existen
mkdir -p media/playbooks/host
mkdir -p media/playbooks/group

echo ""
echo "=== MOVIENDO ARCHIVOS A RUTAS CORRECTAS ==="
echo ""

# Mover archivos que están en playbooks/ directamente
for file in media/playbooks/*.yml; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        echo "Procesando: $filename"
        
        # Determinar si es host o group basándose en el nombre
        # Por defecto, asumimos que son host playbooks
        target_dir="media/playbooks/host"
        
        # Si el nombre contiene "Group", moverlo a group
        if [[ "$filename" == *"Group"* ]]; then
            target_dir="media/playbooks/group"
        fi
        
        # Mover el archivo
        if [ ! -f "$target_dir/$filename" ]; then
            mv "$file" "$target_dir/"
            echo "  ✅ Movido a: $target_dir/$filename"
        else
            echo "  ⚠️  Ya existe en: $target_dir/$filename (eliminando duplicado)"
            rm "$file"
        fi
    fi
done

echo ""
echo "=== ACTUALIZANDO BASE DE DATOS ==="
echo ""

python3 manage.py shell << 'PYTHON_EOF'
from playbooks.models import Playbook
import os

print("Actualizando rutas en la base de datos...\n")

updated = 0
for pb in Playbook.objects.all():
    old_path = pb.file.name
    expected_path = f"playbooks/{pb.playbook_type}/{os.path.basename(pb.file.name)}"
    
    if old_path != expected_path:
        print(f"Actualizando: {pb.name}")
        print(f"  Anterior: {old_path}")
        print(f"  Nueva:    {expected_path}")
        
        pb.file.name = expected_path
        pb.save()
        updated += 1
        print(f"  ✅ Actualizado\n")

print(f"{'='*50}")
print(f"Total de playbooks actualizados: {updated}")
print(f"{'='*50}\n")

# Verificar que todos los archivos existen
print("Verificando integridad de archivos...\n")
missing = 0
for pb in Playbook.objects.all():
    try:
        if not os.path.exists(pb.file.path):
            print(f"❌ Archivo no existe: {pb.name} -> {pb.file.path}")
            missing += 1
        else:
            print(f"✅ {pb.name}")
    except Exception as e:
        print(f"❌ Error verificando {pb.name}: {e}")
        missing += 1

if missing > 0:
    print(f"\n⚠️  {missing} playbooks tienen archivos faltantes")
else:
    print(f"\n✅ Todos los playbooks tienen archivos válidos")
PYTHON_EOF

echo ""
echo "=========================================="
echo "✅ CORRECCIÓN COMPLETADA"
echo "=========================================="
echo ""
echo "Resumen de archivos:"
echo "  Host playbooks:"
ls -1 media/playbooks/host/*.yml 2>/dev/null | wc -l
echo "  Group playbooks:"
ls -1 media/playbooks/group/*.yml 2>/dev/null | wc -l
