# Aletheia Deep Research

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/Docker-20.10+-blue.svg)](https://www.docker.com/)
[![Tests](https://img.shields.io/badge/tests-117%20passing-green.svg)](.)

**Plataforma de investigación profunda asistida por IA** que utiliza el patrón de investigación iterativa con agentes inteligentes.

---

## ¿Qué es Aletheia?

Aletheia ejecuta investigaciones profundas automáticas usando:
- **Planificación inteligente** - Descompone queries complejas en sub-tareas
- **Investigación paralela** - Ejecuta múltiples búsquedas simultáneamente
- **Evaluación iterativa** - Analiza completitud y refina automáticamente
- **Reportes profesionales** - Genera markdown con evidencias y citas

**Ejemplo:**
```bash
Query: "Latest AI trends 2025"
→ Plan automático con 5 sub-tareas
→ 15 evidencias recolectadas de fuentes verificadas
→ 2 iteraciones de refinamiento
→ Reporte markdown completo en ~90 segundos
```

---

## Arquitectura

```mermaid
graph TB
    subgraph Client["Cliente"]
        HTTP[HTTP REST API]
        WS[WebSocket]
    end

    subgraph API["FastAPI Application"]
        Router[API Router]
        BG[Background Tasks]
        PM[Progress Manager]
    end

    subgraph Domain["Domain Services"]
        Planner[Planner Service<br/>Saptiva Ops]
        Researcher[Researcher Service<br/>Saptiva Ops]
        Evaluator[Evaluator Service<br/>Saptiva Ops]
        Writer[Writer Service<br/>Saptiva Cortex]
        Orchestrator[Iterative Research<br/>Orchestrator]
    end

    subgraph Adapters["Adapters"]
        Saptiva[Saptiva AI Client<br/>LLM Models]
        Tavily[Tavily Search<br/>Web Search API]
        Mongo[(MongoDB<br/>Tasks, Reports, Logs)]
        Telemetry[OpenTelemetry<br/>Tracing & Events]
    end

    HTTP --> Router
    WS --> PM
    Router --> BG
    BG --> Orchestrator
    PM -.->|Real-time updates| WS

    Orchestrator --> Planner
    Orchestrator --> Researcher
    Orchestrator --> Evaluator
    Orchestrator --> Writer

    Planner --> Saptiva
    Researcher --> Saptiva
    Researcher --> Tavily
    Evaluator --> Saptiva
    Writer --> Saptiva

    Orchestrator --> Mongo
    Orchestrator --> PM
    Orchestrator --> Telemetry

    style Domain fill:#e1f5ff
    style Adapters fill:#fff4e1
    style API fill:#f0e1ff
```

**Flujo de Deep Research:**
1. Cliente envía query vía HTTP POST
2. API crea tarea y la ejecuta en background
3. Orchestrator coordina el ciclo iterativo:
   - Planner descompone query en sub-tareas
   - Researcher ejecuta búsquedas en paralelo
   - Evaluator analiza completitud y genera refinamientos
   - Writer sintetiza reporte final
4. Progress Manager envía updates en tiempo real vía WebSocket
5. MongoDB persiste tareas, reportes y logs

---

## Inicio Rápido (5 minutos)

### 1. Requisitos Previos

- **Python 3.11+** (requerido)
- **Docker + Docker Compose** (recomendado)
- **API Keys:** [Saptiva AI](https://saptiva.ai) + [Tavily Search](https://tavily.com)

```bash
# Verificar Python
python3.11 --version
# Debe mostrar: Python 3.11.x o superior
```

---

### 2. Instalación

```bash
# Clonar repositorio
git clone https://github.com/saptiva-ai/alethia_deepresearch.git
cd alethia_deepresearch

# Crear entorno virtual
python3.11 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# Windows: .venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

---

### 3. Configuración

```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar con tus API keys
nano .env
```

**Configuración mínima en `.env`:**
```bash
# REQUERIDO
SAPTIVA_API_KEY=tu_clave_saptiva_aqui
TAVILY_API_KEY=tu_clave_tavily_aqui

# OPCIONAL (usa Docker Compose para MongoDB automático)
MONGODB_URL=mongodb://aletheia:aletheia_password@localhost:27018/aletheia?authSource=admin
```

---

### 4. Iniciar Sistema

**Con Docker (Recomendado):**
```bash
# Inicia API + MongoDB en contenedores
docker compose up -d

# Verificar
docker ps  # Debe mostrar: aletheia-api y aletheia-mongodb
curl http://localhost:8000/health
```

**Sin Docker (Modo Local):**
```bash
# Solo la API, sin MongoDB (in-memory)
uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 📖 Ejemplos de Uso

### Ejemplo 1: Investigación Simple con cURL

```bash
# 1. Iniciar investigación
curl -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" \
  -d '{"query": "Python best practices 2025"}'

# Response:
# {
#   "task_id": "abc-123-def-456",
#   "status": "accepted",
#   "details": "Research task accepted. Use /tasks/{task_id}/status to monitor progress."
# }

# 2. Monitorear status
curl "http://localhost:8000/tasks/abc-123-def-456/status"

# 3. Obtener reporte cuando status=completed
curl "http://localhost:8000/reports/abc-123-def-456" | jq -r '.report_md' > report.md
```

---

### Ejemplo 2: Deep Research con cURL

```bash
# 1. Iniciar deep research con parámetros avanzados
curl -X POST http://localhost:8000/deep-research \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Impact of AI on software development: productivity, job market, and best practices",
    "max_iterations": 3,
    "min_completion_score": 0.80,
    "budget": 150
  }'

# Response:
# {
#   "task_id": "xyz-789-uvw-012",
#   "status": "accepted",
#   "details": "Deep research task accepted with parallel processing. Configuration: 3 iterations, 0.8 min score."
# }

# 2. Monitorear progreso
watch -n 5 "curl -s 'http://localhost:8000/tasks/xyz-789-uvw-012/status' | jq"

# 3. Obtener reporte completo
curl "http://localhost:8000/deep-research/xyz-789-uvw-012" | jq '.report_md' -r > deep_report.md

# 4. Ver métricas de calidad
curl "http://localhost:8000/deep-research/xyz-789-uvw-012" | jq '.quality_metrics'
```

**Parámetros de Deep Research:**
- `max_iterations` (1-5): Número máximo de iteraciones de refinamiento
- `min_completion_score` (0.5-1.0): Score mínimo para considerar completa la investigación
- `budget` (50-300): Número máximo de evidencias a recolectar

---

### Ejemplo 3: WebSocket en Tiempo Real (JavaScript)

```javascript
// Conectar al WebSocket para recibir updates en tiempo real
const taskId = 'xyz-789-uvw-012';
const ws = new WebSocket(`ws://localhost:8000/ws/progress/${taskId}`);

ws.onopen = () => {
  console.log('WebSocket conectado');
};

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);

  // Formato del mensaje:
  // {
  //   "task_id": "xyz-789-uvw-012",
  //   "timestamp": "2025-10-23T12:34:56.789Z",
  //   "event_type": "evidence",  // started, planning, iteration, evidence, evaluation, completed
  //   "message": "Collected 5 new evidence items (total: 12)",
  //   "data": {
  //     "new_evidence": 5,
  //     "total_evidence": 12,
  //     "iteration": 2
  //   }
  // }

  console.log(`[${update.event_type}] ${update.message}`);

  if (update.data) {
    console.log('Data:', update.data);
  }

  // Actualizar UI según el tipo de evento
  switch (update.event_type) {
    case 'started':
      showStatus('Investigación iniciada...');
      break;
    case 'planning':
      showStatus(`Plan creado con ${update.data.subtask_count} sub-tareas`);
      break;
    case 'iteration':
      showStatus(`Iteración ${update.data.iteration}/${update.data.max_iterations}`);
      break;
    case 'evidence':
      updateProgress(update.data.total_evidence);
      break;
    case 'evaluation':
      showScore(update.data.score, update.data.level);
      break;
    case 'completed':
      showSuccess('¡Investigación completada!');
      downloadReport(taskId);
      ws.close();
      break;
    case 'failed':
      showError('La investigación falló');
      ws.close();
      break;
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('WebSocket cerrado');
};

// Opcional: enviar pings periódicos para mantener conexión
setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send('ping');
  }
}, 20000);
```

---

### Ejemplo 4: WebSocket en Tiempo Real (Python)

```python
#!/usr/bin/env python3
"""Monitoreo de deep research con WebSocket."""
import asyncio
import json
import websockets
import requests

