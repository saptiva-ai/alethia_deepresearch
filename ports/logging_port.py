from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class LogLevel(Enum):
    """Log levels for structured logging."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class LoggingPort(ABC):
    """Port for structured logging operations."""

    @abstractmethod
    def log(self, level: LogLevel, message: str, **kwargs: Any) -> bool:
        """
        Log a message with structured data.

        Args:
            level: Log level
            message: Log message
            **kwargs: Additional structured data

        Returns:
            True if logged successfully, False otherwise
        """
        pass

    @abstractmethod
    def log_event(self, event_type: str, data: dict[str, Any], task_id: Optional[str] = None) -> bool:
        """
        Log a structured event.

        Args:
            event_type: Type of event (e.g., "research.started", "plan.created")
            data: Event data
            task_id: Optional task identifier

        Returns:
            True if logged successfully, False otherwise
        """
        pass

    @abstractmethod
    def log_error(self, error: Exception, context: dict[str, Any] = None) -> bool:
        """
        Log an error with context.

        Args:
            error: Exception object
            context: Additional context data

        Returns:
            True if logged successfully, False otherwise
        """
        pass

    @abstractmethod
    def log_performance(self, operation: str, duration: float, metadata: dict[str, Any] = None) -> bool:
        """
        Log performance metrics.

        Args:
            operation: Name of the operation
            duration: Duration in seconds
            metadata: Additional performance metadata

        Returns:
            True if logged successfully, False otherwise
        """
        pass

    @abstractmethod
    def log_api_call(self, service: str, endpoint: str, status_code: int, duration: float, **kwargs: Any) -> bool:
        """
        Log API call details.

        Args:
            service: Service name (e.g., "saptiva", "tavily")
            endpoint: API endpoint
            status_code: HTTP status code
            duration: Call duration in seconds
            **kwargs: Additional call metadata

        Returns:
            True if logged successfully, False otherwise
        """
        pass

    @abstractmethod
    def create_correlation_id(self) -> str:
        """
        Create a unique correlation ID for tracking requests.

        Returns:
            Unique correlation ID
        """
        pass

    @abstractmethod
    def get_logs(self, task_id: Optional[str] = None,
                 start_time: Optional[datetime] = None,
                 end_time: Optional[datetime] = None,
                 level: Optional[LogLevel] = None) -> list[dict[str, Any]]:
        """
        Retrieve logs based on filters.

        Args:
            task_id: Optional task ID filter
            start_time: Optional start time filter
            end_time: Optional end time filter
            level: Optional log level filter

        Returns:
            List of log entries
        """
        pass

    @abstractmethod
    def export_logs(self, file_path: str, format: str = "ndjson", **filters: Any) -> bool:
        """
        Export logs to a file.

        Args:
            file_path: Path to save logs
            format: Export format ("ndjson", "json", "csv")
            **filters: Log filters

        Returns:
            True if export successful, False otherwise
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if the logging service is available and healthy.

        Returns:
            True if healthy, False otherwise
        """
        pass
