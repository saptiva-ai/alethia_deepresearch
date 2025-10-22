#!/bin/bash
# ============================================
# Aletheia Deep Research - Simple Research Example
# ============================================
# Este script demuestra cómo ejecutar una investigación simple
# y obtener el reporte final de forma automática.

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
API_URL="${API_URL:-http://localhost:8000}"
QUERY="${1:-Últimas tendencias en inteligencia artificial 2025}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Aletheia Deep Research - Simple Example${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if API is running
echo -e "\n${YELLOW}1. Verificando que la API esté corriendo...${NC}"
if ! curl -s "$API_URL/health" > /dev/null; then
    echo -e "${RED}❌ Error: La API no está corriendo en $API_URL${NC}"
    echo -e "${YELLOW}Inicia con: uvicorn apps.api.main:app --reload${NC}"
    exit 1
fi
echo -e "${GREEN}✅ API corriendo correctamente${NC}"

# Start research
echo -e "\n${YELLOW}2. Iniciando investigación...${NC}"
echo -e "   Query: ${QUERY}"

RESPONSE=$(curl -s -X POST "$API_URL/research" \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"$QUERY\"}")

# Extract task_id
TASK_ID=$(echo "$RESPONSE" | jq -r '.task_id')

if [ "$TASK_ID" == "null" ] || [ -z "$TASK_ID" ]; then
    echo -e "${RED}❌ Error al iniciar investigación${NC}"
    echo "$RESPONSE" | jq '.'
    exit 1
fi

echo -e "${GREEN}✅ Investigación iniciada${NC}"
echo -e "   Task ID: ${TASK_ID}"

# Monitor status
echo -e "\n${YELLOW}3. Monitoreando progreso...${NC}"
ATTEMPTS=0
MAX_ATTEMPTS=60  # 5 minutes max

while [ $ATTEMPTS -lt $MAX_ATTEMPTS ]; do
    STATUS_RESPONSE=$(curl -s "$API_URL/tasks/$TASK_ID/status")
    STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.status')

    if [ "$STATUS" == "completed" ]; then
        echo -e "${GREEN}✅ Investigación completada!${NC}"
        break
    elif [ "$STATUS" == "failed" ]; then
        echo -e "${RED}❌ La investigación falló${NC}"
        echo "$STATUS_RESPONSE" | jq '.'
        exit 1
    fi

    echo -e "   Status: $STATUS (intento $((ATTEMPTS + 1))/$MAX_ATTEMPTS)"
    sleep 5
    ATTEMPTS=$((ATTEMPTS + 1))
done

if [ $ATTEMPTS -ge $MAX_ATTEMPTS ]; then
    echo -e "${RED}❌ Timeout: La investigación tardó demasiado${NC}"
    exit 1
fi

# Get report
echo -e "\n${YELLOW}4. Obteniendo reporte...${NC}"
REPORT_RESPONSE=$(curl -s "$API_URL/reports/$TASK_ID")

# Save report to file
REPORT_FILE="report_$(date +%Y%m%d_%H%M%S).md"
echo "$REPORT_RESPONSE" | jq -r '.report_md' > "$REPORT_FILE"

# Display summary
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}📊 RESUMEN${NC}"
echo -e "${GREEN}========================================${NC}"

SOURCES=$(echo "$REPORT_RESPONSE" | jq -r '.sources_bib')
echo -e "Task ID:    ${TASK_ID}"
echo -e "Status:     ${GREEN}✅ Completado${NC}"
echo -e "Fuentes:    ${SOURCES}"
echo -e "Reporte:    ${REPORT_FILE}"

echo -e "\n${YELLOW}📄 Preview del reporte:${NC}"
head -n 20 "$REPORT_FILE"
echo -e "\n${YELLOW}... (ver archivo completo: $REPORT_FILE)${NC}"

echo -e "\n${GREEN}🎉 Investigación completada exitosamente!${NC}"
