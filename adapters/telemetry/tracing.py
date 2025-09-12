"""
OpenTelemetry tracing setup for Aletheia Deep Research.
Provides distributed tracing across all research operations.
"""
from contextlib import contextmanager
from functools import wraps
import logging
import os
from typing import Any, Optional

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

logger = logging.getLogger(__name__)


class TelemetryManager:
    """Manages OpenTelemetry configuration and tracing for Aletheia."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TelemetryManager, cls).__new__(cls)
            cls._instance.tracer_provider = None
            cls._instance.tracer = None
            cls._instance.initialized = False
        return cls._instance

    def reset(self):
        """Resets the singleton instance. For testing purposes only."""
        self.tracer_provider = None
        self.tracer = None
        self.initialized = False
        TelemetryManager._instance = None

    def setup_tracing(self) -> None:
        """Initialize OpenTelemetry tracing."""
        if self.initialized:
            return

        try:
            # Create resource with service information
            resource = Resource.create({
                "service.name": "aletheia-deep-research",
                "service.version": "0.2.0",
                "service.namespace": "research",
                "deployment.environment": os.getenv("ENVIRONMENT", "development")
            })

            # Create tracer provider
            self.tracer_provider = TracerProvider(resource=resource)
            trace.set_tracer_provider(self.tracer_provider)

            # Configure exporters
            self._setup_exporters()

            # Get tracer
            self.tracer = trace.get_tracer("aletheia.research", "0.2.0")

            # Instrument libraries
            self._setup_instrumentation()

            self.initialized = True
            logger.info("OpenTelemetry tracing initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize OpenTelemetry: {e}")
            # Create a no-op tracer for graceful degradation
            self.tracer = trace.NoOpTracer()

    def _setup_exporters(self) -> None:
        """Setup span exporters."""
        if not self.tracer_provider:
            return

        # OTLP Exporter (for Jaeger, etc.)
        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
        if otlp_endpoint:
            try:
                otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
                otlp_processor = BatchSpanProcessor(otlp_exporter)
                self.tracer_provider.add_span_processor(otlp_processor)
                logger.info(f"OTLP exporter configured for {otlp_endpoint}")
            except Exception as e:
                logger.warning(f"Failed to setup OTLP exporter: {e}")

        # Console exporter for development
        if os.getenv("ENVIRONMENT") == "development":
            console_exporter = ConsoleSpanExporter()
            console_processor = BatchSpanProcessor(console_exporter)
            self.tracer_provider.add_span_processor(console_processor)

    def _setup_instrumentation(self) -> None:
        """Setup automatic instrumentation."""
        try:
            # Instrument HTTP clients
            HTTPXClientInstrumentor().instrument()
            logger.info("HTTPX instrumentation enabled")
        except Exception as e:
            logger.warning(f"Failed to instrument HTTPX: {e}")

    def instrument_fastapi(self, app) -> None:
        """Instrument FastAPI application."""
        if not self.initialized:
            self.setup_tracing()

        try:
            FastAPIInstrumentor.instrument_app(app)
            logger.info("FastAPI instrumentation enabled")
        except Exception as e:
            logger.warning(f"Failed to instrument FastAPI: {e}")

    def get_tracer(self) -> trace.Tracer:
        """Get the configured tracer."""
        if not self.initialized:
            self.setup_tracing()
        return self.tracer or trace.NoOpTracer()


# Global telemetry manager instance
telemetry_manager = TelemetryManager()


def get_tracer() -> trace.Tracer:
    """Get the global tracer instance."""
    return telemetry_manager.get_tracer()


@contextmanager
def trace_operation(name: str, attributes: Optional[dict[str, Any]] = None, tracer: Optional[trace.Tracer] = None):
    """Context manager for tracing operations."""
    if tracer is None:
        tracer = get_tracer()
    with tracer.start_as_current_span(name) as span:
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)

        try:
            yield span
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            raise


def trace_async_operation(operation_name: str, attributes: Optional[dict[str, Any]] = None):
    """Decorator for tracing async operations."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            tracer = get_tracer()
            with tracer.start_as_current_span(operation_name) as span:
                # Add attributes
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)

                # Add function info
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)

                try:
                    result = await func(*args, **kwargs)
                    span.set_status(trace.Status(trace.StatusCode.OK))
                    return result
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    raise
        return wrapper
    return decorator


def trace_sync_operation(operation_name: str, attributes: Optional[dict[str, Any]] = None):
    """Decorator for tracing sync operations."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            tracer = get_tracer()
            with tracer.start_as_current_span(operation_name) as span:
                # Add attributes
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)

                # Add function info
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)

                try:
                    result = func(*args, **kwargs)
                    span.set_status(trace.Status(trace.StatusCode.OK))
                    return result
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    raise
        return wrapper
    return decorator


def add_span_attributes(span: trace.Span, attributes: dict[str, Any]) -> None:
    """Helper to add multiple attributes to a span."""
    for key, value in attributes.items():
        span.set_attribute(key, value)


def record_research_metrics(span: trace.Span, evidence_count: int, execution_time: float,
                          quality_score: Optional[float] = None) -> None:
    """Record research-specific metrics in span."""
    span.set_attribute("research.evidence_count", evidence_count)
    span.set_attribute("research.execution_time_seconds", execution_time)
    if quality_score is not None:
        span.set_attribute("research.quality_score", quality_score)


def setup_telemetry() -> TelemetryManager:
    """Setup and return the global telemetry manager."""
    telemetry_manager.setup_tracing()
    return telemetry_manager
