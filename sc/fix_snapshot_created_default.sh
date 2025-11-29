#!/bin/bash
# Script para corregir el default del campo snapshot_created
# Ejecutar después de aplicar la migración 0008
# Get script directory and navigate to project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

cd "$PROJECT_DIR"
source venv/bin/activate

echo "Corrigiendo default del campo snapshot_created..."

python manage.py shell --settings=diaken.settings_production -c "
from django.db import connection

with connection.cursor() as cursor:
    # Modificar el campo para que tenga default 0
    cursor.execute('ALTER TABLE scheduler_scheduledtask MODIFY COLUMN snapshot_created tinyint(1) NOT NULL DEFAULT 0')
    print('✓ Campo snapshot_created modificado con default=0')
    
    # Verificar
    cursor.execute('DESCRIBE scheduler_scheduledtask')
    columns = cursor.fetchall()
    
    for col in columns:
        if col[0] == 'snapshot_created':
            print(f'  Verificación: {col[0]} | Default: {col[4]}')
"

echo "✓ Corrección completada"
