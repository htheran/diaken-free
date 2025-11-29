#!/bin/bash
#
# Script para instalar Docker en Oracle Linux y construir imagen de Diaken PDN
# Específico para Oracle Linux 9.x
# Uso: sudo bash install_docker_oracle_linux.sh
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Diaken PDN - Docker Setup${NC}"
echo -e "${GREEN}  Oracle Linux 9.x${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Por favor ejecuta este script como root o con sudo${NC}"
    exit 1
fi

# Get the actual user (not root)
ACTUAL_USER=${SUDO_USER:-$USER}
if [ "$ACTUAL_USER" = "root" ]; then
    echo -e "${YELLOW}Ejecutando como root. El usuario será 'root'.${NC}"
    ACTUAL_USER="root"
fi

echo -e "${YELLOW}Usuario: $ACTUAL_USER${NC}"
echo ""

# Detect Oracle Linux version
if [ -f /etc/oracle-release ]; then
    OL_VERSION=$(cat /etc/oracle-release)
    echo -e "${BLUE}Sistema: $OL_VERSION${NC}"
else
    echo -e "${YELLOW}Advertencia: No se detectó Oracle Linux, continuando...${NC}"
fi
echo ""

# Step 1: Remove old Docker versions
echo -e "${GREEN}[1/7] Removiendo versiones antiguas de Docker (si existen)...${NC}"
dnf remove -y docker docker-client docker-client-latest docker-common \
    docker-latest docker-latest-logrotate docker-logrotate docker-engine \
    podman runc 2>/dev/null || true
echo -e "${GREEN}Limpieza completada${NC}"
echo ""

# Step 2: Install required packages
echo -e "${GREEN}[2/7] Instalando paquetes requeridos...${NC}"
dnf install -y dnf-plugins-core yum-utils device-mapper-persistent-data lvm2
echo -e "${GREEN}Paquetes instalados${NC}"
echo ""

# Step 3: Add Docker repository
echo -e "${GREEN}[3/7] Agregando repositorio de Docker...${NC}"
dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
echo -e "${GREEN}Repositorio agregado${NC}"
echo ""

# Step 4: Install Docker
echo -e "${GREEN}[4/7] Instalando Docker Engine...${NC}"
echo -e "${YELLOW}Esto puede tomar varios minutos...${NC}"
dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
echo -e "${GREEN}Docker instalado correctamente${NC}"
echo ""

# Step 5: Start and enable Docker
echo -e "${GREEN}[5/7] Iniciando y habilitando Docker...${NC}"
systemctl start docker
systemctl enable docker
systemctl status docker --no-pager | head -n 5
echo -e "${GREEN}Docker iniciado y habilitado${NC}"
echo ""

# Step 6: Add user to docker group (if not root)
if [ "$ACTUAL_USER" != "root" ]; then
    echo -e "${GREEN}[6/7] Agregando usuario al grupo docker...${NC}"
    usermod -aG docker $ACTUAL_USER
    echo -e "${GREEN}Usuario $ACTUAL_USER agregado al grupo docker${NC}"
    echo -e "${YELLOW}Nota: El usuario necesitará cerrar sesión y volver a entrar${NC}"
else
    echo -e "${GREEN}[6/7] Usuario es root, omitiendo configuración de grupo${NC}"
fi
echo ""

# Step 7: Verify Docker installation
echo -e "${GREEN}[7/7] Verificando instalación...${NC}"
docker --version
docker compose version
echo ""
echo -e "${GREEN}Verificación exitosa${NC}"
echo ""

# Test Docker
echo -e "${BLUE}Probando Docker con hello-world...${NC}"
docker run --rm hello-world
echo ""

# Build Diaken image
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Construyendo Imagen de Diaken PDN${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

PROJECT_DIR="/opt/www/app/diaken-pdn"

if [ ! -d "$PROJECT_DIR" ]; then
    echo -e "${RED}Error: Directorio $PROJECT_DIR no existe${NC}"
    exit 1
fi

cd "$PROJECT_DIR"

echo -e "${YELLOW}Construyendo imagen Docker...${NC}"
echo -e "${YELLOW}Esto tomará 5-10 minutos la primera vez...${NC}"
echo ""

# Build with docker compose
docker compose build

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  ¡Instalación Completada!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${GREEN}✓ Docker instalado y funcionando${NC}"
echo -e "${GREEN}✓ Imagen de Diaken PDN construida${NC}"
echo ""
echo -e "${BLUE}Información del sistema:${NC}"
docker info | grep -E "Server Version|Operating System|OSType|Architecture|CPUs|Total Memory"
echo ""
echo -e "${BLUE}Imágenes disponibles:${NC}"
docker images | grep -E "REPOSITORY|diaken-pdn|redis"
echo ""
echo -e "${YELLOW}Próximos pasos:${NC}"
echo ""
echo -e "1. Levantar los servicios:"
echo -e "   ${BLUE}cd $PROJECT_DIR${NC}"
echo -e "   ${BLUE}docker compose up -d${NC}"
echo ""
echo -e "2. Ver logs:"
echo -e "   ${BLUE}docker compose logs -f${NC}"
echo ""
echo -e "3. Verificar estado:"
echo -e "   ${BLUE}docker compose ps${NC}"
echo ""
echo -e "4. Acceder a la aplicación:"
echo -e "   ${BLUE}http://localhost${NC}"
echo -e "   Usuario: ${GREEN}admin${NC}"
echo -e "   Password: ${GREEN}admin${NC}"
echo ""
echo -e "${YELLOW}Comandos útiles:${NC}"
echo -e "  docker compose ps          # Ver estado de servicios"
echo -e "  docker compose restart     # Reiniciar servicios"
echo -e "  docker compose down        # Detener servicios"
echo -e "  docker compose logs -f     # Ver logs en tiempo real"
echo -e "  docker ps                  # Ver contenedores corriendo"
echo -e "  docker images              # Ver imágenes disponibles"
echo ""
echo -e "${GREEN}¡Todo listo! 🚀${NC}"
echo ""
