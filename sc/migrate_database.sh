#!/bin/bash

# Script de Migración de Base de Datos MariaDB
# Para migrar de MariaDB local a MariaDB remoto

set -e  # Exit on error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=========================================="
echo "MIGRACIÓN DE BASE DE DATOS MARIADB"
echo -e "==========================================${NC}"
echo ""

# Verificar que se está ejecutando como root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ Este script debe ejecutarse como root${NC}"
    exit 1
fi

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
APP_DIR="$SCRIPT_DIR"
BACKUP_DIR="/tmp/db_migration_$(date +%Y%m%d_%H%M%S)"

# Crear directorio de backup
mkdir -p "$BACKUP_DIR"

echo -e "${YELLOW}Directorio de backup: $BACKUP_DIR${NC}"
echo ""

# Función para leer input con valor por defecto
read_with_default() {
    local prompt="$1"
    local default="$2"
    local value
    
    if [ -n "$default" ]; then
        read -p "$prompt [$default]: " value
        echo "${value:-$default}"
    else
        read -p "$prompt: " value
        echo "$value"
    fi
}

# Función para leer password
read_password() {
    local prompt="$1"
    local password
    
    read -s -p "$prompt: " password
    echo "$password"
}

echo -e "${BLUE}=========================================="
echo "PASO 1: INFORMACIÓN DEL SERVIDOR MARIADB"
echo -e "==========================================${NC}"
echo ""

# Solicitar información del servidor MariaDB remoto
DB_HOST=$(read_with_default "IP del servidor MariaDB remoto" "")
DB_PORT=$(read_with_default "Puerto MariaDB" "3306")
DB_NAME=$(read_with_default "Nombre de la base de datos" "diaken_pdn")
DB_USER=$(read_with_default "Usuario de la base de datos" "diaken_user")
echo ""
DB_PASSWORD=$(read_password "Contraseña del usuario de la base de datos")
echo ""
echo ""

# Validar que se proporcionaron los datos
if [ -z "$DB_HOST" ] || [ -z "$DB_PASSWORD" ]; then
    echo -e "${RED}❌ Error: Debes proporcionar la IP del servidor y la contraseña${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Información recopilada${NC}"
echo ""

# Probar conectividad al servidor MariaDB remoto
echo -e "${BLUE}=========================================="
echo "PASO 2: PROBAR CONECTIVIDAD"
echo -e "==========================================${NC}"
echo ""

echo "Probando conexión a $DB_HOST:$DB_PORT..."
if mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" -e "SELECT 1;" &>/dev/null; then
    echo -e "${GREEN}✅ Conexión exitosa al servidor MariaDB remoto${NC}"
else
    echo -e "${RED}❌ No se pudo conectar al servidor MariaDB remoto${NC}"
    echo "Verifica:"
    echo "  - IP y puerto correctos"
    echo "  - Usuario y contraseña correctos"
    echo "  - Firewall permite conexión al puerto 3306"
    echo "  - MariaDB configurado para aceptar conexiones remotas"
    exit 1
fi
echo ""

# Identificar base de datos actual
echo -e "${BLUE}=========================================="
echo "PASO 3: IDENTIFICAR BASE DE DATOS ACTUAL"
echo -e "==========================================${NC}"
echo ""

cd "$APP_DIR"
source venv/bin/activate

# Leer configuración actual
CURRENT_DB_ENGINE=$(grep "^DB_ENGINE=" .env 2>/dev/null | cut -d'=' -f2 || echo "")
CURRENT_DB_NAME=$(grep "^DB_NAME=" .env 2>/dev/null | cut -d'=' -f2 || echo "")

echo "Configuración actual:"
echo "  Engine: $CURRENT_DB_ENGINE"
echo "  Name: $CURRENT_DB_NAME"
echo ""

# Determinar si es MariaDB/MySQL o SQLite
if [[ "$CURRENT_DB_ENGINE" == *"mysql"* ]]; then
    echo "Base de datos actual: MariaDB/MySQL"
    DB_TYPE="mysql"
elif [[ "$CURRENT_DB_ENGINE" == *"sqlite"* ]] || [ -z "$CURRENT_DB_ENGINE" ]; then
    echo "Base de datos actual: SQLite"
    DB_TYPE="sqlite"
else
    echo -e "${YELLOW}⚠️  Tipo de base de datos no reconocido: $CURRENT_DB_ENGINE${NC}"
    DB_TYPE="unknown"
fi
echo ""

# Hacer backup de la base de datos actual
echo -e "${BLUE}=========================================="
echo "PASO 4: BACKUP DE BASE DE DATOS ACTUAL"
echo -e "==========================================${NC}"
echo ""