async def monitor_research(task_id: str):
    """Monitorea el progreso de una investigación en tiempo real."""
    ws_url = f"ws://localhost:8000/ws/progress/{task_id}"

    print(f"📡 Conectando a WebSocket: {ws_url}")

    try:
        async with websockets.connect(ws_url, ping_interval=20) as websocket:
            print("WebSocket conectado - recibiendo actualizaciones...\n")

            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=30)
                    update = json.loads(message)

                    # Formatear output
                    event_icons = {
                        "started": "🚀",
                        "planning": "📋",
                        "iteration": "🔄",
                        "evidence": "🔍",
                        "evaluation": "📊",
                        "gap_analysis": "🎯",
                        "refinement": "🔧",
                        "report_generation": "📝",
                        "completed": "✅",
                        "failed": "❌"
                    }

                    icon = event_icons.get(update["event_type"], "📌")
                    print(f"{icon} [{update['event_type']}] {update['message']}")

                    # Mostrar data adicional si existe
                    if update.get("data"):
                        data = update["data"]
                        if "iteration" in data and "max_iterations" in data:
                            print(f"   → Iteración: {data['iteration']}/{data['max_iterations']}")
                        if "total_evidence" in data:
                            print(f"   → Evidencias totales: {data['total_evidence']}")
                        if "score" in data:
                            print(f"   → Score: {data['score']:.2%} ({data['level']})")

                    print()  # Línea en blanco

                    # Salir si completó o falló
                    if update["event_type"] in ["completed", "failed"]:
                        break

                except asyncio.TimeoutError:
                    # Enviar ping para mantener conexión
                    await websocket.send("ping")

    except websockets.exceptions.WebSocketException as e:
        print(f"Error de WebSocket: {e}")
    except Exception as e:
        print(f"Error inesperado: {e}")

