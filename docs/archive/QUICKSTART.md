# 🚀 Guía de Inicio Rápido - Aletheia Deep Research

Esta guía te llevará de **cero a investigación funcionando en 5 minutos**.

---

## ⚡ Setup en 4 Pasos

### Paso 1: Requisitos Previos

Necesitas tener instalado:
- **Python 3.11+** (⚠️ REQUERIDO)
- **Git**
- **Docker + Docker Compose** (recomendado para MongoDB)

Verifica tu versión de Python:
```bash
python3.11 --version
# Debe mostrar: Python 3.11.x o superior
```

Si no tienes Python 3.11:
```bash
# Ubuntu/Debian
sudo apt update && sudo apt install python3.11 python3.11-venv

# macOS
brew install python@3.11
```

---

### Paso 2: Clonar e Instalar

```bash
# 1. Clonar el repositorio
git clone https://github.com/saptiva-ai/alethia_deepresearch.git
cd alethia_deepresearch

# 2. Crear entorno virtual con Python 3.11
python3.11 -m venv .venv

# 3. Activar entorno virtual
source .venv/bin/activate  # Linux/Mac
# En Windows: .venv\Scripts\activate

# 4. Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt
```

---

### Paso 3: Configurar API Keys

```bash
# 1. Copiar archivo de ejemplo
cp .env.example .env

# 2. Editar .env con tus API keys
nano .env  # o usa tu editor favorito
```

**Configuración mínima en `.env`:**
```bash
# === REQUERIDO: Obtén tus keys ===
SAPTIVA_API_KEY=tu_clave_saptiva_aqui      # https://saptiva.ai
TAVILY_API_KEY=tu_clave_tavily_aqui        # https://tavily.com

# === MongoDB (Opcional - usa Docker Compose) ===
MONGODB_URL=mongodb://aletheia:aletheia_password@localhost:27018/aletheia?authSource=admin
MONGODB_DATABASE=aletheia
```

**Nota:** Sin MongoDB, el sistema funciona pero los datos se pierden al reiniciar.

---

### Paso 4: Iniciar el Sistema

#### Opción A: Con Docker Compose (Recomendado)

Incluye MongoDB automáticamente:

```bash
# Iniciar todo (API + MongoDB)
docker-compose up -d

# Verificar que esté corriendo
curl http://localhost:8000/health

# Ver logs
docker-compose logs -f api
```

#### Opción B: Sin Docker (Modo Desarrollo)

```bash
# Asegúrate de estar en el entorno virtual
source .venv/bin/activate

# Iniciar la API
uvicorn apps.api.main:app --reload --port 8000

# En otra terminal, verifica:
curl http://localhost:8000/health
```

---

## ✅ Verificar Instalación

Ejecuta el script de verificación:

```bash
python tools/verify_system.py
```

Este script verificará:
- ✅ API Keys configuradas
- ✅ API corriendo correctamente
- ✅ MongoDB conectado (si está configurado)
- ✅ Research endpoint funcionando
- ✅ Deep Research con WebSocket funcionando
- ✅ Guardado de reportes
- ✅ Trazabilidad completa

**Salida esperada:**
```
🔍 VERIFICACIÓN COMPLETA DEL SISTEMA ALETHEIA
======================================================================

1️⃣  VERIFICACIÓN DE VARIABLES DE ENTORNO
======================================================================
✅ PASS - SAPTIVA_API_KEY configurada
✅ PASS - TAVILY_API_KEY configurada
✅ PASS - MONGODB_URL configurada

2️⃣  VERIFICACIÓN DE API
======================================================================
✅ PASS - API Health Check
✅ PASS - API Version
✅ PASS - Saptiva API Key (en API)
✅ PASS - Tavily API Key (en API)

...

📋 RESUMEN FINAL
======================================================================
   Tests ejecutados: 20
   ✅ Pasados: 20
   ❌ Fallados: 0

   🎉 ¡TODOS LOS TESTS PASARON! El sistema está funcionando correctamente.
```

---

## 🧪 Pruebas Rápidas

### 1. Investigación Simple (30-60 segundos)

```bash
# Iniciar investigación
curl -X POST "http://localhost:8000/research" \
  -H "Content-Type: application/json" \
  -d '{"query": "Últimas tendencias en inteligencia artificial 2025"}'

# Respuesta:
# {"task_id": "abc123...", "status": "accepted"}

# Obtener reporte (espera ~30 segundos primero)
curl "http://localhost:8000/reports/abc123..."
```

