from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class DatabasePort(ABC):
    """Port for database operations (tasks, reports, logs)."""

    # === Task Operations ===

    @abstractmethod
    async def create_task(self, task_id: str, task_data: dict[str, Any]) -> bool:
        """
        Create a new task record.

        Args:
            task_id: Unique task identifier
            task_data: Task data dictionary

        Returns:
            True if created successfully, False otherwise
        """
        pass

    @abstractmethod
    async def get_task(self, task_id: str) -> dict[str, Any] | None:
        """
        Retrieve a task by ID.

        Args:
            task_id: Task identifier

        Returns:
            Task data dictionary or None if not found
        """
        pass

    @abstractmethod
    async def update_task(self, task_id: str, task_data: dict[str, Any]) -> bool:
        """
        Update an existing task.

        Args:
            task_id: Task identifier
            task_data: Updated task data

        Returns:
            True if updated successfully, False otherwise
        """
        pass

    @abstractmethod
    async def delete_task(self, task_id: str) -> bool:
        """
        Delete a task by ID.

        Args:
            task_id: Task identifier

        Returns:
            True if deleted successfully, False otherwise
        """
        pass

    @abstractmethod
    async def list_tasks(
        self,
        status: str | None = None,
        limit: int = 100,
        skip: int = 0
    ) -> list[dict[str, Any]]:
        """
        List tasks with optional filtering.

        Args:
            status: Optional status filter (e.g., "completed", "failed")
            limit: Maximum number of tasks to return
            skip: Number of tasks to skip (pagination)

        Returns:
            List of task dictionaries
        """
        pass

    # === Report Operations ===

    @abstractmethod
    async def create_report(self, task_id: str, report_data: dict[str, Any]) -> bool:
        """
        Create or update a research report.

        Args:
            task_id: Associated task identifier
            report_data: Report data dictionary

        Returns:
            True if created successfully, False otherwise
        """
        pass

    @abstractmethod
    async def get_report(self, task_id: str) -> dict[str, Any] | None:
        """
        Retrieve a report by task ID.

        Args:
            task_id: Task identifier

        Returns:
            Report data dictionary or None if not found
        """
        pass

    @abstractmethod
    async def list_reports(
        self,
        limit: int = 100,
        skip: int = 0
    ) -> list[dict[str, Any]]:
        """
        List all reports.

        Args:
            limit: Maximum number of reports to return
            skip: Number of reports to skip (pagination)

        Returns:
            List of report dictionaries
        """
        pass

    # === Log Operations ===

    @abstractmethod
    async def create_log(self, log_data: dict[str, Any]) -> bool:
        """
        Create a log entry.

        Args:
            log_data: Log data dictionary (should include timestamp, level, message, etc.)

        Returns:
            True if created successfully, False otherwise
        """
        pass

    @abstractmethod
    async def get_logs(
        self,
        task_id: str | None = None,
        level: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
        skip: int = 0
    ) -> list[dict[str, Any]]:
        """
        Retrieve logs with optional filtering.

        Args:
            task_id: Optional task ID filter
            level: Optional log level filter (e.g., "ERROR", "INFO")
            start_time: Optional start time filter
            end_time: Optional end time filter
            limit: Maximum number of logs to return
            skip: Number of logs to skip (pagination)

        Returns:
            List of log dictionaries
        """
        pass

    # === Health Check ===

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the database is available and healthy.

        Returns:
            True if healthy, False otherwise
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """
        Close database connections.
        """
        pass
