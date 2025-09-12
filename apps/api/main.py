import asyncio
import os
import time
import uuid
from functools import lru_cache

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException, status
from pydantic import BaseModel

# Load environment variables from .env file
load_dotenv()

# Initialize observability early
from adapters.telemetry.tracing import setup_telemetry, TelemetryManager

# Domain Services
from domain.services.iterative_research_svc import IterativeResearchOrchestrator
from domain.services.planner_svc import PlannerService
from domain.services.research_svc import ResearchService
from domain.services.writer_svc import WriterService

app = FastAPI(
    title="Aletheia Deep Research API",
    description="API para análisis e investigación profunda.",
    version="0.2.0",
)

telemetry_manager: TelemetryManager

@app.on_event("startup")
async def startup_event():
    """Initializes Telemetry."""
    global telemetry_manager
    telemetry_manager = setup_telemetry()
    telemetry_manager.instrument_fastapi(app)


# --- Data Models ---

from typing import Optional


class ResearchRequest(BaseModel):
    query: str
    scope: Optional[str] = None
    budget: Optional[float] = None

class DeepResearchRequest(BaseModel):
    query: str
    scope: Optional[str] = None
    max_iterations: Optional[int] = 3
    min_completion_score: Optional[float] = 0.75
    budget: Optional[int] = 100

class TaskStatus(BaseModel):
    task_id: str
    status: str
    details: Optional[str] = None

class Report(BaseModel):
    status: str
    report_md: Optional[str] = None
    sources_bib: Optional[str] = None
    metrics_json: Optional[str] = None

class DeepResearchReport(BaseModel):
    status: str
    report_md: Optional[str] = None
    sources_bib: Optional[str] = None
    research_summary: Optional[dict] = None
    quality_metrics: Optional[dict] = None

class Traces(BaseModel):
    manifest_json: str
    events_ndjson: str
    otel_export_json: str

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
    
    return {
        "saptiva_available": saptiva_available,
        "tavily_available": tavily_available
    }

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
            "evidence_count": len(evidence_list)
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
            budget=request.budget
        )

        # Execute deep research
        result = await orchestrator.execute_deep_research(request.query, tracer=telemetry_manager.get_tracer())

        # Store result
        deep_research_tasks[task_id] = {
            "status": "completed",
            "result": result,
            "summary": orchestrator.get_research_summary(result)
        }
        print(f"Deep research completed for task {task_id}")

    except Exception as e:
        print(f"Error during deep research pipeline for task {task_id}: {e}")
        deep_research_tasks[task_id] = {"status": "failed", "error": f"An error occurred: {e}"}


# --- API Endpoints ---

@app.get("/health")
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
            "cached": True
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
        "timestamp": current_time
    }

@app.post("/research", status_code=status.HTTP_202_ACCEPTED, response_model=TaskStatus)
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
    background_tasks.add_task(run_real_research_pipeline_sync, task_id, request.query)
    
    return TaskStatus(
        task_id=task_id, 
        status="accepted", 
        details="Research task has been accepted and is running with optimized parallel processing."
    )

@app.get("/tasks/{task_id}/status", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """
    Get the current status of a research task.
    """
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return TaskStatus(task_id=task_id, status=task["status"], details=task.get("report", ""))

@app.get("/reports/{task_id}", response_model=Report)
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
            metrics_json='{"mock_metric": 1.0}'
        )
    else:
        return Report(status=task["status"], report_md=task.get("report"))


@app.get("/traces/{task_id}", response_model=Traces)
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

@app.post("/deep-research", status_code=status.HTTP_202_ACCEPTED, response_model=TaskStatus)
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
        details=f"Deep research task accepted with parallel processing. Configuration: {request.max_iterations} iterations, {request.min_completion_score} min score."
    )

@app.get("/deep-research/{task_id}", response_model=DeepResearchReport)
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
                "execution_time": result.execution_time_seconds
            }
        )
    elif task["status"] == "failed":
        return DeepResearchReport(
            status="failed",
            report_md=f"Deep research failed: {task.get('error', 'Unknown error')}"
        )
    else:
        return DeepResearchReport(status=task["status"])