### 2. Deep Research con Feedback en Tiempo Real (2-5 minutos)

```bash
# Usar el script de ejemplo (incluye WebSocket)
python examples/deep_research.py "Impacto de la IA en el mercado laboral"

# Verás actualizaciones en tiempo real:
# 🚀 Starting deep research...
# 📋 Research plan created with 5 sub-tasks
# 🔄 Starting iteration 1/3
# 🔍 Collected 12 new evidence items
# 📊 Completion score: 45%
# ...
```

---

## 📚 Documentación de la API

Una vez que el sistema esté corriendo, visita:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

Ahí encontrarás todos los endpoints interactivos.

---

## 🔍 Endpoints Principales

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/research` | POST | Investigación simple (30-60s) |
| `/deep-research` | POST | Investigación profunda (2-5 min) |
| `/reports/{task_id}` | GET | Obtener reporte |
| `/deep-research/{task_id}` | GET | Obtener reporte deep research |
| `/ws/progress/{task_id}` | WebSocket | Actualizaciones en tiempo real |

---

## 📊 Ver Reportes Guardados (MongoDB)

Si usas MongoDB, puedes ver todos los reportes guardados:

```bash
# Conectar a MongoDB
docker exec -it aletheia-mongodb mongosh \
  -u aletheia -p aletheia_password \
  --authenticationDatabase admin \
  aletheia

# Comandos útiles dentro de mongosh:
db.tasks.find().pretty()              # Ver todas las tareas
db.reports.find().pretty()            # Ver todos los reportes
db.tasks.find({status: "completed"})  # Solo tareas completadas
db.logs.find().sort({timestamp: -1}).limit(10)  # Últimos 10 logs
```

---

## 🐛 Solución de Problemas

### La API no inicia

```bash
# Verifica que estás en el entorno virtual
source .venv/bin/activate

# Verifica la versión de Python
python --version  # Debe ser 3.11+

# Reinstala dependencias
pip install -r requirements.txt

# Intenta iniciar de nuevo
uvicorn apps.api.main:app --reload
```

### "API key not configured"

```bash
# Verifica que las keys estén en .env
cat .env | grep API_KEY

# Deben verse así:
# SAPTIVA_API_KEY=va-ai-xxxxx
# TAVILY_API_KEY=tvly-xxxxx

# NO deben ser "pon_tu_api_key_aqui"
```

### "Task not found" después de crear tarea

Esto pasa si MongoDB no está configurado y reinicias la API. Solución:

```bash
# Opción 1: Usar Docker Compose (incluye MongoDB)
docker-compose up -d

# Opción 2: Configurar MongoDB local
# Ver README.md sección "Configuración de MongoDB Local"
```

### WebSocket no conecta

```bash
# Verifica que la API esté corriendo
curl http://localhost:8000/health

# Verifica que websockets esté instalado
pip install websockets==12.0

# Intenta el ejemplo de nuevo
python examples/deep_research.py "test query"
```

---

## 📖 Siguientes Pasos

1. **Lee el README completo:** [README.md](README.md)
2. **Explora ejemplos:** Mira `examples/`
3. **Configura MongoDB:** Para persistencia de datos
4. **Personaliza:** Modifica parámetros de investigación
5. **Integra:** Usa la API en tu aplicación

---

## 💡 Recursos Útiles

- **Documentación Completa:** [README.md](README.md)
- **Cambios Recientes:** [SIMPLIFICATION.md](SIMPLIFICATION.md)
- **Issues:** [GitHub Issues](https://github.com/saptiva-ai/alethia_deepresearch/issues)
- **Saptiva AI:** https://saptiva.ai
- **Tavily Search:** https://tavily.com

---

## 🎯 TL;DR - Comandos Rápidos

```bash
# Setup completo
git clone https://github.com/saptiva-ai/alethia_deepresearch.git
cd alethia_deepresearch
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edita .env con tus API keys

# Opción A: Docker
docker-compose up -d

# Opción B: Local
uvicorn apps.api.main:app --reload

# Verificar
python tools/verify_system.py

# Probar
python examples/deep_research.py "Tu consulta aquí"
```

---

**¿Problemas?** Abre un issue en [GitHub](https://github.com/saptiva-ai/alethia_deepresearch/issues)

**¡Listo para investigar!** 🚀
