#!/bin/bash
# Script para verificar la versión de Python antes de ejecutar la aplicación

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🔍 Verificando versión de Python..."

# Función para extraer versión mayor y menor
get_python_version() {
    python --version 2>&1 | grep -oP '\d+\.\d+' | head -1
}

# Verificar si Python está disponible
if ! command -v python &> /dev/null; then
    echo -e "${RED}❌ Error: Python no está instalado o no está en el PATH${NC}"
    exit 1
fi

# Obtener versión actual
CURRENT_VERSION=$(get_python_version)
REQUIRED_MAJOR=3
REQUIRED_MINOR=11

# Extraer major y minor de la versión actual
CURRENT_MAJOR=$(echo $CURRENT_VERSION | cut -d. -f1)
CURRENT_MINOR=$(echo $CURRENT_VERSION | cut -d. -f2)

echo "📦 Versión actual de Python: $CURRENT_VERSION"
echo "📋 Versión requerida: $REQUIRED_MAJOR.$REQUIRED_MINOR o superior"

# Comparar versiones
if [ "$CURRENT_MAJOR" -lt "$REQUIRED_MAJOR" ] || \
   ([ "$CURRENT_MAJOR" -eq "$REQUIRED_MAJOR" ] && [ "$CURRENT_MINOR" -lt "$REQUIRED_MINOR" ]); then
    echo -e "${RED}❌ Error: Este proyecto requiere Python $REQUIRED_MAJOR.$REQUIRED_MINOR o superior${NC}"
    echo ""
    echo "Tu versión actual es Python $CURRENT_VERSION"
    echo ""
    echo -e "${YELLOW}Para solucionar este problema:${NC}"
    echo ""
    echo "1. Instala Python 3.11:"
    echo "   Ubuntu/Debian: sudo apt install python3.11 python3.11-venv"
    echo "   macOS: brew install python@3.11"
    echo ""
    echo "2. Crea el entorno virtual con Python 3.11:"
    echo "   python3.11 -m venv .venv"
    echo ""
    echo "3. Activa el entorno virtual:"
    echo "   source .venv/bin/activate"
    echo ""
    exit 1
fi

echo -e "${GREEN}✅ Versión de Python correcta${NC}"

# Verificar que estamos en un entorno virtual
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}⚠️  Advertencia: No estás en un entorno virtual${NC}"
    echo "Se recomienda crear y activar un entorno virtual:"
    echo "  python3.11 -m venv .venv"
    echo "  source .venv/bin/activate"
    exit 0
fi

echo -e "${GREEN}✅ Entorno virtual activo: $VIRTUAL_ENV${NC}"
echo ""
echo "🎉 Todo listo para ejecutar Aletheia!"
