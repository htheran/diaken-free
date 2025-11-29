#!/bin/bash
# Script para limpiar playbooks huérfanos de la base de datos
# Uso: ./cleanup_orphan_playbooks.sh

set -e

echo "========================================"
echo "LIMPIEZA DE PLAYBOOKS HUÉRFANOS"
echo "========================================"

# Get script directory and navigate to project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
cd "$PROJECT_DIR"

python3 manage.py shell << 'PYTHON_EOF'
from playbooks.models import Playbook
import os

print("\n=== VERIFICANDO PLAYBOOKS EN BASE DE DATOS ===\n")
playbooks = Playbook.objects.all().order_by('playbook_type', 'name')

to_delete = []
valid_count = 0

for pb in playbooks:
    try:
        file_exists = os.path.exists(pb.file.path)
        if file_exists:
            valid_count += 1
            print(f"✅ {pb.name} ({pb.playbook_type})")
        else:
            print(f"❌ {pb.name} ({pb.playbook_type}) - Archivo no existe: {pb.file.path}")
            to_delete.append(pb)
    except Exception as e:
        print(f"❌ {pb.name} ({pb.playbook_type}) - Error: {e}")
        to_delete.append(pb)

print(f"\n{'='*50}")
print(f"Playbooks válidos: {valid_count}")
print(f"Playbooks huérfanos: {len(to_delete)}")
print(f"{'='*50}\n")

if to_delete:
    print("=== ELIMINANDO PLAYBOOKS HUÉRFANOS ===\n")
    for pb in to_delete:
        print(f"Eliminando: {pb.name} (ID: {pb.id}, Tipo: {pb.playbook_type})")
        pb.delete()
    print(f"\n✅ {len(to_delete)} playbooks eliminados de la base de datos\n")
else:
    print("✅ No hay playbooks huérfanos. Base de datos limpia.\n")

print("=== RESUMEN FINAL ===")
print(f"Total de playbooks en DB: {Playbook.objects.count()}")
print(f"  - Host: {Playbook.objects.filter(playbook_type='host').count()}")
print(f"  - Group: {Playbook.objects.filter(playbook_type='group').count()}")
PYTHON_EOF

echo ""
echo "=========================================="
echo "✅ LIMPIEZA COMPLETADA"
echo "=========================================="