if [ "$DB_TYPE" = "mysql" ]; then
    echo "Haciendo backup de MariaDB local..."
    CURRENT_DB_USER=$(grep "^DB_USER=" .env 2>/dev/null | cut -d'=' -f2 || echo "root")
    CURRENT_DB_PASSWORD=$(grep "^DB_PASSWORD=" .env 2>/dev/null | cut -d'=' -f2 || echo "")
    
    if [ -n "$CURRENT_DB_PASSWORD" ]; then
        mysqldump -u "$CURRENT_DB_USER" -p"$CURRENT_DB_PASSWORD" "$CURRENT_DB_NAME" > "$BACKUP_DIR/database_backup.sql"
    else
        echo "Ingresa la contraseña de MariaDB local:"
        mysqldump -u "$CURRENT_DB_USER" -p "$CURRENT_DB_NAME" > "$BACKUP_DIR/database_backup.sql"
    fi
    
    echo -e "${GREEN}✅ Backup creado: $BACKUP_DIR/database_backup.sql${NC}"
    
elif [ "$DB_TYPE" = "sqlite" ]; then
    echo "Haciendo backup de SQLite..."
    if [ -f "$APP_DIR/db.sqlite3" ]; then
        cp "$APP_DIR/db.sqlite3" "$BACKUP_DIR/db.sqlite3.backup"
        echo -e "${GREEN}✅ Backup creado: $BACKUP_DIR/db.sqlite3.backup${NC}"
        
        # Exportar a SQL para importar en MariaDB
        echo "Exportando datos para MariaDB..."
        python manage.py dumpdata --natural-foreign --natural-primary > "$BACKUP_DIR/data.json"
        echo -e "${GREEN}✅ Datos exportados: $BACKUP_DIR/data.json${NC}"
    else
        echo -e "${RED}❌ No se encontró db.sqlite3${NC}"
        exit 1
    fi
else
    echo -e "${RED}❌ No se puede hacer backup de tipo de base de datos desconocido${NC}"
    exit 1
fi

# Verificar tamaño del backup
BACKUP_SIZE=$(du -h "$BACKUP_DIR" | tail -1 | awk '{print $1}')
echo "Tamaño del backup: $BACKUP_SIZE"
echo ""

# Importar datos al servidor MariaDB remoto
echo -e "${BLUE}=========================================="
echo "PASO 5: IMPORTAR DATOS AL SERVIDOR REMOTO"
echo -e "==========================================${NC}"
echo ""

if [ "$DB_TYPE" = "mysql" ]; then
    echo "Importando backup SQL al servidor remoto..."
    mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" < "$BACKUP_DIR/database_backup.sql"
    echo -e "${GREEN}✅ Datos importados exitosamente${NC}"
    
elif [ "$DB_TYPE" = "sqlite" ]; then
    echo "Para SQLite, se usará Django para migrar los datos..."
    echo "Esto se hará después de configurar la nueva conexión."
fi
echo ""

# Detener servicios
echo -e "${BLUE}=========================================="
echo "PASO 6: DETENER SERVICIOS"
echo -e "==========================================${NC}"
echo ""

echo "Deteniendo Apache..."
systemctl stop httpd
echo -e "${GREEN}✅ Apache detenido${NC}"

echo "Deteniendo Celery..."
systemctl stop celery-diaken
echo -e "${GREEN}✅ Celery detenido${NC}"
echo ""

# Backup del archivo .env
echo -e "${BLUE}=========================================="
echo "PASO 7: ACTUALIZAR CONFIGURACIÓN"
echo -e "==========================================${NC}"
echo ""

echo "Haciendo backup de .env..."
cp "$APP_DIR/.env" "$BACKUP_DIR/.env.backup"
echo -e "${GREEN}✅ Backup de .env creado${NC}"

# Actualizar .env
echo "Actualizando configuración de base de datos..."

# Remover líneas antiguas de DB_*
sed -i '/^DB_ENGINE=/d' "$APP_DIR/.env"
sed -i '/^DB_NAME=/d' "$APP_DIR/.env"
sed -i '/^DB_USER=/d' "$APP_DIR/.env"
sed -i '/^DB_PASSWORD=/d' "$APP_DIR/.env"
sed -i '/^DB_HOST=/d' "$APP_DIR/.env"
sed -i '/^DB_PORT=/d' "$APP_DIR/.env"
sed -i '/^DB_SOCKET=/d' "$APP_DIR/.env"

