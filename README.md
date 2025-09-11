# Aletheia (ἀλήθεια - desocultamiento de la verdad)

Proyecto de deep research basado en modelos Saptiva y patrones AutoGen, con énfasis en veracidad, trazabilidad y despliegue soberano (cloud / on-prem / cliente).
---

## Alcance y Casos de Uso

Como usuario quiero usar la herramienta para:
- Análisis de una empresa
- Análisis macroeconómico de un país
- Análisis de una industria
- Benchmark (lista de competidores)
- Investigación de un tema complejo (p. ej. “cómo implementar Triton en hardware AMD”)

**Criterios de Aceptación (CA):**
- Se usan los modelos de **Saptiva**
- Se recibe un **reporte** consolidado con el resultado de investigación
- Código documentado separando **búsqueda**, **planeación** y **síntesis**
- Hay **traces** de consultas y de tools usadas (OpenTelemetry + event logs)
- **Tavily** se usa como motor de búsqueda primario (con fallback opcional)

---

## Arquitectura

En el centro vive el **Dominio** (agnóstico a framework/modelo). La orquestación usa Saptiva‑Agents. Las dependencias externas entran por **Ports** y se implementan en **Adapters** intercambiables.

```mermaid
flowchart LR
  subgraph Domain[Dominio]
    T(ResearchTask)
Plan
Evidence
Citation
Report
    P[Planner]
R[Researcher]
C[Curator]
F[FactChecker]
W[Writer]
X[Critic]
  end

  subgraph Ports[Ports]
    MP[ModelClientPort]
    SP[SearchPort]
    VP[VectorStorePort]
    BP[BrowserPort]
    DP[DocExtractPort]
    GP[GuardPort]
    LP[LoggingPort]
    STP[StoragePort]
  end

  subgraph Adapters[Adapters]
    MA[Saptiva Model Client]
    TA[Tavily API]
    WA[Weaviate DB]
    SA[Multimodal Web Surfer]
    DA[PDF/OCR Extractor]
    GA[Saptiva Guard]
    OA[OpenTelemetry + Event Logs]
    FS[MinIO/S3/FS]
  end

  Domain --> Ports
  Ports --> Adapters
```

**Principios clave**
- **Separation of concerns:** Dominio no conoce Saptiva/Tavily; habla con puertos.
- **Configuración por entorno:** cada adapter se resuelve por variables de entorno (on‑prem, nube, cliente).
- **Observabilidad de primera clase:** todos los pasos emiten eventos estructurados y spans.
- **Reproducibilidad:** cada evidencia trae `source.url`, `excerpt`, `timestamp`, `hash` y `tool_call_id`.

---

## Equipo de Agentes (patrones al estilo AutoGen, implementados con Saptiva‑Agents)

| Rol | Modelo Saptiva sugerido | Tools/Ports | Función |
|---|---|---|---|
| **Planner** | `Saptiva Ops` | Model, Vector, Search(meta) | Descompone la pregunta en sub‑tareas, define presupuesto de pasos y criterios de cierre. |
| **Researcher** | `Saptiva Ops/Turbo` | **Tavily**, WebSurfer, DocExtract | Ejecuta búsquedas paralelas, lee páginas/PDF, produce _evidence packs_. |
| **Curator (Evidence Scorer)** | `Saptiva Cortex` | Model | Deduplica, puntúa calidad (autoridad, frescura, consistencia), arma _top‑k_. |
| **FactChecker** | `Saptiva Cortex` + **Guard** | Model, Guard | Cruza afirmaciones ↔ evidencias, aplica políticas (PII, seguridad). |
| **Writer** | `Saptiva Cortex` | Model, Vector | Redacta **reporte** con citaciones \[1..N], tablas y anexos. |
| **Critic/Editor (Evaluation)** | `Saptiva Cortex` | Model | Evalúa completitud, identifica gaps, genera queries de refinamiento (Together AI pattern). |

> **Nota:** Diseño flexible para ejecutar como **Round‑Robin secuencial** o **fan‑out concurrente** (Planner → branch de Researchers por tipo de fuente → merge en Curator).

---

## Flujo de Trabajo (patrón Deep Research)

