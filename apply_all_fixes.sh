#!/bin/bash
# Script para aplicar TODOS los fixes del servidor remoto al servidor local
# Versión: 2.6.6
# Fecha: 2025-12-01

set -e

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║     APLICAR TODOS LOS FIXES - SERVIDOR LOCAL                 ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -f "manage.py" ]; then
    echo -e "${RED}❌ Error: No estamos en el directorio de Diaken${NC}"
    echo "Ejecuta este script desde /opt/diaken"
    exit 1
fi

echo -e "${YELLOW}[1/7]${NC} Pull últimos cambios del repositorio..."
git pull origin main
echo -e "${GREEN}✅ Cambios descargados${NC}"
echo ""

echo -e "${YELLOW}[2/7]${NC} Verificar openssh-clients instalado..."
if ! which ssh-keyscan &>/dev/null; then
    echo "Instalando openssh-clients..."
    sudo dnf install -y openssh-clients || sudo yum install -y openssh-clients
    echo -e "${GREEN}✅ openssh-clients instalado${NC}"
else
    echo -e "${GREEN}✅ openssh-clients ya está instalado${NC}"
fi
echo ""

echo -e "${YELLOW}[3/7]${NC} Configurar sudoers para /etc/hosts..."
SUDOERS_FILE="/etc/sudoers.d/diaken-hosts"
if [ ! -f "$SUDOERS_FILE" ]; then
    echo "Creando archivo sudoers..."
    sudo bash -c 'cat > /etc/sudoers.d/diaken-hosts' << 'SUDOEOF'
# Allow diaken user to update /etc/hosts without password
# This is required for automatic inventory management
diaken ALL=(ALL) NOPASSWD: /usr/bin/mv /tmp/diaken_hosts_* /etc/hosts
SUDOEOF
    
    sudo chmod 440 "$SUDOERS_FILE"
    
    # Verificar sintaxis
    if sudo visudo -c -f "$SUDOERS_FILE" &>/dev/null; then
        echo -e "${GREEN}✅ Sudoers configurado correctamente${NC}"
    else
        echo -e "${RED}❌ Error en sintaxis de sudoers${NC}"
        sudo rm -f "$SUDOERS_FILE"
        exit 1
    fi
else
    echo -e "${GREEN}✅ Sudoers ya está configurado${NC}"
fi
echo ""

echo -e "${YELLOW}[4/7]${NC} Verificar permisos de .env..."
if [ -f ".env" ]; then
    sudo chown diaken:diaken .env
    sudo chmod 640 .env
    echo -e "${GREEN}✅ Permisos de .env configurados${NC}"
else
    echo -e "${YELLOW}⚠️  Archivo .env no encontrado${NC}"
fi
echo ""

echo -e "${YELLOW}[5/7]${NC} Verificar directorio .ssh para usuario diaken..."
if [ ! -d "/home/diaken/.ssh" ]; then
    echo "Creando directorio .ssh..."
    sudo mkdir -p /home/diaken/.ssh
    sudo chown diaken:diaken /home/diaken/.ssh
    sudo chmod 700 /home/diaken/.ssh
    echo -e "${GREEN}✅ Directorio .ssh creado${NC}"
else
    echo -e "${GREEN}✅ Directorio .ssh ya existe${NC}"
fi
echo ""

echo -e "${YELLOW}[6/7]${NC} Actualizar /etc/hosts con inventario..."
echo "Ejecutando update_hosts_file..."
sudo -u diaken venv/bin/python manage.py update_hosts_file
echo ""
echo "Contenido actual de /etc/hosts:"
cat /etc/hosts
echo ""
echo -e "${GREEN}✅ /etc/hosts actualizado${NC}"
echo ""

echo -e "${YELLOW}[7/7]${NC} Reiniciar servicio Diaken..."
sudo systemctl restart diaken
echo -e "${GREEN}✅ Servicio reiniciado${NC}"
echo ""

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║     VERIFICACIÓN FINAL                                        ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

echo "1. Verificar sudoers:"
if [ -f "/etc/sudoers.d/diaken-hosts" ]; then
    echo -e "${GREEN}✅ /etc/sudoers.d/diaken-hosts existe${NC}"
else
    echo -e "${RED}❌ /etc/sudoers.d/diaken-hosts NO existe${NC}"
fi
echo ""

echo "2. Verificar openssh-clients:"
if which ssh &>/dev/null && which ssh-keyscan &>/dev/null; then
    echo -e "${GREEN}✅ ssh: $(which ssh)${NC}"
    echo -e "${GREEN}✅ ssh-keyscan: $(which ssh-keyscan)${NC}"
else
    echo -e "${RED}❌ openssh-clients NO instalado correctamente${NC}"
fi
echo ""

echo "3. Verificar /etc/hosts:"
if grep -q "Diaken managed hosts" /etc/hosts 2>/dev/null; then
    echo -e "${GREEN}✅ /etc/hosts contiene hosts de Diaken${NC}"
    echo "Hosts configurados:"
    grep -A 10 "Diaken managed hosts" /etc/hosts | grep -v "^#" | grep -v "^$"
else
    echo -e "${YELLOW}⚠️  /etc/hosts no contiene hosts de Diaken${NC}"
fi
echo ""

echo "4. Verificar servicio Diaken:"
if systemctl is-active --quiet diaken; then
    echo -e "${GREEN}✅ Servicio Diaken está corriendo${NC}"
else
    echo -e "${RED}❌ Servicio Diaken NO está corriendo${NC}"
fi
echo ""

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║     DIAGNÓSTICO DE IPs                                        ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

if [ -f "diagnose_host_ips.py" ]; then
    echo "Ejecutando diagnóstico de IPs..."
    sudo -u diaken venv/bin/python diagnose_host_ips.py
else
    echo -e "${YELLOW}⚠️  diagnose_host_ips.py no encontrado${NC}"
fi
echo ""

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║     TODOS LOS FIXES APLICADOS                                ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}✅ Instalación completada exitosamente${NC}"
echo ""
echo "Próximos pasos:"
echo "1. Verificar que no hay IPs duplicadas en el diagnóstico"
echo "2. Corregir IPs incorrectas en Inventory → Hosts"
echo "3. Configurar permisos de snapshot en vCenter"
echo "4. Probar ejecución de tareas programadas"
echo ""