# Agregar nuevas líneas
cat >> "$APP_DIR/.env" << EOF

# Database Configuration (MariaDB Remoto)
DB_ENGINE=django.db.backends.mysql
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_HOST=$DB_HOST
DB_PORT=$DB_PORT
EOF

echo -e "${GREEN}✅ Configuración actualizada${NC}"
echo ""

# Verificar instalación de mysqlclient
echo -e "${BLUE}=========================================="
echo "PASO 8: VERIFICAR DEPENDENCIAS"
echo -e "==========================================${NC}"
echo ""

cd "$APP_DIR"
source venv/bin/activate

if python -c "import MySQLdb" 2>/dev/null; then
    echo -e "${GREEN}✅ mysqlclient ya está instalado${NC}"
else
    echo "Instalando mysqlclient..."
    pip install mysqlclient
    echo -e "${GREEN}✅ mysqlclient instalado${NC}"
fi
echo ""

# Probar conexión desde Django
echo -e "${BLUE}=========================================="
echo "PASO 9: PROBAR CONEXIÓN DESDE DJANGO"
echo -e "==========================================${NC}"
echo ""

python manage.py shell << 'PYEOF'
from django.db import connection
try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        print(f"✅ Conexión exitosa a MariaDB: {version[0]}")
except Exception as e:
    print(f"❌ Error de conexión: {e}")
    exit(1)
PYEOF

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Error al conectar desde Django${NC}"
    echo "Restaurando configuración anterior..."
    cp "$BACKUP_DIR/.env.backup" "$APP_DIR/.env"
    systemctl start httpd
    systemctl start celery-diaken
    exit 1
fi
echo ""

# Si venimos de SQLite, importar datos usando Django
if [ "$DB_TYPE" = "sqlite" ]; then
    echo -e "${BLUE}=========================================="
    echo "PASO 10: MIGRAR DATOS DESDE SQLITE"
    echo -e "==========================================${NC}"
    echo ""
    
    echo "Aplicando migraciones..."
    python manage.py migrate
    
    echo "Importando datos..."
    python manage.py loaddata "$BACKUP_DIR/data.json"
    
    echo -e "${GREEN}✅ Datos migrados desde SQLite${NC}"
    echo ""
fi

# Aplicar migraciones
echo -e "${BLUE}=========================================="
echo "PASO 11: APLICAR MIGRACIONES"
echo -e "==========================================${NC}"
echo ""

python manage.py migrate
echo -e "${GREEN}✅ Migraciones aplicadas${NC}"
echo ""

# Verificar datos
echo -e "${BLUE}=========================================="
echo "PASO 12: VERIFICAR INTEGRIDAD DE DATOS"
echo -e "==========================================${NC}"
echo ""

python manage.py shell << 'PYEOF'
from django.contrib.auth.models import User
from inventory.models import Host, Group, Environment
from playbooks.models import Playbook

print("Conteo de registros:")
print(f"  Usuarios: {User.objects.count()}")
print(f"  Hosts: {Host.objects.count()}")
print(f"  Grupos: {Group.objects.count()}")
print(f"  Ambientes: {Environment.objects.count()}")
print(f"  Playbooks: {Playbook.objects.count()}")
PYEOF
echo ""

# Reiniciar servicios
echo -e "${BLUE}=========================================="
echo "PASO 13: REINICIAR SERVICIOS"
echo -e "==========================================${NC}"
echo ""

echo "Iniciando Apache..."
systemctl start httpd
systemctl status httpd --no-pager
echo -e "${GREEN}✅ Apache iniciado${NC}"
echo ""

echo "Iniciando Celery..."
systemctl start celery-diaken
systemctl status celery-diaken --no-pager
echo -e "${GREEN}✅ Celery iniciado${NC}"
echo ""

# Resumen
echo -e "${GREEN}=========================================="
echo "✅ MIGRACIÓN COMPLETADA EXITOSAMENTE"
echo -e "==========================================${NC}"
echo ""
echo "Resumen:"
echo "  Base de datos remota: $DB_HOST:$DB_PORT"
echo "  Base de datos: $DB_NAME"
echo "  Usuario: $DB_USER"
echo "  Backup guardado en: $BACKUP_DIR"
echo ""
echo "Próximos pasos:"
echo "  1. Probar la aplicación web"
echo "  2. Verificar que todas las funcionalidades trabajen"
echo "  3. Configurar backups automáticos en el servidor MariaDB"
echo "  4. Considerar eliminar la base de datos local (después de verificar)"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANTE: Guarda el directorio de backup: $BACKUP_DIR${NC}"
echo ""
