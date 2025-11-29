#!/bin/bash
#
# Script de Deployment Automático para Producción
# Oracle Linux 9.6 + Apache httpd + mod_wsgi
#
# Uso: sudo bash deploy_production.sh
#

set -e  # Salir si hay error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  Deployment Automático - Diaken Production                ║${NC}"
echo -e "${GREEN}║  Oracle Linux 9.6 + Apache httpd + Django 5.2.6           ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Verificar que se ejecuta como root
if [ "$EUID" -ne 0 ]; then 
   echo -e "${RED}❌ Este script debe ejecutarse como root (sudo)${NC}"
   exit 1
fi

# Variables de configuración
PROJECT_DIR="/opt/www/diaken"
LOGS_DIR="/opt/www/logs"
BACKUPS_DIR="/opt/www/backups"
VENV_DIR="$PROJECT_DIR/venv"
GITHUB_REPO="https://github.com/TU_USUARIO/TU_REPO.git"  # CAMBIAR ESTO
SERVER_NAME="your-server.example.com"  # CAMBIAR ESTO
SERVER_IP="10.100.x.x"  # CAMBIAR ESTO

# Función para mostrar progreso
show_progress() {
    echo -e "${YELLOW}▶ $1${NC}"
}

show_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

show_error() {
    echo -e "${RED}❌ $1${NC}"
}

# ============================================================================
# PASO 1: Actualizar sistema e instalar dependencias
# ============================================================================
show_progress "Paso 1: Actualizando sistema e instalando dependencias..."

dnf update -y > /dev/null 2>&1
show_success "Sistema actualizado"

# Instalar dependencias del sistema
show_progress "Instalando Python, Apache, Git, Ansible..."
dnf install -y python3.9 python3.9-devel python3-pip python3-virtualenv \
    httpd httpd-devel python3-mod_wsgi \
    git ansible \
    gcc gcc-c++ make openssl-devel libffi-devel \
    wget tar > /dev/null 2>&1
show_success "Dependencias del sistema instaladas"

# Instalar govc
show_progress "Instalando govc CLI..."
if [ ! -f /usr/local/bin/govc ]; then
    cd /tmp
    wget -q https://github.com/vmware/govmomi/releases/download/v0.37.0/govc_Linux_x86_64.tar.gz
    tar -C /usr/local/bin -xzf govc_Linux_x86_64.tar.gz govc
    chmod +x /usr/local/bin/govc
    rm -f govc_Linux_x86_64.tar.gz
    show_success "govc instalado: $(govc version)"
else
    show_success "govc ya está instalado: $(govc version)"
fi

# ============================================================================
# PASO 2: Crear estructura de directorios
# ============================================================================
show_progress "Paso 2: Creando estructura de directorios..."

mkdir -p /opt/www
mkdir -p $LOGS_DIR
mkdir -p $BACKUPS_DIR
mkdir -p /opt/www/scripts

show_success "Directorios creados"

# ============================================================================
# PASO 3: Clonar proyecto desde GitHub
# ============================================================================
show_progress "Paso 3: Clonando proyecto desde GitHub..."

if [ -d "$PROJECT_DIR" ]; then
    show_progress "El directorio ya existe. ¿Desea eliminarlo y clonar de nuevo? (y/n)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        rm -rf $PROJECT_DIR
        git clone $GITHUB_REPO $PROJECT_DIR
        show_success "Proyecto clonado desde GitHub"
    else
        show_success "Usando proyecto existente"
    fi
else
    git clone $GITHUB_REPO $PROJECT_DIR
    show_success "Proyecto clonado desde GitHub"
fi

cd $PROJECT_DIR

# ============================================================================
# PASO 4: Configurar Python Virtual Environment
# ============================================================================
show_progress "Paso 4: Configurando Python Virtual Environment..."

if [ ! -d "$VENV_DIR" ]; then
    python3.9 -m venv $VENV_DIR
    show_success "Virtual environment creado"
else
    show_success "Virtual environment ya existe"
fi

$VENV_DIR/bin/pip install --upgrade pip setuptools wheel > /dev/null 2>&1
show_success "pip actualizado"

show_progress "Instalando dependencias Python..."
$VENV_DIR/bin/pip install -r requirements.txt > /dev/null 2>&1
show_success "Dependencias Python instaladas"

# ============================================================================
# PASO 5: Configurar Django para Producción
# ============================================================================
show_progress "Paso 5: Configurando Django para producción..."

# Generar SECRET_KEY
SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')

# Crear settings_production.py
cat > $PROJECT_DIR/diaken/settings_production.py << EOF
from .settings import *

# SECURITY SETTINGS
DEBUG = False
SECRET_KEY = '$SECRET_KEY'

