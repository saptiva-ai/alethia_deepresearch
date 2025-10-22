# Aletheia (ἀλήθεια – desocultamiento de la verdad)

[![CI Status](https://github.com/saptiva-ai/alethia_deepresearch/workflows/CI%20-%20Quality%20Checks/badge.svg)](https://github.com/saptiva-ai/alethia_deepresearch/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

Aletheia es una plataforma de investigación asistida por agentes que separa claramente el
*Dominio* de la orquestación y de las integraciones externas. El objetivo del repositorio es
ofrecer un pipeline reproducible para planear, ejecutar y sintetizar investigaciones
aprovechando modelos de lenguaje de Saptiva y fuentes externas (Tavily, documentos locales, etc.).

> **Estado:** ✅ **En producción** - API completamente operativa, configuración minimalista, deployment simplificado.

> 📝 **¿Vienes de una versión anterior?** El proyecto ha sido simplificado para setup instantáneo. Ver [SIMPLIFICATION.md](SIMPLIFICATION.md) para detalles de los cambios y guía de migración.

## 🎯 Configuración Minimalista

Este proyecto está optimizado para un **setup simple y directo**:

✅ **Solo 2 API Keys requeridas**: Saptiva + Tavily
✅ **Sin dependencias de servicios externos**: Sin bases de datos, sin contenedores obligatorios
✅ **Python 3.11+ como único requisito** del sistema
✅ **Docker opcional**: Funciona perfectamente sin contenedores
✅ **Zero config**: Valores por defecto listos para producción

**Tiempo de setup:** < 5 minutos desde cero

---

## 🚀 Enlaces Rápidos

- **[Configuración Rápida](#-configuración-rápida)**: Setup en < 5 minutos
- **[API Docs](http://localhost:8000/docs)**: Swagger UI interactivo (cuando el servidor esté corriendo)
- **[Health Check](http://localhost:8000/health)**: Verificar estado del sistema
- **[Deployment](#-deployment)**: Guías de despliegue
- **[Arquitectura](#-arquitectura)**: Diseño del sistema
- **[SIMPLIFICATION.md](SIMPLIFICATION.md)**: Guía de la configuración minimalista

---

## 📦 Qué incluye el repositorio

- **`apps/api`**: Aplicación FastAPI que expone endpoints de investigación y salud
- **`domain`**: Reglas de negocio (planificación, evaluación, orquestación iterativa y modelos)
- **`adapters`**: Integraciones concretas (Saptiva, Tavily, extracción de documentos, telemetría, almacenamiento vectorial, etc.)
- **`ports`**: Interfaces que definen contratos entre el dominio y los adapters
- **`infra`**: Infraestructura como código (Docker, Kubernetes)
- **`scripts`**: Scripts de deployment y utilidades de desarrollo
- **`tests`**: Suites unitarias e integrales (99 tests, cobertura 23%+)
- **`docs`**: Material de referencia y diagramas adicionales

---

## 🛠 Requisitos Mínimos

### Esenciales (Requeridos)
- **Python 3.11+** ⚠️ **REQUERIDO** - El proyecto usa sintaxis moderna de Python
- **pip** y **virtualenv** para gestión de dependencias
- **API Keys**:
  - Saptiva AI: [Obtener key](https://saptiva.ai)
  - Tavily Search: [Obtener key](https://tavily.com)

### Opcionales (No requeridos por defecto)
- **Docker** - Solo para deployment en contenedores
- **Weaviate** - Solo si activas vector database (`VECTOR_BACKEND=weaviate`)
- **Tesseract OCR** - Solo para procesamiento OCR de imágenes
- **Jaeger** - Solo para trazabilidad distribuida avanzada

> **Nota importante**: El sistema funciona completamente sin ningún servicio externo. La configuración minimalista es ideal para desarrollo y producción.

### Verificar Python 3.11

⚠️ **IMPORTANTE**: Verifica tu versión de Python antes de continuar:

```bash
python3.11 --version  # Debe mostrar Python 3.11.x o superior
```

**Si no tienes Python 3.11:**

```bash
# Ubuntu/Debian
sudo apt update && sudo apt install python3.11 python3.11-venv python3.11-dev

# macOS (Homebrew)
brew install python@3.11
```

---

## ⚡ Configuración Rápida

### 1. Clonar y configurar entorno

⚠️ **IMPORTANTE: Usa `python3.11` explícitamente en todos los comandos**

```bash
git clone https://github.com/saptiva-ai/alethia_deepresearch.git
cd alethia_deepresearch

# Crear entorno virtual con Python 3.11
python3.11 -m venv .venv

# Activar entorno virtual
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Verificar que estás usando Python 3.11
python --version  # Debe mostrar Python 3.11.x
```

### 2. Instalar dependencias

```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .[dev]  # Incluye herramientas de desarrollo
```

### 3. Configurar variables de entorno

```bash
cp .env.example .env
```

Edita `.env` con tus API keys:

```bash
# === REQUERIDO ===
SAPTIVA_API_KEY=tu_clave_saptiva_aqui
TAVILY_API_KEY=tu_clave_tavily_aqui

# === Configuración predeterminada (ya configurada) ===
SAPTIVA_BASE_URL=https://api.saptiva.ai/v1
VECTOR_BACKEND=none
ENVIRONMENT=development
```

**Nota**: Los demás valores ya tienen defaults apropiados. Solo necesitas las API keys.

### 4. Verificar configuración (opcional pero recomendado)

```bash
# Ejecutar script de verificación
./scripts/check_python_version.sh
```

### 5. Ejecutar la API

```bash
# Asegúrate de que el entorno virtual esté activado
python --version  # Debe mostrar Python 3.11.x

# Ejecutar el servidor
uvicorn apps.api.main:app --reload --port 8000
```

🎉 **API disponible en:** http://localhost:8000/docs

**Notas importantes:**
- ✅ El servidor usa **modo minimalista** por defecto (sin Weaviate, sin servicios externos)
- ✅ Si obtienes errores de sintaxis como `TypeError: unsupported operand type(s) for |`, estás usando Python < 3.10
- ✅ Los warnings de Pydantic son normales y no afectan la funcionalidad

---

## 🧪 Pruebas y Calidad de Código

El proyecto mantiene estándares profesionales con CI/CD automatizado:

### Ejecutar verificaciones localmente

```bash
# Linting y formato
ruff check .
ruff check . --fix  # Corregir problemas automáticamente

# Type checking
mypy domain/models --ignore-missing-imports

# Tests unitarios (99 tests, sin servicios externos)
pytest tests/unit/ -v --cov=domain --cov=adapters --cov=apps --cov-report=term-missing

# Tests de integración (requiere configurar API keys)
pytest tests/integration/ -v
```

### Pipeline CI/CD Automatizado

El repositorio incluye verificaciones completas en cada push:

- ✅ **Linting**: Ruff para calidad de código
- ✅ **Type checking**: MyPy para validación de tipos
- ✅ **Testing**: 99 unit tests con 23%+ cobertura
- ✅ **Security**: Bandit + Safety para análisis de seguridad
- ✅ **Build**: Docker multi-stage optimizado
- ✅ **Deploy**: Automatización a staging/producción

Ver `.github/workflows/ci.yml` para configuración completa.

---

## 🚀 Deployment

### Opción 1: Docker Compose (Recomendado para producción) ✅

El método más simple y rápido:

```bash
# 1. Configurar variables de entorno
cp .env.example .env
# Edita .env con tus API keys (Saptiva + Tavily)

# 2. Iniciar el servicio
docker-compose up -d

# 3. Verificar estado
curl http://localhost:8000/health
```

**Acceso:**
- API: http://localhost:8000
- Documentación interactiva: http://localhost:8000/docs
- Redoc: http://localhost:8000/redoc

### Opción 2: Docker Build Manual

```bash
# Build
docker build -t aletheia-api .

# Run
docker run -d \
  --name aletheia-api \
  -p 8000:8000 \
  --env-file .env \
  aletheia-api
```

### Opción 3: Servidor Directo (SSH)

Para servidores con acceso SSH:

```bash
# En el servidor remoto
git clone https://github.com/saptiva-ai/alethia_deepresearch.git
cd alethia_deepresearch
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edita .env con tus keys

# Ejecutar con systemd o supervisord
uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Configuración de Producción

Ajustes recomendados para entornos de producción:

```bash
# === API Keys (REQUERIDAS) ===
SAPTIVA_API_KEY=your_production_key
TAVILY_API_KEY=your_production_key

# === Configuración de producción ===
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
API_RELOAD=false

# === Servicios opcionales (deshabilitados por defecto) ===
VECTOR_BACKEND=none  # Cambiar a 'weaviate' solo si lo necesitas
```

**Nota**: El sistema funciona perfectamente sin servicios adicionales (Weaviate, Jaeger, etc.).

---

## 📡 API Endpoints

### Core Research Endpoints

| Endpoint | Method | Descripción |
|----------|--------|-------------|
| `/health` | GET | Health check con status de APIs |
| `/research` | POST | Investigación simple optimizada |
| `/deep-research` | POST | Investigación profunda iterativa |
| `/tasks/{task_id}/status` | GET | Estado de tarea en curso |
| `/reports/{task_id}` | GET | Reporte final generado |
| `/traces/{task_id}` | GET | Trazas de telemetría |

### Ejemplos de uso

```bash
# 1. Investigación simple (optimizada para rapidez)
curl -X POST "http://localhost:8000/research" \
  -H "Content-Type: application/json" \
  -d '{"query": "Latest developments in quantum computing 2025"}'

# Respuesta
{
  "task_id": "task-abc123",
  "status": "accepted",
  "message": "Research task initiated"
}

# 2. Verificar estado de la tarea
curl "http://localhost:8000/tasks/task-abc123/status"

# 3. Obtener reporte final
curl "http://localhost:8000/reports/task-abc123"

# 4. Investigación profunda (iterativa con múltiples refinamientos)
curl -X POST "http://localhost:8000/deep-research" \
  -H "Content-Type: application/json" \
  -d '{"query": "Impact of AI regulation on startup ecosystems", "max_iterations": 3}'
```

---

## 🏗 Arquitectura

### Vista general

```mermaid
flowchart TB
    subgraph API[FastAPI Application]
        E[Endpoints]
        M[Middleware]
        H[Health Checks]
    end

    subgraph Domain[Domain Layer]
        T[ResearchTask]
        Plan[Planning Service]
        Research[Research Service]
        Eval[Evaluation Service]
        Orchestrator[Iterative Orchestrator]
        Writer[Writer Service]
    end

    subgraph Ports[Port Interfaces]
        ModelPort[Model Client Port]
        SearchPort[Search Port]
        VectorPort[Vector Store Port]
        ExtractPort[Document Extract Port]
        GuardPort[Guard Port]
    end

    subgraph Adapters[External Integrations]
        Saptiva[Saptiva AI Models]
        Tavily[Tavily Search API]
        Weaviate[Weaviate Vector DB]
        PDFExtract[PDF/OCR Extractor]
        Telemetry[OpenTelemetry]
    end

    API --> Domain
    Domain --> Ports
    Ports --> Adapters
```

### Flujo de investigación


```mermaid
flowchart TD
    A[Query Input] --> B[Query Normalization]
    B --> C[Planning Service]
    C --> D[Subtask Generation]
    D --> E[Parallel Research Execution]
    
    E --> F[Tavily Search]
    E --> G[Web Scraping]
    E --> H[Document Extraction]
    
    F --> I[Evidence Collection]
    G --> I
    H --> I
    
    I --> J[Quality Scoring]
    J --> K[Vector Embedding]
    K --> L[Weaviate Storage]
    
    L --> M[Evidence Clustering]
    M --> N[Completeness Evaluation]
    
    N --> O{Quality Threshold Met?}
    O -->|No| P[Gap Analysis]
    O -->|Yes| Q[Report Synthesis]
    
    P --> R[Refinement Queries]
    R --> E
    
    Q --> S[Citation Generation]
    S --> T[Final Report]
    T --> U[Artifact Export]
    
    subgraph "Quality Control"
        V[Authority Scoring]
        W[Recency Weighting]
        X[Relevance Ranking]
        Y[Bias Detection]
    end
    
    J --> V
    J --> W
    J --> X
    J --> Y
```


### Principios de diseño

- **🏛 Clean Architecture**: Separación clara entre dominio, puertos y adapters
- **🔌 Dependency Inversion**: Abstracciones estables, implementaciones intercambiables
- **🧪 Testability**: 99 unit tests, mocking de dependencias externas
- **⚡ Performance**: Procesamiento paralelo, optimizaciones asíncronas
- **🛡 Resilience**: Graceful degradation, retry mechanisms, modo fallback
- **🎯 Simplicity**: Configuración minimalista, servicios externos opcionales

**Modo Minimalista por defecto:**
- Vector storage opera en modo mock (sin Weaviate)
- Evidence se almacena en memoria durante la sesión
- No hay impacto en rendimiento del pipeline de investigación
- Todas las funcionalidades operan normalmente

---

## 🔧 Desarrollo

### Estructura del proyecto

```
alethia_deepresearch/
├── apps/                    # FastAPI application
│   └── api/
├── domain/                  # Business logic (clean architecture)
│   ├── models/             # Domain models
│   └── services/           # Domain services
├── adapters/               # External integrations
│   ├── saptiva_model/      # Saptiva AI integration
│   ├── tavily_search/      # Tavily search integration
│   ├── weaviate_vector/    # Vector database
│   └── telemetry/          # Observability
├── ports/                  # Interface contracts
├── tests/                  # Test suites
│   ├── unit/              # Unit tests (99 tests)
│   └── integration/       # Integration tests
├── scripts/               # Deployment & utility scripts
│   └── deployment/        # Deployment automation
├── infra/                 # Infrastructure as code
│   ├── docker/           # Docker Compose
│   └── k8s/              # Kubernetes manifests
└── docs/                  # Documentation
```

### Scripts disponibles

```bash
# Verificación de Python
./scripts/check_python_version.sh      # Verificar Python 3.11+

# Deployment scripts
./scripts/deployment/setup-server.sh   # Configurar servidor remoto
./scripts/deployment/deploy-remote.sh  # Deploy via SSH
./scripts/deployment/deploy-docker.sh  # Deploy con Docker local
./scripts/deployment/deploy.sh         # Deploy general
```

### Configuración de desarrollo

```bash
# Pre-commit hooks (recomendado)
pip install pre-commit
pre-commit install

# Variables de desarrollo
export DEBUG=true
export LOG_LEVEL=DEBUG
export ENVIRONMENT=development
```

---

## 📊 Monitoreo y Observabilidad

### Health Check

El endpoint de salud proporciona información completa del sistema:

```bash
curl http://localhost:8000/health
```

**Respuesta:**
```json
{
  "status": "healthy",
  "service": "Aletheia Deep Research API",
  "version": "0.2.0",
  "api_keys": {
    "saptiva_available": true,
    "tavily_available": true
  }
}
```

### Logs Estructurados

El sistema incluye logging completo sin dependencias externas:

- **Formato**: Console output estructurado (JSON opcional)
- **Niveles**: DEBUG, INFO, WARNING, ERROR
- **Task IDs**: Tracking automático de todas las requests
- **Timestamps**: Información temporal precisa

### Observabilidad Avanzada (100% Opcional)

Si necesitas trazabilidad distribuida o métricas detalladas:

```bash
# 1. Instalar dependencias opcionales
pip install -r requirements-optional.txt

# 2. Habilitar servicios en docker-compose.yml
# (Descomentar secciones de Jaeger/OpenTelemetry)

# 3. Configurar en .env
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

**Nota**: La configuración minimalista incluye OpenTelemetry básico sin servicios externos.

---

## 🤝 Contribuir

### Workflow de desarrollo

1. **Fork** el repositorio
2. **Crear branch** para feature/fix: `git checkout -b feature/amazing-feature`
3. **Commit** cambios: `git commit -m 'Add amazing feature'`
4. **Push** a branch: `git push origin feature/amazing-feature`
5. **Crear Pull Request**

### Estándares de código

- ✅ **Linting**: Código debe pasar `ruff check`
- ✅ **Format**: Usar `ruff check --fix` para auto-format
- ✅ **Types**: Type hints obligatorios
- ✅ **Tests**: Tests unitarios para nuevas features
- ✅ **Docs**: Actualizar README.md si es necesario

### Revisión de código

- CI/CD debe pasar (99 tests, linting, security)
- Revisión por al menos 1 maintainer
- Documentación actualizada si aplica

---

## 📚 Recursos Adicionales

### Documentación

- **[API Reference](http://localhost:8000/docs)**: Swagger UI interactivo con ejemplos
- **[ReDoc](http://localhost:8000/redoc)**: Documentación alternativa de la API
- **[Documentación técnica](docs/)**: Guías detalladas y ejemplos en el directorio docs/
- **[SIMPLIFICATION.md](SIMPLIFICATION.md)**: Guía de la configuración minimalista

### Enlaces Útiles

- **[GitHub Issues](https://github.com/saptiva-ai/alethia_deepresearch/issues)**: Reportar bugs o solicitar features
- **[GitHub Discussions](https://github.com/saptiva-ai/alethia_deepresearch/discussions)**: Preguntas y discusiones
- **[Releases](https://github.com/saptiva-ai/alethia_deepresearch/releases)**: Historial de versiones

---

## 📄 Licencia

Apache License 2.0 - ver [LICENSE](LICENSE) para más detalles.

Copyright 2025 Saptiva Inc.

---

## 🙏 Agradecimientos

- **Saptiva AI** - Modelos de lenguaje de vanguardia
- **Tavily** - Search API para investigación
- **FastAPI** - Framework web moderno y rápido
- **Weaviate** - Vector database escalable

---

<div align="center">

**¿Encontraste útil este proyecto? ⭐ Danos una estrella!**

[Reportar Bug](https://github.com/saptiva-ai/alethia_deepresearch/issues) · [Solicitar Feature](https://github.com/saptiva-ai/alethia_deepresearch/issues) · [Documentación](docs/)

</div>
