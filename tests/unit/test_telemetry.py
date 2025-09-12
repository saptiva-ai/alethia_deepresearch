"""
Tests for the telemetry adapter, including tracing and event logging.
"""
import asyncio
import os
from unittest.mock import MagicMock, patch, call, mock_open

import pytest
from opentelemetry import trace

from adapters.telemetry.tracing import (
    TelemetryManager,
    get_tracer,
    setup_telemetry,
    trace_async_operation,
    trace_sync_operation,
)
from adapters.telemetry.events import (
    EventLogger,
    EventType,
    get_event_logger,
    ResearchEvent,
)


@pytest.fixture(autouse=True)
def reset_telemetry_state():
    """Reset telemetry state between tests."""
    # Clear any existing global tracer provider
    trace.set_tracer_provider(None)
    # Reset singleton
    if TelemetryManager._instance is not None:
        TelemetryManager._instance = None
    yield
    # Clean up after test
    if TelemetryManager._instance is not None:
        TelemetryManager._instance = None


class TestTelemetryManager:
    """Tests for the TelemetryManager."""

    @patch("adapters.telemetry.tracing.OTLPSpanExporter")
    @patch("adapters.telemetry.tracing.ConsoleSpanExporter")
    @patch.dict(os.environ, {"OTEL_EXPORTER_OTLP_ENDPOINT": "http://localhost:4317", "ENVIRONMENT": "development"})
    def test_setup_tracing_full(self, mock_console_exporter, mock_otlp_exporter):
        """Test setup_tracing with both OTLP and console exporters."""
        manager = TelemetryManager()
        manager.setup_tracing()

        assert manager.initialized
        assert manager.tracer is not None
        mock_otlp_exporter.assert_called_once()
        mock_console_exporter.assert_called_once()
        assert len(manager.tracer_provider._active_span_processor._span_processors) == 2

    @patch.dict(os.environ, {}, clear=True)
    def test_setup_tracing_no_exporters(self):
        """Test setup_tracing with no exporters configured."""
        manager = TelemetryManager()
        manager.setup_tracing()

        assert manager.initialized
        assert len(manager.tracer_provider._active_span_processor._span_processors) == 0

    @patch.object(TelemetryManager, 'setup_tracing')
    def test_get_tracer_uninitialized(self, mock_setup):
        """Test that get_tracer calls setup_tracing when not initialized."""
        manager = TelemetryManager()
        manager.initialized = False
        manager.tracer = None
        
        # Mock setup_tracing to set a NoOpTracer
        def mock_setup_side_effect():
            manager.tracer = trace.NoOpTracer()
            manager.initialized = True
        mock_setup.side_effect = mock_setup_side_effect
        
        tracer = manager.get_tracer()
        mock_setup.assert_called_once()
        assert isinstance(tracer, trace.NoOpTracer)

    def test_get_tracer_initialized(self):
        """Test that get_tracer returns a real tracer after initialization."""
        manager = TelemetryManager()
        manager.setup_tracing()
        tracer = manager.get_tracer()
        assert not isinstance(tracer, trace.NoOpTracer)


@pytest.mark.asyncio
async def test_trace_async_operation_decorator():
    """Test the trace_async_operation decorator can execute without errors."""
    @trace_async_operation("test_op", {"attr1": "value1"})
    async def my_async_func(x, y):
        return x + y

    # Test that the decorator works without errors
    result = await my_async_func(1, 2)
    assert result == 3


def test_trace_sync_operation_decorator():
    """Test the trace_sync_operation decorator."""
    mock_tracer = MagicMock()
    mock_span = MagicMock()
    mock_tracer.start_as_current_span.return_value.__enter__.return_value = mock_span

    @trace_sync_operation("test_sync_op")
    def my_sync_func(x, y):
        return x * y

    with patch("adapters.telemetry.tracing.get_tracer", return_value=mock_tracer):
        result = my_sync_func(3, 4)

    assert result == 12
    mock_tracer.start_as_current_span.assert_called_once_with("test_sync_op")
    mock_span.set_attribute.assert_any_call("function.name", "my_sync_func")
    mock_span.set_status.assert_called_once()
    status_arg = mock_span.set_status.call_args[0][0]
    assert status_arg.status_code == trace.StatusCode.OK


@pytest.mark.asyncio
async def test_trace_async_operation_exception():
    """Test that the decorator properly propagates exceptions."""
    @trace_async_operation("test_op_fail")
    async def my_failing_func():
        raise ValueError("Test error")

    # Test that exceptions are properly propagated
    with pytest.raises(ValueError, match="Test error"):
        await my_failing_func()


class TestEventLogger:
    """Tests for the EventLogger."""

    @patch("builtins.open")
    @patch("os.makedirs")
    def test_log_event(self, mock_makedirs, mock_open):
        """Test the core log_event method."""
        logger = EventLogger()
        logger.set_task_context("task-123")

        event = logger.log_event(
            EventType.RESEARCH_STARTED,
            data={"query": "test"},
            duration_ms=10.5,
        )

        assert len(logger.events) == 1
        assert event.event_type == EventType.RESEARCH_STARTED
        assert event.task_id == "task-123"
        assert event.data["query"] == "test"
        assert event.duration_ms == 10.5
        mock_open.assert_called_with(logger.events_file, "a", encoding="utf-8")
        # Verify that the file handle write method was called
        mock_file_handle = mock_open.return_value.__enter__.return_value
        mock_file_handle.write.assert_called_once()

    def test_log_research_started(self):
        """Test the specific log_research_started method."""
        logger = EventLogger()
        logger.log_event = MagicMock()

        logger.log_research_started("task-abc", "my query", {"config": 1})

        logger.log_event.assert_called_once()
        args, kwargs = logger.log_event.call_args
        assert args[0] == EventType.RESEARCH_STARTED
        assert kwargs['data']['query'] == "my query"
        assert kwargs['task_id'] == "task-abc"

    def test_get_events_for_task(self):
        """Test filtering events by task_id."""
        logger = EventLogger()
        logger.log_event(EventType.RESEARCH_STARTED, task_id="task-1")
        logger.log_event(EventType.PLAN_CREATED, task_id="task-2")
        logger.log_event(EventType.RESEARCH_COMPLETED, task_id="task-1")

        task_1_events = logger.get_events_for_task("task-1")
        assert len(task_1_events) == 2
        assert task_1_events[0].event_type == EventType.RESEARCH_STARTED
        assert task_1_events[1].event_type == EventType.RESEARCH_COMPLETED

    def test_export_events_ndjson(self):
        """Test exporting events to NDJSON."""
        logger = EventLogger()
        event1 = logger.log_event(EventType.RESEARCH_STARTED, task_id="task-1")
        event2 = logger.log_event(EventType.PLAN_CREATED, task_id="task-1")

        ndjson = logger.export_events_ndjson(task_id="task-1")
        lines = ndjson.strip().split('\n')

        assert len(lines) == 2
        assert '"event_type": "research.started"' in lines[0]
        assert '"event_type": "plan.created"' in lines[1]