#!/bin/bash
# Script de sincronización forzada entre servidores
# Uso: ./force_sync.sh

set -e

echo "=========================================="
echo "SINCRONIZACIÓN FORZADA DE REPOSITORIO"
echo "=========================================="

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory and navigate to project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
cd "$PROJECT_DIR"

echo -e "${YELLOW}[1/6]${NC} Verificando estado actual..."
git status

echo -e "\n${YELLOW}[2/6]${NC} Descartando cambios locales en archivos compilados..."
git checkout -- deploy/__pycache__/*.pyc 2>/dev/null || true
git checkout -- playbooks/__pycache__/*.pyc 2>/dev/null || true
git checkout -- settings/__pycache__/*.pyc 2>/dev/null || true

echo -e "\n${YELLOW}[3/6]${NC} Obteniendo últimos cambios del repositorio remoto..."
git fetch origin main

echo -e "\n${YELLOW}[4/6]${NC} Reseteando a la última versión remota..."
git reset --hard origin/main

echo -e "\n${YELLOW}[5/6]${NC} Limpiando archivos no rastreados..."
git clean -fd

echo -e "\n${YELLOW}[6/6]${NC} Reiniciando servicios..."
sudo systemctl restart httpd
sudo systemctl restart celery-diaken

echo -e "\n${GREEN}✅ SINCRONIZACIÓN COMPLETADA${NC}"
echo "=========================================="
echo "Últimos commits:"
git log --oneline -5

echo -e "\nEstado actual:"
git status
