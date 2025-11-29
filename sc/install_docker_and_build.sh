#!/bin/bash
#
# Script para instalar Docker y construir la imagen de Diaken PDN
# Uso: sudo bash install_docker_and_build.sh
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
    echo -e "${RED}No ejecutes este script directamente como root.${NC}"
    echo -e "${YELLOW}Usa: sudo bash install_docker_and_build.sh${NC}"
    exit 1
fi

echo -e "${YELLOW}Usuario detectado: $ACTUAL_USER${NC}"
echo ""

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    VER=$VERSION_ID
else
    echo -e "${RED}No se pudo detectar el sistema operativo${NC}"
    exit 1
fi

echo -e "${BLUE}Sistema operativo detectado: $OS $VER${NC}"
echo ""

# Step 1: Install Docker
echo -e "${GREEN}[1/5] Instalando Docker...${NC}"

if command -v docker &> /dev/null; then
    echo -e "${YELLOW}Docker ya está instalado: $(docker --version)${NC}"
else
    case $OS in
        ubuntu|debian)
            echo "Instalando Docker en Ubuntu/Debian..."
            apt-get update
            apt-get install -y apt-transport-https ca-certificates curl software-properties-common gnupg lsb-release
            
            # Add Docker's official GPG key
            mkdir -p /etc/apt/keyrings
            curl -fsSL https://download.docker.com/linux/$OS/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
            
            # Set up repository
            echo \
              "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/$OS \
              $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
            
            # Install Docker
            apt-get update
            apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
            ;;
            
        rhel|centos|rocky|almalinux|ol)
            echo "Instalando Docker en RHEL/CentOS/Rocky/Oracle Linux..."
            dnf install -y dnf-plugins-core
            dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
            dnf install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
            ;;
            
        *)
            echo -e "${RED}Sistema operativo no soportado: $OS${NC}"
            exit 1
            ;;
    esac
    
    echo -e "${GREEN}Docker instalado correctamente${NC}"
fi

# Step 2: Start and enable Docker
echo -e "${GREEN}[2/5] Iniciando Docker...${NC}"
systemctl start docker
systemctl enable docker
echo -e "${GREEN}Docker iniciado y habilitado${NC}"

# Step 3: Add user to docker group
echo -e "${GREEN}[3/5] Agregando usuario al grupo docker...${NC}"
usermod -aG docker $ACTUAL_USER
echo -e "${GREEN}Usuario $ACTUAL_USER agregado al grupo docker${NC}"
echo -e "${YELLOW}Nota: El usuario necesitará cerrar sesión y volver a entrar para que los cambios surtan efecto${NC}"

# Step 4: Verify Docker installation
echo -e "${GREEN}[4/5] Verificando instalación de Docker...${NC}"
docker --version
docker compose version
echo -e "${GREEN}Docker verificado correctamente${NC}"
echo ""

# Step 5: Build Docker image
echo -e "${GREEN}[5/5] Construyendo imagen Docker de Diaken PDN...${NC}"
echo -e "${YELLOW}Esto puede tomar 5-10 minutos la primera vez...${NC}"
echo ""

PROJECT_DIR="/opt/www/app/diaken-pdn"
cd "$PROJECT_DIR"

# Build with docker compose
echo -e "${BLUE}Ejecutando: docker compose build${NC}"
docker compose build

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  ¡Instalación Completada!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Imagen Docker construida exitosamente${NC}"
echo ""
echo -e "${BLUE}Para levantar los servicios:${NC}"
echo -e "  cd $PROJECT_DIR"
echo -e "  docker compose up -d"
echo ""
echo -e "${BLUE}Para ver logs:${NC}"
echo -e "  docker compose logs -f"
echo ""
echo -e "${BLUE}Para acceder a la aplicación:${NC}"
echo -e "  http://localhost"
echo -e "  Usuario: admin"
echo -e "  Password: admin"
echo ""
echo -e "${YELLOW}Comandos útiles:${NC}"
echo -e "  docker compose ps          # Ver estado"
echo -e "  docker compose restart     # Reiniciar"
echo -e "  docker compose down        # Detener"
echo -e "  docker compose logs -f     # Ver logs"
echo ""
echo -e "${GREEN}¡Todo listo! 🚀${NC}"