def start_deep_research(query: str) -> str:
    """Inicia una deep research y retorna el task_id."""
    response = requests.post(
        "http://localhost:8000/deep-research",
        json={
            "query": query,
            "max_iterations": 3,
            "min_completion_score": 0.75,
            "budget": 100
        },
        timeout=10
    )
    response.raise_for_status()
    return response.json()["task_id"]

async def main():
    query = "Latest trends in AI-powered code generation 2025"

    print(f"🔬 Iniciando deep research: {query}\n")

    # Iniciar investigación
    task_id = start_deep_research(query)
    print(f"Task ID: {task_id}\n")

    # Monitorear progreso
    await monitor_research(task_id)

    print(f"\nDescargando reporte...")

    # Obtener reporte
    response = requests.get(f"http://localhost:8000/deep-research/{task_id}")
    report_data = response.json()

    # Guardar reporte
    if report_data.get("status") == "completed":
        with open(f"report_{task_id[:8]}.md", "w") as f:
            f.write(report_data["report_md"])
        print(f"Reporte guardado: report_{task_id[:8]}.md")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Features Principales

### 1. Investigación Simple (`POST /research`)
- Búsqueda web automática con Tavily
- Generación de reporte markdown
- **Tiempo:** ~30-60 segundos

### 2. Deep Research (`POST /deep-research`)
- **Iteraciones múltiples** (1-5 configurables)
- **Evaluación automática** de completitud (score 0-1)
- **Refinamiento inteligente** - Identifica gaps y genera nuevas queries
- **Procesamiento paralelo** - Sub-tareas ejecutadas concurrentemente
- **Tiempo:** ~2-5 minutos

### 3. WebSocket en Tiempo Real (`WS /ws/progress/{task_id}`)
- Updates en tiempo real durante la investigación
- Eventos: `started`, `planning`, `iteration`, `evidence`, `evaluation`, `completed`
- Conexión persistente con keepalive automático

### 4. Persistencia con MongoDB
- **Tasks:** Estado y métricas de investigaciones
- **Reports:** Reportes markdown completos con metadata
- **Logs:** Historial de eventos y errores
- **Fallback:** Modo in-memory si MongoDB no está disponible

---

## Testing

```bash
# Unit tests (117/117 passing)
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# Con coverage
pytest tests/unit/ --cov=. --cov-report=html

# Verificación completa del sistema
python tools/verify_system.py
```

**Resultados actuales:**
- **117 tests passing** (100%)
-  **Coverage: 55.60%** (supera el 50% requerido)

---

## Estructura del Proyecto

```
alethia_deepresearch/
├── apps/api/              # FastAPI application
│   └── main.py           # Endpoints REST + WebSocket
├── domain/               # Business logic
│   ├── models/           # Evidence, Plan, Evaluation
│   └── services/         # Planner, Researcher, Evaluator, Writer
│       └── iterative_research_svc.py  # Orchestrator principal
├── adapters/             # External integrations
│   ├── mongodb/          # MongoDB adapter (Motor async)
│   ├── saptiva_model/    # Saptiva AI client
│   ├── tavily_search/    # Tavily search client
│   ├── websocket/        # WebSocket progress manager
│   └── telemetry/        # OpenTelemetry tracing
├── ports/                # Interfaces (DatabasePort)
├── tests/                # Unit & integration tests
│   ├── unit/            # 116 tests passing
│   └── integration/     # API + MongoDB tests
├── examples/             # Example scripts
│   ├── simple_research.py
│   └── deep_research.py
├── tools/                # Utilities
│   └── verify_system.py  # System verification
├── docs/                 # Documentation
├── docker-compose.yml    # Docker orchestration
└── README.md            # Este archivo
```

---

## Configuración Avanzada

### Variables de Entorno Completas

