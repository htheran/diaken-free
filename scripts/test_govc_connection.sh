#!/bin/bash
# Script para probar la conexión de govc con vCenter
# Uso: sudo -u apache bash scripts/test_govc_connection.sh

echo "=========================================="
echo "Test de Conexión govc con vCenter"
echo "=========================================="
echo ""

# Verificar que govc está instalado
echo "1. Verificando instalación de govc..."
if /usr/local/bin/govc version &>/dev/null; then
    echo "   ✅ govc instalado: $(/usr/local/bin/govc version)"
else
    echo "   ❌ ERROR: govc no está instalado o no se puede ejecutar"
    exit 1
fi
echo ""

# Leer credenciales desde .env
echo "2. Leyendo credenciales desde .env..."
# Get script directory and navigate to project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
if [ -f "$PROJECT_DIR/.env" ]; then
    source "$PROJECT_DIR/.env"
    echo "   ✅ Archivo .env cargado"
else
    echo "   ❌ ERROR: Archivo .env no encontrado"
    exit 1
fi
echo ""

# Verificar que las variables están definidas
echo "3. Verificando variables de entorno..."
if [ -z "$VCENTER_HOST" ] || [ -z "$VCENTER_USER" ] || [ -z "$VCENTER_PASSWORD" ]; then
    echo "   ❌ ERROR: Variables VCENTER_HOST, VCENTER_USER o VCENTER_PASSWORD no definidas en .env"
    exit 1
fi
echo "   ✅ VCENTER_HOST: $VCENTER_HOST"
echo "   ✅ VCENTER_USER: $VCENTER_USER"
echo "   ✅ VCENTER_PASSWORD: [OCULTO]"
echo ""

# Configurar variables de entorno para govc
export GOVC_URL="$VCENTER_HOST"
export GOVC_USERNAME="$VCENTER_USER"
export GOVC_PASSWORD="$VCENTER_PASSWORD"
export GOVC_INSECURE="true"

# Probar conexión con vCenter
echo "4. Probando conexión con vCenter..."
if /usr/local/bin/govc about &>/dev/null; then
    echo "   ✅ Conexión exitosa con vCenter"
    echo ""
    echo "   Información de vCenter:"
    /usr/local/bin/govc about | head -5
else
    echo "   ❌ ERROR: No se pudo conectar con vCenter"
    echo ""
    echo "   Detalles del error:"
    /usr/local/bin/govc about
    exit 1
fi
echo ""

# Listar redes disponibles
echo "5. Listando redes disponibles..."
if /usr/local/bin/govc ls network &>/dev/null; then
    echo "   ✅ Redes disponibles:"
    /usr/local/bin/govc ls network | head -10
else
    echo "   ❌ ERROR: No se pudieron listar las redes"
    /usr/local/bin/govc ls network
    exit 1
fi
echo ""

echo "=========================================="
echo "✅ TODAS LAS PRUEBAS PASARON"
echo "=========================================="
echo ""
echo "govc está correctamente configurado y puede conectarse a vCenter."
echo "El cambio de red debería funcionar correctamente ahora."
