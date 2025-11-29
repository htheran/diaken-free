#!/bin/bash
#
# Script de deployment para aplicar cambios después de git pull
# Uso: ./scripts/deploy_updates.sh
#

set -e  # Salir si hay algún error

echo "=========================================="
echo "DIAKEN - Script de Deployment"
echo "=========================================="
echo ""

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar que estamos en el directorio correcto
if [ ! -f "manage.py" ]; then
    echo -e "${RED}Error: Este script debe ejecutarse desde el directorio raíz del proyecto${NC}"
    exit 1
fi

echo -e "${YELLOW}1. Activando entorno virtual...${NC}"
source venv/bin/activate

echo -e "${YELLOW}2. Creando backup de base de datos...${NC}"
BACKUP_DIR="/tmp/diaken_backups"
mkdir -p $BACKUP_DIR
BACKUP_FILE="$BACKUP_DIR/diaken_backup_$(date +%Y%m%d_%H%M%S).sql"

if command -v mariadb-dump &> /dev/null; then
    mariadb-dump -u root diaken > $BACKUP_FILE 2>/dev/null && \
        echo -e "${GREEN}✓ Backup creado: $BACKUP_FILE${NC}" || \
        echo -e "${YELLOW}⚠ No se pudo crear backup (continuando...)${NC}"
else
    echo -e "${YELLOW}⚠ mariadb-dump no disponible (saltando backup)${NC}"
fi

echo -e "${YELLOW}3. Instalando/actualizando dependencias...${NC}"
pip install -r requirements.txt --quiet

echo -e "${YELLOW}4. Aplicando migraciones de base de datos...${NC}"
python manage.py migrate

echo -e "${YELLOW}5. Recolectando archivos estáticos...${NC}"
python manage.py collectstatic --noinput

echo -e "${YELLOW}6. Verificando estructura de directorios...${NC}"

# Crear directorios necesarios si no existen
mkdir -p /var/run/celery
mkdir -p /var/log/celery
mkdir -p media/playbooks/host
mkdir -p media/playbooks/group
mkdir -p media/ssh
mkdir -p media/scripts
mkdir -p media/j2
mkdir -p media/ssl

echo -e "${GREEN}✓ Directorios verificados${NC}"

echo -e "${YELLOW}7. Estableciendo permisos...${NC}"
chown -R apache:apache /var/run/celery
chown -R apache:apache /var/log/celery
chown -R apache:apache media/
chmod -R 755 media/playbooks/

echo -e "${GREEN}✓ Permisos establecidos${NC}"

echo -e "${YELLOW}8. Verificando configuración de tmpfiles.d...${NC}"
if [ ! -f "/etc/tmpfiles.d/celery-diaken.conf" ]; then
    echo "Creando /etc/tmpfiles.d/celery-diaken.conf..."
    cat > /etc/tmpfiles.d/celery-diaken.conf << 'EOF'
d /var/run/celery 0755 apache apache -
d /var/log/celery 0755 apache apache -
EOF
    echo -e "${GREEN}✓ Archivo tmpfiles.d creado${NC}"
else
    echo -e "${GREEN}✓ Archivo tmpfiles.d ya existe${NC}"
fi

echo -e "${YELLOW}9. Verificando configuración de Apache...${NC}"
if [ ! -f "/etc/httpd/conf.d/mpm_prefork.conf" ]; then
    echo "Creando /etc/httpd/conf.d/mpm_prefork.conf..."
    cat > /etc/httpd/conf.d/mpm_prefork.conf << 'EOF'
# Configuración optimizada para servidor con poca RAM (3.4GB)
<IfModule mpm_prefork_module>
    StartServers             2
    MinSpareServers          2
    MaxSpareServers          5
    MaxRequestWorkers       20
    MaxConnectionsPerChild  1000
</IfModule>
EOF
    echo -e "${GREEN}✓ Configuración de Apache creada${NC}"
else
    echo -e "${GREEN}✓ Configuración de Apache ya existe${NC}"
fi

echo -e "${YELLOW}10. Corrigiendo rutas de playbooks en base de datos...${NC}"
python manage.py shell << 'PYEOF'
from playbooks.models import Playbook
import os

print("Verificando y corrigiendo rutas de playbooks...")

fixed_count = 0
for pb in Playbook.objects.all():
    expected_path = f'playbooks/{pb.playbook_type}/{os.path.basename(pb.file.name)}'
    
    if pb.file.name != expected_path:
        print(f"  Corrigiendo: {pb.name}")
        print(f"    De: {pb.file.name}")
        print(f"    A:  {expected_path}")
        
        # Actualizar ruta en BD
        pb.file.name = expected_path
        pb.save()
        fixed_count += 1

if fixed_count > 0:
    print(f"✓ {fixed_count} playbook(s) corregido(s)")
else:
    print("✓ Todos los playbooks tienen rutas correctas")
PYEOF

echo -e "${YELLOW}11. Reiniciando servicios...${NC}"
systemctl restart httpd
systemctl restart celery-diaken

echo ""
echo -e "${GREEN}=========================================="
echo "✅ Deployment completado exitosamente"
echo "==========================================${NC}"
echo ""
echo "Servicios reiniciados:"
echo "  - Apache (httpd)"
echo "  - Celery worker"
echo ""
echo "Verificar estado de servicios:"
echo "  systemctl status httpd"
echo "  systemctl status celery-diaken"
echo ""