```bash
# === Saptiva AI (Requerido) ===
SAPTIVA_API_KEY=your_key
SAPTIVA_BASE_URL=https://api.saptiva.com/v1
SAPTIVA_MODEL_PLANNER=Saptiva Ops
SAPTIVA_MODEL_RESEARCHER=Saptiva Ops
SAPTIVA_MODEL_WRITER=Saptiva Cortex

# === Tavily Search (Requerido) ===
TAVILY_API_KEY=your_key

# === MongoDB (Opcional) ===
MONGODB_URL=mongodb://user:pass@host:port/db?authSource=admin
MONGODB_DATABASE=aletheia
MONGO_ROOT_USERNAME=aletheia
MONGO_ROOT_PASSWORD=aletheia_password

# === Application ===
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000

# === Vector Storage (Opcional) ===
VECTOR_BACKEND=none  # none | weaviate
```

### Parámetros de Deep Research

```json
{
  "query": "Your research question",
  "max_iterations": 3,              // 1-5: Número de iteraciones
  "min_completion_score": 0.75,     // 0.5-1.0: Score mínimo para completar
  "budget": 100                     // 50-300: Límite de evidencias
}
```

**Completion Levels:**
- `comprehensive` (0.9-1.0): Investigación completa y profunda
- `substantial` (0.75-0.89): Investigación sólida con cobertura amplia
- `partial` (0.5-0.74): Investigación básica con gaps
- `insufficient` (0-0.49): Investigación insuficiente

---

## Deployment

### Docker Compose (Producción)

```bash
# Build y start
docker compose up -d

# Logs
docker compose logs -f api

# Restart con nuevos cambios
docker compose build api
docker compose up -d api

# Stop
docker compose down
```

### Health Checks

```bash
# API health
curl http://localhost:8000/health

# Response esperado:
# {
#   "status": "healthy",
#   "api_keys": {
#     "saptiva": true,
#     "tavily": true
#   },
#   "mongodb": "connected",
#   "version": "0.2.0"
# }
```

---

## Solución de Problemas

### Error: "Python version too old"
```bash
# Ubuntu/Debian
sudo apt update && sudo apt install python3.11 python3.11-venv

# macOS
brew install python@3.11

# Verificar
python3.11 --version
```

### Error: "API keys not configured"
```bash
# Verifica tu archivo .env
cat .env | grep -E "SAPTIVA_API_KEY|TAVILY_API_KEY"

# Las keys NO deben estar vacías
```

### MongoDB connection issues
```bash
# Verifica que MongoDB esté corriendo
docker ps | grep mongo

# Reinicia MongoDB
docker compose restart mongodb

# Check logs
docker logs aletheia-mongodb
```

### WebSocket timeout
```bash
# Aumenta el timeout en el cliente
# Python:
await websocket.recv(timeout=60)

# JavaScript:
// El navegador maneja timeouts automáticamente
// Envía pings cada 20s para mantener conexión
setInterval(() => ws.send('ping'), 20000);
```

---

## Documentación Adicional

- **[IMPLEMENTATION_SUMMARY.md](docs/IMPLEMENTATION_SUMMARY.md)** - Detalles de implementación
- **[Testing Guide](docs/testing/TESTING_GUIDE.md)** - Guía completa de testing
- **[API Docs](http://localhost:8000/docs)** - Swagger UI interactivo
- **[Changelog](docs/archive/)** - Historial de cambios

---

## Contribuciones

Las contribuciones son bienvenidas! Por favor:

1. Fork el repositorio
2. Crea una branch (`git checkout -b feature/amazing-feature`)
3. Commit tus cambios (`git commit -m 'Add amazing feature'`)
4. Push a la branch (`git push origin feature/amazing-feature`)
5. Abre un Pull Request

**Antes de contribuir:**
- Ejecuta tests: `pytest tests/unit/ -v`
- Verifica linting: `ruff check .`
- Actualiza documentación si es necesario

---

## Agradecimientos

- **[Saptiva AI](https://saptiva.ai)** - Modelos de lenguaje
- **[Tavily](https://tavily.com)** - API de búsqueda web
- **[Together AI](https://together.ai)** - Inspiración del patrón de investigación iterativa

---

## Soporte

- **Issues:** [GitHub Issues](https://github.com/saptiva-ai/alethia_deepresearch/issues)
- **Documentación:** [docs/](docs/)
- **Email:** support@saptiva.ai

---

**Hecho con ❤️ by Saptiva AI Team**


## License

```
                                 Apache License
                           Version 2.0, January 2004
                        http://www.apache.org/licenses/

   Copyright 2025 Saptiva Inc.

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
```

For the complete license text, see the [LICENSE](LICENSE) file in the repository root.
