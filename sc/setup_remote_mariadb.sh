#!/bin/bash

# Script para configurar el servidor MariaDB remoto
# Ejecutar ESTE script EN EL SERVIDOR MARIADB NUEVO

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=========================================="
echo "CONFIGURACIÓN DE SERVIDOR MARIADB REMOTO"
echo -e "==========================================${NC}"
echo ""

# Verificar que se está ejecutando como root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ Este script debe ejecutarse como root${NC}"
    exit 1
fi

# Verificar que MariaDB está instalado
if ! command -v mysql &> /dev/null; then
    echo -e "${RED}❌ MariaDB no está instalado${NC}"
    echo "Instala MariaDB primero:"
    echo "  sudo dnf install mariadb-server -y"
    echo "  sudo systemctl enable --now mariadb"
    echo "  sudo mysql_secure_installation"
    exit 1
fi

echo -e "${GREEN}✅ MariaDB está instalado${NC}"
echo ""

# Solicitar información
echo -e "${BLUE}Configuración de la base de datos:${NC}"
echo ""

read -p "Nombre de la base de datos [diaken_pdn]: " DB_NAME
DB_NAME=${DB_NAME:-diaken_pdn}

read -p "Usuario de la base de datos [diaken_user]: " DB_USER
DB_USER=${DB_USER:-diaken_user}

read -s -p "Contraseña del usuario: " DB_PASSWORD
echo ""

if [ -z "$DB_PASSWORD" ]; then
    echo -e "${RED}❌ La contraseña no puede estar vacía${NC}"
    exit 1
fi

read -p "Contraseña de root de MariaDB: " -s ROOT_PASSWORD
echo ""
echo ""

# Crear base de datos y usuario
echo -e "${BLUE}=========================================="
echo "PASO 1: CREAR BASE DE DATOS Y USUARIO"
echo -e "==========================================${NC}"
echo ""

mysql -u root -p"$ROOT_PASSWORD" << EOF
-- Crear base de datos
CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Crear usuario
CREATE USER IF NOT EXISTS '$DB_USER'@'%' IDENTIFIED BY '$DB_PASSWORD';

-- Otorgar permisos
GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'%';

-- Aplicar cambios
FLUSH PRIVILEGES;

-- Verificar
SELECT User, Host FROM mysql.user WHERE User='$DB_USER';
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Base de datos y usuario creados${NC}"
else
    echo -e "${RED}❌ Error al crear base de datos y usuario${NC}"
    exit 1
fi
echo ""

# Configurar MariaDB para conexiones remotas
echo -e "${BLUE}=========================================="
echo "PASO 2: CONFIGURAR CONEXIONES REMOTAS"
echo -e "==========================================${NC}"
echo ""

MARIADB_CONF="/etc/my.cnf.d/mariadb-server.cnf"

if [ ! -f "$MARIADB_CONF" ]; then
    echo -e "${YELLOW}⚠️  Archivo de configuración no encontrado en ubicación esperada${NC}"
    echo "Buscando archivo de configuración..."
    MARIADB_CONF=$(find /etc -name "*.cnf" -path "*/mariadb/*" | head -1)
    if [ -z "$MARIADB_CONF" ]; then
        echo -e "${RED}❌ No se encontró archivo de configuración de MariaDB${NC}"
        exit 1
    fi
    echo "Usando: $MARIADB_CONF"
fi

# Hacer backup del archivo de configuración
cp "$MARIADB_CONF" "${MARIADB_CONF}.backup_$(date +%Y%m%d_%H%M%S)"

# Verificar si bind-address ya está configurado
if grep -q "^bind-address" "$MARIADB_CONF"; then
    echo "Actualizando bind-address existente..."
    sed -i 's/^bind-address.*/bind-address = 0.0.0.0/' "$MARIADB_CONF"
else
    echo "Agregando bind-address..."
    # Buscar sección [mysqld] y agregar bind-address
    if grep -q "^\[mysqld\]" "$MARIADB_CONF"; then
        sed -i '/^\[mysqld\]/a bind-address = 0.0.0.0' "$MARIADB_CONF"
    else
        # Si no existe [mysqld], agregarlo al final
        echo -e "\n[mysqld]\nbind-address = 0.0.0.0" >> "$MARIADB_CONF"
    fi