1. **Intake & Guard:** normaliza la pregunta, activa `Guard` y fija límites (pasos, tokens, dominios).
2. **Plan:** Planner entrega `research_plan.yaml` con sub‑tareas y fuentes objetivo.
3. **Búsqueda & Extracción:** Researcher usa **Tavily** (primario) + WebSurfer + Extractor PDF/OCR para obtener artefactos; cada artefacto se guarda con metadatos y hash.
4. **Indexado (RAG):** vectoriza con **Saptiva Embed** y guarda en **Weaviate** (colección por _task_).
5. **Curación:** Curator deduplica/scorea evidencias, produce `evidence_set.json` (top‑k por sub‑tarea).
6. **Borrador:** Writer redacta un primer reporte con citaciones \[i]→bibliografía.
7. **Verificación (Reflection):** Critic/FactChecker marcan huecos; si aplica, se re‑dispara búsqueda focalizada.
8. **Entrega:** genera **Markdown/HTML/PDF** y exporta **trazas** (spans + event logs + manifest de fuentes).

---

## Trazabilidad y Observabilidad

- **OpenTelemetry**: `TRACES_EXPORTER=otlp` (Jaeger/Zipkin soportados).
- **Event Logs**: cada herramienta emite `FunctionExecutionResult` con `args`, `elapsed_ms`, `excerpt` y `source.url`.
- **Run Manifest**: `runs/{task_id}/manifest.json` con versiones, semillas, presupuesto y checksums.
- **Replay:** se puede re‑generar el informe desde `evidence_set.json` sin tocar la web (modo offline).

---

## Estructura del Repo

```
alethia/
├─ apps/
│  └─ api/                # FastAPI: /research, /reports/{id}, /traces/{id}
├─ domain/
│  ├─ models/             # ResearchTask, Plan, Evidence, Citation, Report
│  └─ services/           # PlannerSvc, ResearchSvc, CuratorSvc, WriterSvc
├─ ports/                 # *Port interfaces (SearchPort, VectorStorePort, etc.)
├─ adapters/
│  ├─ saptiva_model/      # SaptivaAIChatCompletionClient adapter
│  ├─ tavily_search/      # Tavily API adapter
│  ├─ weaviate_vector/    # VectorStore adapter (fallback: chroma/none)
│  ├─ web_surfer/         # Playwright/Multimodal surfer
│  ├─ extractor/          # PDF/OCR adapter
│  ├─ guard/              # Saptiva Guard adapter
│  └─ telemetry/          # OTel & event logs
├─ agents/                # Orquestación Saptiva-Agents (team definitions)
├─ prompts/               # System/prompts por rol (planner, writer, critic)
├─ runs/                  # Artifacts por ejecución (manifest, traces, evidence, report)
└─ infra/
   ├─ docker/             # Compose para dev; Jaeger/Weaviate/MinIO opcionales
   └─ k8s/                # Manifests para despliegues por entorno
```

---

## API (Implementada)

### Investigación Básica (Secuencial)
- `POST /research`: body `{ query, scope, budget }` → `202 Accepted` con `task_id`.
- `GET /reports/{task_id}`: devuelve `status`, `report.md`, `sources.bib`, `metrics.json`.
- `GET /traces/{task_id}`: descarga `manifest.json`, `events.ndjson`, `otel-export.json`.

### Deep Research (Together AI Pattern - Iterativo)
- `POST /deep-research`: body `{ query, scope, max_iterations, min_completion_score, budget }` → `202 Accepted` con `task_id`.
- `GET /deep-research/{task_id}`: devuelve `status`, `report.md`, `sources.bib`, `research_summary`, `quality_metrics`.

**Esquema `Evidence` (resumen):**
```json
{
  "id": "ev_01",
  "source": {"url": "https://...", "title": "...", "fetched_at": "2025-09-10T20:00:00Z"},
  "excerpt": "párrafo relevante...",
  "hash": "sha256:...",
  "tool_call_id": "tavily:search:abc123",
  "score": 0.84,
  "tags": ["macro", "2024", "imf"],
  "cit_key": "IMF2024"
}
```

---

## Variables de Entorno

```
SAPTIVA_API_KEY=...
SAPTIVA_MODEL_PLANNER=SAPTIVA_OPS
SAPTIVA_MODEL_WRITER=SAPTIVA_CORTEX
TAVILY_API_KEY=...
VECTOR_BACKEND=weaviate    # weaviate | chroma | none
WEAVIATE_HOST=http://localhost:8080
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
ARTIFACTS_DIR=./runs
```

---

## Quickstart (modo dev)

