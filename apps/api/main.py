from contextlib import asynccontextmanager
from functools import lru_cache
import os
import time
import uuid

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException, status
from pydantic import BaseModel, Field

# Initialize observability early
from adapters.telemetry.tracing import TelemetryManager, setup_telemetry

# Domain Services
from domain.services.iterative_research_svc import IterativeResearchOrchestrator
from domain.services.planner_svc import PlannerService
from domain.services.research_svc import ResearchService
from domain.services.writer_svc import WriterService

# Load environment variables from .env file
load_dotenv()

# Global telemetry manager
telemetry_manager: TelemetryManager | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown."""
    # Startup
    global telemetry_manager
    telemetry_manager = setup_telemetry()
    yield
    # Shutdown (if needed)
    pass


app = FastAPI(
    lifespan=lifespan,
    title="Aletheia Deep Research API",
    description="""
    ## 🔍 API para análisis e investigación profunda

    Esta API proporciona capacidades avanzadas de investigación utilizando:

    - **Investigación Iterativa**: Búsqueda profunda con múltiples iteraciones
    - **Procesamiento Paralelo**: Optimizado para alto rendimiento
    - **Trazabilidad Completa**: Monitoreo y observabilidad con OpenTelemetry
    - **Múltiples Fuentes**: Integración con Tavily y Saptiva APIs

    ### 📋 Casos de Uso

    - Análisis de mercado y competencia
    - Investigación académica y científica
    - Due diligence empresarial
    - Monitoreo de tendencias

    ### 🚀 Características

    - ✅ Auto-escalado en Kubernetes
    - ✅ CI/CD enterprise-grade
    - ✅ Seguridad y compliance
    - ✅ Métricas de calidad
    """,
    version="0.7.0",
    contact={
        "name": "Aletheia Development Team",
        "url": "https://github.com/saptiva-ai/alethia_deepresearch",
        "email": "dev@saptiva.ai",
    },
    license_info={"name": "Apache 2.0", "url": "https://www.apache.org/licenses/LICENSE-2.0"},
    openapi_tags=[
        {"name": "health", "description": "Endpoints de estado y monitoreo del sistema"},
        {
            "name": "research",
            "description": "Investigación estándar con procesamiento paralelo optimizado",
        },
        {
            "name": "deep-research",
            "description": "Investigación iterativa profunda usando patrón Together AI",
        },
        {"name": "tasks", "description": "Gestión y seguimiento de tareas de investigación"},
        {"name": "reports", "description": "Generación y recuperación de reportes"},
        {"name": "observability", "description": "Trazabilidad y métricas de rendimiento"},
    ],
)

# --- Data Models ---


class ResearchRequest(BaseModel):
    """Solicitud para investigación estándar con procesamiento paralelo optimizado."""

    query: str = Field(
        ...,
        description="Consulta de investigación",
        example="Análisis del mercado de inteligencia artificial en 2025",
    )
    scope: str | None = Field(
        None,
        description="Alcance específico de la investigación",
        example="mercado_latinoamericano",
    )
    budget: float | None = Field(None, description="Presupuesto máximo para fuentes de datos", example=50.0, gt=0, le=1000)


class DeepResearchRequest(BaseModel):
    """Solicitud para investigación iterativa profunda usando patrón Together AI."""

    query: str = Field(
        ...,
        description="Consulta principal de investigación profunda",
        example="Impacto de la regulación AI Act en startups europeas",
    )
    scope: str | None = Field(
        None,
        description="Alcance específico de la investigación",
        example="startup_ecosystem_europa",
    )
    max_iterations: int | None = Field(3, description="Máximo número de iteraciones de refinamiento", example=5, ge=1, le=10)
    min_completion_score: float | None = Field(0.75, description="Score mínimo de completitud para finalizar", example=0.85, ge=0.1, le=1.0)
    budget: int | None = Field(100, description="Presupuesto total para la investigación", example=200, gt=0, le=5000)


class TaskStatus(BaseModel):
    """Estado de una tarea de investigación."""

    task_id: str = Field(
        ...,
        description="Identificador único de la tarea",
        example="550e8400-e29b-41d4-a716-446655440000",
    )
    status: str = Field(..., description="Estado actual de la tarea", example="completed")
    details: str | None = Field(
        None,
        description="Detalles adicionales del estado",
        example="Investigación completada con 15 fuentes",
    )


class Report(BaseModel):
    """Reporte de investigación estándar."""

    status: str = Field(..., description="Estado del reporte", example="completed")
    report_md: str | None = Field(None, description="Contenido del reporte en Markdown")
    sources_bib: str | None = Field(
        None,
        description="Bibliografía de fuentes consultadas",
        example="Generated from 15 evidence sources",
    )
    metrics_json: str | None = Field(None, description="Métricas de calidad en formato JSON")


class DeepResearchReport(BaseModel):
    """Reporte de investigación profunda con métricas de calidad."""

    status: str = Field(..., description="Estado del reporte", example="completed")
    report_md: str | None = Field(None, description="Contenido del reporte final en Markdown")
    sources_bib: str | None = Field(None, description="Bibliografía de fuentes consultadas")
    research_summary: dict | None = Field(None, description="Resumen estructurado de la investigación")
    quality_metrics: dict | None = Field(
        None,
        description="Métricas de calidad de la investigación",
        example={
            "completion_level": 0.95,
            "quality_score": 0.88,
            "evidence_count": 42,
            "execution_time": 127.3,
        },
    )


class Traces(BaseModel):
    """Artefactos de trazabilidad y observabilidad."""

    manifest_json: str = Field(..., description="Manifiesto de la ejecución")
    events_ndjson: str = Field(..., description="Eventos de trazabilidad en formato NDJSON")
    otel_export_json: str = Field(..., description="Exportación de trazas OpenTelemetry")


# --- In-Memory Task Store ---
tasks = {}
deep_research_tasks = {}

# --- Performance Optimizations ---
_health_check_cache = {"status": "healthy", "last_check": 0}
HEALTH_CACHE_TTL = 30  # Cache health status for 30 seconds


@lru_cache(maxsize=128)
def get_api_keys_status():
    """Cached API key validation to avoid repeated environment checks."""
    saptiva_key = os.getenv("SAPTIVA_API_KEY")
    tavily_key = os.getenv("TAVILY_API_KEY")

    saptiva_available = saptiva_key and saptiva_key != "pon_tu_api_key_aqui"
    tavily_available = tavily_key and tavily_key != "pon_tu_api_key_aqui"

    return {"saptiva_available": saptiva_available, "tavily_available": tavily_available}


# --- Real Research Pipeline (Optimized Async Version) ---
async def run_real_research_pipeline(task_id: str, query: str):
    """
    Orchestrates the research process: Plan -> Research -> Write.
    Optimized async version with parallel processing.
    """
    tasks[task_id] = {"status": "running", "report": None}
    print(f"🚀 Starting optimized research for task {task_id} with query: '{query}'")

    try:
        # Initialize services once
        planner = PlannerService()
        researcher = ResearchService()
        writer = WriterService()

        # 1. Plan
        print(f"[{task_id}] Creating research plan...")
        research_plan = planner.create_plan(query)
        print(f"[{task_id}] ✅ Plan created with {len(research_plan.sub_tasks)} sub-tasks.")

        # 2. Research (Using parallel execution)
        print(f"[{task_id}] 🔍 Starting parallel research execution...")
        evidence_list = await researcher.execute_plan_parallel(research_plan)
        print(f"[{task_id}] ✅ Research completed with {len(evidence_list)} pieces of evidence.")

        # 3. Write
        print(f"[{task_id}] 📝 Generating report...")
        report_content = writer.write_report(query, evidence_list)
        print(f"[{task_id}] ✅ Report generated.")

        # 4. Store result
        tasks[task_id] = {
            "status": "completed",
            "report": report_content,
            "sources": f"Generated from {len(evidence_list)} evidence sources",
            "evidence_count": len(evidence_list),
        }
        print(f"🎉 Research completed for task {task_id}")

    except Exception as e:
        print(f"❌ Error during research pipeline for task {task_id}: {e}")
        tasks[task_id] = {"status": "failed", "report": f"An error occurred: {e}"}


# --- Backward Compatibility Sync Version ---
def run_real_research_pipeline_sync(task_id: str, query: str):
    """
    Synchronous wrapper for backward compatibility.
    """
    import asyncio

    asyncio.run(run_real_research_pipeline(task_id, query))


# --- Deep Research Pipeline (Together AI Pattern) ---
async def run_deep_research_pipeline(task_id: str, request: DeepResearchRequest):
    """
    Orchestrates the iterative deep research process using Together AI pattern.
    """
    deep_research_tasks[task_id] = {"status": "running", "result": None}
    print(f"Starting deep research for task {task_id} with query: '{request.query}'")

    try:
        # Initialize iterative research orchestrator
        orchestrator = IterativeResearchOrchestrator(
            max_iterations=request.max_iterations,
            min_completion_score=request.min_completion_score,
            budget=request.budget,
        )

        # Execute deep research
        tracer = telemetry_manager.get_tracer() if telemetry_manager else None
        result = await orchestrator.execute_deep_research(request.query, tracer=tracer)

        # Store result
        deep_research_tasks[task_id] = {
            "status": "completed",
            "result": result,
            "summary": orchestrator.get_research_summary(result),
        }
        print(f"Deep research completed for task {task_id}")

    except Exception as e:
        print(f"Error during deep research pipeline for task {task_id}: {e}")
        deep_research_tasks[task_id] = {"status": "failed", "error": f"An error occurred: {e}"}


# --- API Endpoints ---


@app.get(
    "/health",
    tags=["health"],
    summary="Estado del sistema",
    description="Verifica el estado de salud de la API y la disponibilidad de servicios externos",
    responses={
        200: {
            "description": "Sistema funcionando correctamente",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "service": "Aletheia Deep Research API",
                        "version": "0.7.0",
                        "api_keys": {"saptiva_available": True, "tavily_available": True},
                        "cached": False,
                        "timestamp": 1726179600.0,
                    }
                }
            },
        }
    },
)
async def health_check():
    """
    Health check endpoint for Docker and monitoring.
    Optimized with caching to reduce response time.
    """
    current_time = time.time()

    # Return cached response if within TTL
    if current_time - _health_check_cache["last_check"] < HEALTH_CACHE_TTL:
        return {
            "status": _health_check_cache["status"],
            "service": "Aletheia Deep Research API",
            "version": "0.2.0",
            "cached": True,
        }

    # Perform actual health check
    api_status = get_api_keys_status()
    health_status = "healthy" if api_status["saptiva_available"] or api_status["tavily_available"] else "degraded"

    # Update cache
    _health_check_cache["status"] = health_status
    _health_check_cache["last_check"] = current_time

    return {
        "status": health_status,
        "service": "Aletheia Deep Research API",
        "version": "0.2.0",
        "api_keys": api_status,
        "cached": False,
        "timestamp": current_time,
    }


@app.post(
    "/research",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=TaskStatus,
    tags=["research"],
    summary="Iniciar investigación estándar",
    description="""
    Inicia una nueva tarea de investigación con procesamiento paralelo optimizado.

    - **Procesamiento asíncrono**: La investigación se ejecuta en segundo plano
    - **Optimización paralela**: Múltiples sub-tareas ejecutadas simultáneamente
    - **Múltiples fuentes**: Integración con Tavily y Saptiva APIs
    - **Alta disponibilidad**: Continúa funcionando aunque algunas APIs no estén disponibles
    """,
    responses={
        202: {
            "description": "Tarea de investigación aceptada y en ejecución",
            "content": {
                "application/json": {
                    "example": {
                        "task_id": "550e8400-e29b-41d4-a716-446655440000",
                        "status": "accepted",
                        "details": ("Research task has been accepted and is running with optimized " "parallel processing."),
                    }
                }
            },
        },
        400: {"description": "Parámetros de solicitud inválidos"},
        500: {"description": "Error interno del servidor"},
    },
)
async def start_research(request: ResearchRequest, background_tasks: BackgroundTasks):
    """
    Starts a new research task with performance optimizations.
    """
    # Use cached API key status
    api_status = get_api_keys_status()

    if not api_status["saptiva_available"]:
        print("Warning: SAPTIVA_API_KEY is not set. The planner and writer will use mock data.")

    if not api_status["tavily_available"]:
        print("Warning: TAVILY_API_KEY is not set. The research step will be skipped.")

    task_id = str(uuid.uuid4())
    tasks[task_id] = {"status": "accepted", "started_at": time.time()}
    background_tasks.add_task(run_real_research_pipeline, task_id, request.query)

    return TaskStatus(
        task_id=task_id,
        status="accepted",
        details=("Research task has been accepted and is running with optimized " "parallel processing."),
    )


@app.get(
    "/tasks/{task_id}/status",
    response_model=TaskStatus,
    tags=["tasks"],
    summary="Consultar estado de tarea",
    description="Obtiene el estado actual de una tarea de investigación específica",
    responses={
        200: {
            "description": "Estado de la tarea recuperado exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "task_id": "550e8400-e29b-41d4-a716-446655440000",
                        "status": "completed",
                        "details": "Research completed with 15 evidence sources",
                    }
                }
            },
        },
        404: {"description": "Tarea no encontrada"},
    },
)
async def get_task_status(task_id: str):
    """
    Get the current status of a research task.
    """
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return TaskStatus(
        task_id=task_id,
        status=task["status"],
        details=task.get("report", ""),
    )


@app.get(
    "/reports/{task_id}",
    response_model=Report,
    tags=["reports"],
    summary="Obtener reporte de investigación",
    description=("Recupera el resultado completo de una tarea de investigación " "incluyendo el reporte y fuentes"),
    responses={
        200: {
            "description": "Reporte recuperado exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "status": "completed",
                        "report_md": "# Resumen Ejecutivo de la Investigación",
                        "sources_bib": "Generated from 15 evidence sources",
                        "metrics_json": '{"mock_metric": 1.0}',
                    }
                }
            },
        },
        404: {"description": "Reporte no encontrado"},
    },
)
async def get_report(task_id: str):
    """
    Retrieves the status and result of a research task.
    """
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task["status"] == "completed":
        return Report(
            status="completed",
            report_md=task.get("report"),
            sources_bib=task.get("sources"),
            metrics_json='{"mock_metric": 1.0}',
        )
    else:
        return Report(status=task["status"], report_md=task.get("report"))


@app.get(
    "/traces/{task_id}",
    response_model=Traces,
    tags=["observability"],
    summary="Obtener trazas de observabilidad",
    description="""
    Recupera artefactos de trazabilidad y observabilidad para una tarea específica.

    Incluye:
    - **Manifiesto**: Configuración y metadatos de la ejecución
    - **Eventos**: Log de eventos en formato NDJSON para análisis
    - **OpenTelemetry**: Trazas de rendimiento y monitoreo
    """,
    responses={
        200: {
            "description": "Trazas recuperadas exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "manifest_json": ('{"version": "0.7.0", "task_type": "research", ' '"started_at": "2025-09-12T10:00:00Z"}'),
                        "events_ndjson": ('{"event": "task_started", "timestamp": "2025-09-12T10:00:00Z"}'),
                        "otel_export_json": ('{"trace_id": "abc123", "spans": ' '[{"name": "research_task", "duration_ms": 1250}]}'),
                    }
                }
            },
        },
        404: {"description": "Tarea no encontrada"},
    },
)
async def get_traces(task_id: str):
    """
    Retrieves traceability and observability artifacts for a task.
    """
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    return Traces(
        manifest_json='{"version": "0.1.0", "seed": 123}',
        events_ndjson='{"event": "mock_event", "timestamp": "2025-09-10T21:00:00Z"}',
        otel_export_json='{"trace_id": "mock_trace_id"}',
    )


# --- Deep Research Endpoints (Together AI Pattern) ---


@app.post(
    "/deep-research",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=TaskStatus,
    tags=["deep-research"],
    summary="Iniciar investigación profunda iterativa",
    description="""
    Inicia una investigación profunda usando el patrón Together AI con refinamiento iterativo.

    ### 🔄 Características de Deep Research:
    - **Refinamiento iterativo**: Múltiples ciclos de análisis y mejora
    - **Score de completitud**: Evaluación automática de calidad
    - **Gap analysis**: Identificación automática de brechas de información
    - **Control de presupuesto**: Límites configurables de recursos

    ### 📊 Métricas de Calidad:
    - Completion level (0.0 - 1.0)
    - Research quality score
    - Evidence count tracking
    - Execution time monitoring
    """,
    responses={
        202: {
            "description": "Tarea de investigación profunda aceptada",
            "content": {
                "application/json": {
                    "example": {
                        "task_id": "deep-550e8400-e29b-41d4-a716-446655440000",
                        "status": "accepted",
                        "details": "Deep research task accepted with parallel processing. Configuration: 5 iterations, 0.85 min score.",
                    }
                }
            },
        },
        400: {"description": "Parámetros de configuración inválidos"},
        500: {"description": "Error interno del servidor"},
    },
)
async def start_deep_research(request: DeepResearchRequest, background_tasks: BackgroundTasks):
    """
    Starts a new iterative deep research task using Together AI pattern with performance optimizations.
    """
    # Use cached API key status for better performance
    api_status = get_api_keys_status()

    if not api_status["saptiva_available"]:
        print("Warning: SAPTIVA_API_KEY is not set. Some agents will use mock data.")

    if not api_status["tavily_available"]:
        print("Warning: TAVILY_API_KEY is not set. Research will be limited.")

    task_id = str(uuid.uuid4())
    deep_research_tasks[task_id] = {"status": "accepted", "started_at": time.time()}
    background_tasks.add_task(run_deep_research_pipeline, task_id, request)

    return TaskStatus(
        task_id=task_id,
        status="accepted",
        details=(
            "Deep research task accepted with parallel processing. "
            f"Configuration: {request.max_iterations} iterations, "
            f"{request.min_completion_score} min score."
        ),
    )


@app.get(
    "/deep-research/{task_id}",
    response_model=DeepResearchReport,
    tags=["deep-research"],
    summary="Obtener reporte de investigación profunda",
    description="""
    Recupera el resultado completo de una investigación profunda incluyendo métricas de calidad.

    ### 📊 Contenido del Reporte:
    - **Reporte final**: Documento completo en Markdown
    - **Resumen de investigación**: Estructura de datos con hallazgos clave
    - **Métricas de calidad**: Scores de completitud y evidencia
    - **Bibliografia**: Referencias de todas las fuentes consultadas
    """,
    responses={
        200: {
            "description": "Reporte de investigación profunda recuperado exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "status": "completed",
                        "report_md": "# Impacto de AI Act en Startups Europeas\n\n## Análisis Profundo\n...",
                        "sources_bib": "Generated from 42 evidence sources",
                        "research_summary": {
                            "iterations_completed": 3,
                            "gaps_identified": ["regulatory_compliance", "market_impact"],
                            "key_findings": [
                                "High compliance costs",
                                "Market consolidation likely",
                            ],
                        },
                        "quality_metrics": {
                            "completion_level": 0.95,
                            "quality_score": 0.88,
                            "evidence_count": 42,
                            "execution_time": 127.3,
                        },
                    }
                }
            },
        },
        404: {"description": "Tarea de investigación profunda no encontrada"},
    },
)
async def get_deep_research_report(task_id: str):
    """
    Retrieves the status and result of a deep research task.
    """
    task = deep_research_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Deep research task not found")

    if task["status"] == "completed":
        result = task["result"]
        summary = task["summary"]

        return DeepResearchReport(
            status="completed",
            report_md=result.final_report,
            sources_bib=f"Generated from {result.total_evidence_count} evidence sources",
            research_summary=summary,
            quality_metrics={
                "completion_level": result.completion_level,
                "quality_score": result.research_quality_score,
                "evidence_count": result.total_evidence_count,
                "execution_time": result.execution_time_seconds,
            },
        )
    elif task["status"] == "failed":
        return DeepResearchReport(status="failed", report_md=f"Deep research failed: {task.get('error', 'Unknown error')}")
    else:
        return DeepResearchReport(status=task["status"])