fi

echo -e "${GREEN}✅ Configuración actualizada${NC}"
echo ""

# Reiniciar MariaDB
echo -e "${BLUE}=========================================="
echo "PASO 3: REINICIAR MARIADB"
echo -e "==========================================${NC}"
echo ""

systemctl restart mariadb

if systemctl is-active --quiet mariadb; then
    echo -e "${GREEN}✅ MariaDB reiniciado correctamente${NC}"
else
    echo -e "${RED}❌ Error al reiniciar MariaDB${NC}"
    systemctl status mariadb --no-pager
    exit 1
fi
echo ""

# Configurar firewall
echo -e "${BLUE}=========================================="
echo "PASO 4: CONFIGURAR FIREWALL"
echo -e "==========================================${NC}"
echo ""

if command -v firewall-cmd &> /dev/null; then
    echo "Abriendo puerto 3306..."
    firewall-cmd --permanent --add-port=3306/tcp
    firewall-cmd --reload
    echo -e "${GREEN}✅ Firewall configurado${NC}"
    
    echo "Puertos abiertos:"
    firewall-cmd --list-ports
else
    echo -e "${YELLOW}⚠️  firewalld no está instalado${NC}"
    echo "Si usas otro firewall, asegúrate de abrir el puerto 3306"
fi
echo ""

# Verificar que MariaDB está escuchando en todas las interfaces
echo -e "${BLUE}=========================================="
echo "PASO 5: VERIFICAR CONFIGURACIÓN"
echo -e "==========================================${NC}"
echo ""

echo "Verificando que MariaDB escucha en 0.0.0.0:3306..."
if ss -tlnp | grep -q ":3306.*0.0.0.0"; then
    echo -e "${GREEN}✅ MariaDB escuchando en todas las interfaces${NC}"
else
    echo -e "${YELLOW}⚠️  MariaDB podría no estar escuchando en todas las interfaces${NC}"
    echo "Conexiones actuales:"
    ss -tlnp | grep :3306
fi
echo ""

# Probar conexión local
echo "Probando conexión local..."
if mysql -u "$DB_USER" -p"$DB_PASSWORD" -e "SELECT 1;" &>/dev/null; then
    echo -e "${GREEN}✅ Conexión local exitosa${NC}"
else
    echo -e "${RED}❌ Error en conexión local${NC}"
    exit 1
fi
echo ""

# Obtener IP del servidor
SERVER_IP=$(hostname -I | awk '{print $1}')

# Resumen
echo -e "${GREEN}=========================================="
echo "✅ CONFIGURACIÓN COMPLETADA"
echo -e "==========================================${NC}"
echo ""
echo "Información de conexión:"
echo "  Host: $SERVER_IP"
echo "  Puerto: 3306"
echo "  Base de datos: $DB_NAME"
echo "  Usuario: $DB_USER"
echo "  Contraseña: ********"
echo ""
echo "Próximos pasos:"
echo "  1. Desde el servidor de aplicación, probar conexión:"
echo "     mysql -h $SERVER_IP -u $DB_USER -p $DB_NAME"
echo ""
echo "  2. Si la conexión funciona, ejecutar en el servidor de aplicación:"
echo "     bash migrate_database.sh"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANTE: Guarda esta información de forma segura${NC}"
echo ""

# Guardar información en archivo
INFO_FILE="/root/mariadb_connection_info.txt"
cat > "$INFO_FILE" << EOF
Información de Conexión MariaDB
================================
Fecha: $(date)

Host: $SERVER_IP
Puerto: 3306
Base de datos: $DB_NAME
Usuario: $DB_USER
Contraseña: $DB_PASSWORD

Comando de prueba:
mysql -h $SERVER_IP -u $DB_USER -p $DB_NAME
EOF

chmod 600 "$INFO_FILE"
echo -e "${GREEN}✅ Información guardada en: $INFO_FILE${NC}"
echo ""