1) **Servicios opcionales**: levantar `docker compose` con `weaviate`, `jaeger`, `minio`.
2) **Configurar `.env`** con las variables de arriba.
3) **Ejecutar API**: `uvicorn apps.api.main:app --reload`.
4) **Lanzar tarea**: `curl -X POST /research -d '{"query":"Benchmark de competidores en banca abierta MX"}'`.
5) **Monitorear**: ver spans en Jaeger y `runs/<task_id>/events.ndjson`.
6) **Descargar reporte**: `GET /reports/<task_id>` → `report.md` + `sources.bib`.

---

## Decisiones de Diseño

- **Hexagonal / Ports & Adapters**: permite reemplazar Tavily por otro motor o Weaviate por Pinecone sin tocar dominio.
- **Tavily por defecto**: resultados limpios y API simple; si falla, fallback a Google CSE/WebSurfer.
- **Weaviate**: buena opción **on‑prem**; embeddings con **Saptiva Embed**.
- **Reflection**: Writer ↔ Critic con máximo N iteraciones y presupuesto de tokens.
- **Defensa ante alucinaciones**: _grounding_ obligado: toda afirmación factual debe trazar a `Evidence.id`.
- **Costo/latencia**: límites por etapa, caching de queries y memoización de embeddings.

---

## Seguridad y Cumplimiento

- **Guard** en _input_ y _output_; lista de dominios permitidos opcional.
- **PII redaction** previa a persistencia de artefactos.
- **Determinismo relativo**: registrar seeds/temperatures y versiones de modelos.

---

## Roadmap y Estado Actual

### ✅ v0.2 (COMPLETADO) - Together AI Deep Research Pattern
- **Patrones Avanzados:** Implementación completa del patrón Together AI con agentes Saptiva
- **Investigación Iterativa:** Sistema multi-iteración con evaluación y refinamiento automático
- **API Completa:** Endpoints `/research` y `/deep-research` operativos con Tavily API integrada
- **Agente Evaluador:** Assessment automático de completitud y identificación de gaps
- **RAG Vectorial:** Weaviate integrado para storage y recuperación de evidencia

### 🎯 Funcionalidades Clave Operativas:
- ✅ **Planner Agent** (SAPTIVA_OPS): Genera planes de investigación estructurados
- ✅ **Research Agent** (TAVILY + Saptiva): Búsqueda web real con 15+ fuentes por query
- ✅ **Evaluation Agent** (SAPTIVA_CORTEX): Scoring de completitud y análisis de gaps
- ✅ **Writer Agent** (SAPTIVA_CORTEX): Generación de reportes con citaciones
- ✅ **Iterative Orchestrator**: Loop inteligente hasta alcanzar calidad objetivo

### 🚀 Casos de Uso Validados:
```bash
# Investigación básica (secuencial)
curl -X POST "http://localhost:8000/research" \
  -H "Content-Type: application/json" \
  -d '{"query": "Análisis competitivo bancos digitales México 2024"}'

# Deep Research (iterativo con Together AI pattern)
curl -X POST "http://localhost:8000/deep-research" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Análisis estratégico mercado fintech México 2024", 
    "max_iterations": 3,
    "min_completion_score": 0.75,
    "budget": 150
  }'
```

### 📊 Métricas de Calidad Implementadas:
- **Completion Score**: 0.0-1.0 scale con niveles (insufficient/partial/adequate/comprehensive)
- **Coverage Areas**: Scoring granular por áreas de investigación
- **Gap Analysis**: Identificación automática de información faltante
- **Iterative Refinement**: Queries de seguimiento inteligentes

### 🏗️ v0.3 (Próximo) - DevOps & Production Ready
- **CI/CD Pipeline**: GitHub Actions con testing automatizado
- **Branching Strategy**: Git Flow con feature branches y releases
- **Testing Suite**: Unit tests + integration tests + end-to-end
- **Containerización**: Docker multi-stage builds optimizados
- **Monitoring**: Métricas de performance y alerting
- **Security**: Vulnerability scanning y secret management

### 📋 v1.0 (Futuro)
- **Concurrencia Avanzada**: Parallel search agents y async processing
- **WebSurfer Multimodal**: Extracción de imágenes y PDFs
- **UI Dashboard**: Interface web para monitoring y control
- **Export Avanzado**: PDF/HTML con gráficos y visualizaciones
- **Kubernetes**: Helm charts para despliegue en producción

---

## Licencia
MIT (propuesta).