# ALLOWED HOSTS
ALLOWED_HOSTS = [
    '$SERVER_NAME',
    '$SERVER_IP',
    'localhost',
    '127.0.0.1',
]

# CSRF TRUSTED ORIGINS
CSRF_TRUSTED_ORIGINS = [
    'http://$SERVER_NAME',
    'https://$SERVER_NAME',
]

# STATIC FILES
STATIC_ROOT = '$PROJECT_DIR/staticfiles/'
STATIC_URL = '/static/'

MEDIA_ROOT = '$PROJECT_DIR/media/'
MEDIA_URL = '/media/'

# LOGGING
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '$LOGS_DIR/django.log',
            'maxBytes': 1024 * 1024 * 10,
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'INFO',
    },
}

# SECURITY HEADERS
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
EOF

show_success "settings_production.py creado"

# Modificar wsgi.py
sed -i "s/diaken.settings/diaken.settings_production/g" $PROJECT_DIR/diaken/wsgi.py
show_success "wsgi.py configurado"

# Recolectar archivos estáticos
show_progress "Recolectando archivos estáticos..."
$VENV_DIR/bin/python manage.py collectstatic --noinput --settings=diaken.settings_production > /dev/null 2>&1
show_success "Archivos estáticos recolectados"

# Migrar base de datos
show_progress "Migrando base de datos..."
$VENV_DIR/bin/python manage.py migrate --settings=diaken.settings_production > /dev/null 2>&1
show_success "Base de datos migrada"

# ============================================================================
# PASO 6: Configurar permisos
# ============================================================================
show_progress "Paso 6: Configurando permisos..."

chown -R apache:apache $PROJECT_DIR
chown -R apache:apache $LOGS_DIR
chown -R apache:apache $BACKUPS_DIR

chmod 755 $PROJECT_DIR
chmod 755 $PROJECT_DIR/manage.py
chmod -R 755 $PROJECT_DIR/static
chmod -R 755 $PROJECT_DIR/media
chmod -R 755 $PROJECT_DIR/ansible
chmod 660 $PROJECT_DIR/db.sqlite3 2>/dev/null || true

