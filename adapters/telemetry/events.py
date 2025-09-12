"""
Structured event logging for Aletheia Deep Research.
Captures all research operations as structured events for analysis and debugging.
"""
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional
import uuid

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Types of events in the research process."""
    RESEARCH_STARTED = "research.started"
    RESEARCH_COMPLETED = "research.completed"
    RESEARCH_FAILED = "research.failed"

    PLAN_CREATED = "plan.created"
    PLAN_FAILED = "plan.failed"

    SEARCH_EXECUTED = "search.executed"
    SEARCH_FAILED = "search.failed"

    EVIDENCE_COLLECTED = "evidence.collected"
    EVIDENCE_STORED = "evidence.stored"

    EVALUATION_COMPLETED = "evaluation.completed"
    EVALUATION_FAILED = "evaluation.failed"

    REPORT_GENERATED = "report.generated"
    REPORT_FAILED = "report.failed"

    ITERATION_STARTED = "iteration.started"
    ITERATION_COMPLETED = "iteration.completed"

    API_REQUEST_RECEIVED = "api.request_received"
    API_RESPONSE_SENT = "api.response_sent"

    MODEL_CALL_STARTED = "model.call_started"
    MODEL_CALL_COMPLETED = "model.call_completed"
    MODEL_CALL_FAILED = "model.call_failed"


@dataclass
class ResearchEvent:
    """Structured event for research operations."""
    event_id: str
    event_type: EventType
    timestamp: datetime
    task_id: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None

    # Event payload
    data: Dict[str, Any] = None

    # Performance metrics
    duration_ms: Optional[float] = None

    # Error information
    error: Optional[str] = None
    error_type: Optional[str] = None

    # Tracing
    trace_id: Optional[str] = None
    span_id: Optional[str] = None

    def __post_init__(self):
        if self.data is None:
            self.data = {}
        if self.event_id is None:
            self.event_id = str(uuid.uuid4())

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        result = asdict(self)
        result["timestamp"] = self.timestamp.isoformat()
        result["event_type"] = self.event_type.value
        return result

    def to_json(self) -> str:
        """Convert event to JSON string."""
        return json.dumps(self.to_dict())


class EventLogger:
    """Logger for structured research events."""

    def __init__(self):
        self.events: List[ResearchEvent] = []
        self.current_task_id: Optional[str] = None
        self.session_id = str(uuid.uuid4())
        self._setup_file_logging()

    def _setup_file_logging(self):
        """Setup file-based event logging."""
        self.artifacts_dir = os.getenv("ARTIFACTS_DIR", "./runs")
        os.makedirs(self.artifacts_dir, exist_ok=True)

        # Create events file for this session
        self.events_file = os.path.join(
            self.artifacts_dir,
            f"events_{self.session_id}_{int(time.time())}.ndjson"
        )

    def set_task_context(self, task_id: str):
        """Set current task context for events."""
        self.current_task_id = task_id

    def log_event(self,
                  event_type: EventType,
                  data: Optional[Dict[str, Any]] = None,
                  duration_ms: Optional[float] = None,
                  error: Optional[str] = None,
                  error_type: Optional[str] = None,
                  task_id: Optional[str] = None) -> ResearchEvent:
        """Log a structured event."""

        event = ResearchEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            timestamp=datetime.utcnow(),
            task_id=task_id or self.current_task_id or "unknown",
            session_id=self.session_id,
            data=data or {},
            duration_ms=duration_ms,
            error=error,
            error_type=error_type
        )

        # Add to memory
        self.events.append(event)

        # Write to file
        self._write_event_to_file(event)

        # Log to standard logger
        level = logging.ERROR if error else logging.INFO
        logger.log(level, f"[{event_type.value}] {task_id or 'no-task'}: {data}")

        return event

    def _write_event_to_file(self, event: ResearchEvent):
        """Write event to NDJSON file."""
        try:
            with open(self.events_file, "a", encoding="utf-8") as f:
                f.write(event.to_json() + "\n")
        except Exception as e:
            logger.error(f"Failed to write event to file: {e}")

    def log_research_started(self, task_id: str, query: str, config: Dict[str, Any]):
        """Log research process start."""
        return self.log_event(
            EventType.RESEARCH_STARTED,
            data={
                "query": query,
                "config": config,
                "start_time": datetime.utcnow().isoformat()
            },
            task_id=task_id
        )

    def log_research_completed(self, task_id: str, evidence_count: int,
                             quality_score: float, execution_time: float):
        """Log research process completion."""
        return self.log_event(
            EventType.RESEARCH_COMPLETED,
            data={
                "evidence_count": evidence_count,
                "quality_score": quality_score,
                "execution_time_seconds": execution_time,
                "end_time": datetime.utcnow().isoformat()
            },
            duration_ms=execution_time * 1000,
            task_id=task_id
        )

    def log_plan_created(self, task_id: str, query: str, subtask_count: int):
        """Log research plan creation."""
        return self.log_event(
            EventType.PLAN_CREATED,
            data={
                "query": query,
                "subtask_count": subtask_count,
                "planner_model": "SAPTIVA_OPS"
            },
            task_id=task_id
        )

    def log_search_executed(self, task_id: str, query: str, source: str,
                          results_count: int, duration_ms: float):
        """Log search execution."""
        return self.log_event(
            EventType.SEARCH_EXECUTED,
            data={
                "query": query,
                "source": source,
                "results_count": results_count
            },
            duration_ms=duration_ms,
            task_id=task_id
        )

    def log_evidence_collected(self, task_id: str, evidence_id: str,
                             source_url: str, score: float):
        """Log evidence collection."""
        return self.log_event(
            EventType.EVIDENCE_COLLECTED,
            data={
                "evidence_id": evidence_id,
                "source_url": source_url,
                "relevance_score": score
            },
            task_id=task_id
        )

    def log_evaluation_completed(self, task_id: str, iteration: int,
                               completion_score: float, gaps_found: int):
        """Log evaluation completion."""
        return self.log_event(
            EventType.EVALUATION_COMPLETED,
            data={
                "iteration": iteration,
                "completion_score": completion_score,
                "gaps_found": gaps_found,
                "evaluator_model": "SAPTIVA_CORTEX"
            },
            task_id=task_id
        )

    def log_iteration_started(self, task_id: str, iteration: int, queries: List[str]):
        """Log iteration start."""
        return self.log_event(
            EventType.ITERATION_STARTED,
            data={
                "iteration": iteration,
                "queries": queries,
                "query_count": len(queries)
            },
            task_id=task_id
        )

    def log_model_call(self, task_id: str, model: str, prompt_length: int,
                      response_length: int, duration_ms: float, error: Optional[str] = None):
        """Log model API call."""
        event_type = EventType.MODEL_CALL_FAILED if error else EventType.MODEL_CALL_COMPLETED

        return self.log_event(
            event_type,
            data={
                "model": model,
                "prompt_length": prompt_length,
                "response_length": response_length,
                "tokens_estimated": prompt_length + response_length
            },
            duration_ms=duration_ms,
            error=error,
            error_type="model_error" if error else None,
            task_id=task_id
        )

    def log_api_request(self, endpoint: str, method: str, params: Dict[str, Any]):
        """Log API request."""
        return self.log_event(
            EventType.API_REQUEST_RECEIVED,
            data={
                "endpoint": endpoint,
                "method": method,
                "params": params
            }
        )

    def get_events_for_task(self, task_id: str) -> List[ResearchEvent]:
        """Get all events for a specific task."""
        return [event for event in self.events if event.task_id == task_id]

    def export_events_ndjson(self, task_id: Optional[str] = None) -> str:
        """Export events as NDJSON string."""
        events_to_export = self.events
        if task_id:
            events_to_export = self.get_events_for_task(task_id)

        return "\n".join(event.to_json() for event in events_to_export)

    def get_task_metrics(self, task_id: str) -> Dict[str, Any]:
        """Get performance metrics for a task."""
        task_events = self.get_events_for_task(task_id)

        if not task_events:
            return {}

        start_events = [e for e in task_events if e.event_type == EventType.RESEARCH_STARTED]
        end_events = [e for e in task_events if e.event_type == EventType.RESEARCH_COMPLETED]

        metrics = {
            "total_events": len(task_events),
            "event_types": list(set(e.event_type.value for e in task_events)),
            "has_errors": any(e.error for e in task_events),
            "error_count": len([e for e in task_events if e.error])
        }

        if start_events and end_events:
            start_time = start_events[0].timestamp
            end_time = end_events[-1].timestamp
            duration = (end_time - start_time).total_seconds()
            metrics["total_duration_seconds"] = duration

        return metrics


# Global event logger instance
event_logger = EventLogger()


def get_event_logger() -> EventLogger:
    """Get the global event logger instance."""
    return event_logger


def log_research_event(event_type: EventType, data: Dict[str, Any],
                      task_id: Optional[str] = None, duration_ms: Optional[float] = None):
    """Convenience function to log events."""
    return event_logger.log_event(event_type, data, duration_ms, task_id=task_id)


class EventContext:
    """Context manager for tracking operation duration and logging events."""

    def __init__(self, event_type: EventType, task_id: str, data: Optional[Dict[str, Any]] = None):
        self.event_type = event_type
        self.task_id = task_id
        self.data = data or {}
        self.start_time = None
        self.logger = get_event_logger()

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - self.start_time) * 1000

        if exc_type:
            # Log as failed event
            failed_event_type = EventType(self.event_type.value.replace(".started", ".failed"))
            self.logger.log_event(
                failed_event_type,
                data=self.data,
                duration_ms=duration_ms,
                error=str(exc_val),
                error_type=exc_type.__name__,
                task_id=self.task_id
            )
        else:
            # Log as completed event
            completed_event_type = EventType(self.event_type.value.replace(".started", ".completed"))
            self.logger.log_event(
                completed_event_type,
                data=self.data,
                duration_ms=duration_ms,
                task_id=self.task_id
            )