if [ -d "$PROJECT_DIR/media/ssh" ]; then
    chmod 600 $PROJECT_DIR/media/ssh/*.pem 2>/dev/null || true
    chown apache:apache $PROJECT_DIR/media/ssh/*.pem 2>/dev/null || true
fi

show_success "Permisos configurados"

# ============================================================================
# PASO 7: Configurar Apache httpd
# ============================================================================
show_progress "Paso 7: Configurando Apache httpd..."

cat > /etc/httpd/conf.d/diaken.conf << EOF
<VirtualHost *:80>
    ServerName $SERVER_NAME
    ServerAlias $SERVER_IP
    ServerAdmin admin@example.com

    ErrorLog $LOGS_DIR/apache_error.log
    CustomLog $LOGS_DIR/apache_access.log combined

    WSGIDaemonProcess diaken python-home=$VENV_DIR python-path=$PROJECT_DIR
    WSGIProcessGroup diaken
    WSGIScriptAlias / $PROJECT_DIR/diaken/wsgi.py

    <Directory $PROJECT_DIR/diaken>
        <Files wsgi.py>
            Require all granted
        </Files>
    </Directory>

    Alias /static $PROJECT_DIR/staticfiles
    <Directory $PROJECT_DIR/staticfiles>
        Require all granted
        Options -Indexes
    </Directory>

    Alias /media $PROJECT_DIR/media
    <Directory $PROJECT_DIR/media>
        Require all granted
        Options -Indexes
    </Directory>

    <IfModule mod_headers.c>
        Header always set X-Content-Type-Options "nosniff"
        Header always set X-Frame-Options "DENY"
        Header always set X-XSS-Protection "1; mode=block"
    </IfModule>

    Timeout 600
    ProxyTimeout 600
</VirtualHost>
EOF

show_success "Apache configurado"

# Verificar sintaxis de Apache
if httpd -t > /dev/null 2>&1; then
    show_success "Sintaxis de Apache correcta"
else
    show_error "Error en la configuración de Apache"
    httpd -t
    exit 1
fi

# ============================================================================
# PASO 8: Configurar variables de entorno para govc
# ============================================================================
show_progress "Paso 8: Configurando variables de entorno para govc..."

echo ""
echo -e "${YELLOW}Por favor, ingresa las credenciales de vCenter:${NC}"
read -p "vCenter URL (ej: vcenter.example.com): " VCENTER_URL
read -p "vCenter Username (ej: administrator@vsphere.local): " VCENTER_USER
read -sp "vCenter Password: " VCENTER_PASS
echo ""

mkdir -p /etc/systemd/system/httpd.service.d/
cat > /etc/systemd/system/httpd.service.d/override.conf << EOF
[Service]
Environment="GOVC_URL=$VCENTER_URL"
Environment="GOVC_USERNAME=$VCENTER_USER"
Environment="GOVC_PASSWORD=$VCENTER_PASS"
Environment="GOVC_INSECURE=true"
EOF

systemctl daemon-reload
show_success "Variables de entorno de govc configuradas"

# ============================================================================
# PASO 9: Configurar SELinux
# ============================================================================
show_progress "Paso 9: Configurando SELinux..."

setenforce 0
sed -i 's/^SELINUX=enforcing/SELINUX=permissive/' /etc/selinux/config
show_success "SELinux configurado en modo permisivo"

# ============================================================================
# PASO 10: Configurar Firewall
# ============================================================================
show_progress "Paso 10: Configurando Firewall..."

firewall-cmd --permanent --add-service=http > /dev/null 2>&1
firewall-cmd --permanent --add-service=https > /dev/null 2>&1
firewall-cmd --reload > /dev/null 2>&1
show_success "Firewall configurado"

# ============================================================================
# PASO 11: Habilitar y reiniciar Apache
# ============================================================================
show_progress "Paso 11: Habilitando y reiniciando Apache..."

systemctl enable httpd > /dev/null 2>&1
systemctl restart httpd

if systemctl is-active --quiet httpd; then
    show_success "Apache está corriendo"
else
    show_error "Apache no pudo iniciarse"
    systemctl status httpd
    exit 1
fi

# ============================================================================
# PASO 12: Crear scripts de mantenimiento
# ============================================================================
show_progress "Paso 12: Creando scripts de mantenimiento..."

# Script de actualización
cat > /opt/www/scripts/update_diaken.sh << 'EOF'
#!/bin/bash
set -e
cd /opt/www/diaken
cp db.sqlite3 /opt/www/backups/db_backup_$(date +%Y%m%d_%H%M%S).sqlite3
sudo -u apache git pull origin main
sudo -u apache /opt/www/diaken/venv/bin/pip install -r requirements.txt --upgrade
sudo -u apache /opt/www/diaken/venv/bin/python manage.py migrate --settings=diaken.settings_production
sudo -u apache /opt/www/diaken/venv/bin/python manage.py collectstatic --noinput --settings=diaken.settings_production
systemctl restart httpd
echo "✅ Actualización completada!"
EOF

chmod +x /opt/www/scripts/update_diaken.sh

# Script de backup
cat > /opt/www/scripts/backup_db.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/www/backups"
DB_FILE="/opt/www/diaken/db.sqlite3"
DATE=$(date +%Y%m%d_%H%M%S)
cp $DB_FILE $BACKUP_DIR/db_backup_$DATE.sqlite3
cd $BACKUP_DIR
ls -t db_backup_*.sqlite3 | tail -n +31 | xargs -r rm
echo "✅ Backup creado: db_backup_$DATE.sqlite3"
EOF

chmod +x /opt/www/scripts/backup_db.sh

show_success "Scripts de mantenimiento creados"

# ============================================================================
# FINALIZACIÓN
# ============================================================================
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅ DEPLOYMENT COMPLETADO EXITOSAMENTE                    ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}📋 Información del deployment:${NC}"
echo -e "   Proyecto: $PROJECT_DIR"
echo -e "   Logs: $LOGS_DIR"
echo -e "   Backups: $BACKUPS_DIR"
echo ""
echo -e "${YELLOW}🌐 Acceso a la aplicación:${NC}"
echo -e "   URL: http://$SERVER_NAME"
echo -e "   IP: http://$SERVER_IP"
echo ""
echo -e "${YELLOW}📝 Próximos pasos:${NC}"
echo -e "   1. Crear superusuario:"
echo -e "      ${GREEN}sudo -u apache $VENV_DIR/bin/python $PROJECT_DIR/manage.py createsuperuser --settings=diaken.settings_production${NC}"
echo ""
echo -e "   2. Verificar logs:"
echo -e "      ${GREEN}tail -f $LOGS_DIR/apache_error.log${NC}"
echo -e "      ${GREEN}tail -f $LOGS_DIR/django.log${NC}"
echo ""
echo -e "   3. Probar la aplicación:"
echo -e "      ${GREEN}curl http://localhost/${NC}"
echo ""
echo -e "${YELLOW}🔧 Scripts de mantenimiento:${NC}"
echo -e "   Actualizar: ${GREEN}/opt/www/scripts/update_diaken.sh${NC}"
echo -e "   Backup: ${GREEN}/opt/www/scripts/backup_db.sh${NC}"
echo ""
echo -e "${YELLOW}📚 Documentación completa:${NC}"
echo -e "   ${GREEN}$PROJECT_DIR/DEPLOYMENT_PRODUCCION.md${NC}"
echo ""
