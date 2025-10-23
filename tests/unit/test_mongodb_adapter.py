"""Unit tests for MongoDB adapter."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from adapters.mongodb.mongodb_database import MongoDBDatabase


@pytest.fixture
def mock_motor_client():
    """Mock Motor AsyncIOMotorClient."""
    with patch("adapters.mongodb.mongodb_database.AsyncIOMotorClient") as mock:
        client = AsyncMock()
        db = AsyncMock()

        # Mock collections
        db.tasks = AsyncMock()
        db.reports = AsyncMock()
        db.logs = AsyncMock()

        client.__getitem__.return_value = db
        mock.return_value = client

        yield mock


@pytest.fixture
async def mongodb_adapter(mock_motor_client):
    """Create MongoDB adapter instance."""
    adapter = MongoDBDatabase(
        connection_url="mongodb://test:test@localhost:27017",
        database_name="test_db"
    )
    await adapter.initialize()
    return adapter


@pytest.mark.asyncio
class TestMongoDBDatabase:
    """Test suite for MongoDB database adapter."""

    async def test_initialization(self, mock_motor_client):
        """Test MongoDB initialization."""
        adapter = MongoDBDatabase(
            connection_url="mongodb://test:test@localhost:27017",
            database_name="test_db"
        )

        assert not adapter._initialized
        await adapter.initialize()
        assert adapter._initialized

        # Verify indexes were created
        adapter.db.tasks.create_index.assert_called()
        adapter.db.reports.create_index.assert_called()
        adapter.db.logs.create_index.assert_called()

    async def test_create_task(self, mongodb_adapter):
        """Test task creation."""
        task_id = "test-task-123"
        task_data = {
            "status": "accepted",
            "query": "Test query",
            "started_at": 1234567890.0
        }

        # Mock insert result
        mongodb_adapter.db.tasks.insert_one.return_value = AsyncMock(acknowledged=True)

        result = await mongodb_adapter.create_task(task_id, task_data)

        assert result is True
        mongodb_adapter.db.tasks.insert_one.assert_called_once()

        # Verify the document has required fields
        call_args = mongodb_adapter.db.tasks.insert_one.call_args[0][0]
        assert call_args["task_id"] == task_id
        assert call_args["status"] == "accepted"
        assert "created_at" in call_args
        assert "updated_at" in call_args

    async def test_get_task(self, mongodb_adapter):
        """Test task retrieval."""
        task_id = "test-task-123"
        expected_task = {
            "_id": "mock_id",
            "task_id": task_id,
            "status": "completed",
            "query": "Test query"
        }

        mongodb_adapter.db.tasks.find_one.return_value = expected_task.copy()

        result = await mongodb_adapter.get_task(task_id)

        assert result is not None
        assert result["task_id"] == task_id
        assert "_id" not in result  # Should be removed
        mongodb_adapter.db.tasks.find_one.assert_called_once_with({"task_id": task_id})

    async def test_get_task_not_found(self, mongodb_adapter):
        """Test task retrieval when task doesn't exist."""
        mongodb_adapter.db.tasks.find_one.return_value = None

        result = await mongodb_adapter.get_task("nonexistent")

        assert result is None

    async def test_update_task(self, mongodb_adapter):
        """Test task update."""
        task_id = "test-task-123"
        update_data = {"status": "completed", "evidence_count": 10}

        # Mock update result
        mock_result = AsyncMock(modified_count=1)
        mongodb_adapter.db.tasks.update_one.return_value = mock_result

        result = await mongodb_adapter.update_task(task_id, update_data)

        assert result is True
        mongodb_adapter.db.tasks.update_one.assert_called_once()

        # Verify updated_at is added
        call_args = mongodb_adapter.db.tasks.update_one.call_args[0]
        assert "updated_at" in call_args[1]["$set"]

    async def test_update_task_not_modified(self, mongodb_adapter):
        """Test task update when no documents modified."""
        mock_result = AsyncMock(modified_count=0)
        mongodb_adapter.db.tasks.update_one.return_value = mock_result

        result = await mongodb_adapter.update_task("nonexistent", {"status": "failed"})

        assert result is False

    async def test_delete_task(self, mongodb_adapter):
        """Test task deletion."""
        task_id = "test-task-123"
        mock_result = AsyncMock(deleted_count=1)
        mongodb_adapter.db.tasks.delete_one.return_value = mock_result

        result = await mongodb_adapter.delete_task(task_id)

        assert result is True
        mongodb_adapter.db.tasks.delete_one.assert_called_once_with({"task_id": task_id})

    async def test_list_tasks(self, mongodb_adapter):
        """Test listing tasks."""
        mock_tasks = [
            {"_id": "1", "task_id": "task-1", "status": "completed"},
            {"_id": "2", "task_id": "task-2", "status": "running"}
        ]

        # Mock cursor - return same mock for chaining
        mock_cursor = MagicMock()
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_cursor.skip = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)
        mock_cursor.to_list = AsyncMock(return_value=mock_tasks)

        mongodb_adapter.db.tasks.find = MagicMock(return_value=mock_cursor)

        result = await mongodb_adapter.list_tasks(status="completed", limit=10, skip=0)

        assert len(result) == 2
        assert all("_id" not in task for task in result)
        mongodb_adapter.db.tasks.find.assert_called_once_with({"status": "completed"})

    async def test_create_report(self, mongodb_adapter):
        """Test report creation."""
        task_id = "test-task-123"
        report_data = {
            "content": "# Test Report\n\nContent here",
            "query": "Test query"
        }

        mock_result = AsyncMock(acknowledged=True)
        mongodb_adapter.db.reports.update_one.return_value = mock_result

        result = await mongodb_adapter.create_report(task_id, report_data)

        assert result is True
        mongodb_adapter.db.reports.update_one.assert_called_once()

    async def test_get_report(self, mongodb_adapter):
        """Test report retrieval."""
        task_id = "test-task-123"
        expected_report = {
            "_id": "mock_id",
            "task_id": task_id,
            "content": "# Report content",
            "created_at": datetime.utcnow()
        }

        mongodb_adapter.db.reports.find_one.return_value = expected_report.copy()

        result = await mongodb_adapter.get_report(task_id)

        assert result is not None
        assert result["task_id"] == task_id
        assert "_id" not in result

    async def test_list_reports(self, mongodb_adapter):
        """Test listing reports."""
        mock_reports = [
            {"_id": "1", "task_id": "task-1", "content": "Report 1"},
            {"_id": "2", "task_id": "task-2", "content": "Report 2"}
        ]

        mock_cursor = MagicMock()
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_cursor.skip = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)
        mock_cursor.to_list = AsyncMock(return_value=mock_reports)

        mongodb_adapter.db.reports.find = MagicMock(return_value=mock_cursor)

        result = await mongodb_adapter.list_reports(limit=10, skip=0)

        assert len(result) == 2
        assert all("_id" not in report for report in result)

    async def test_create_log(self, mongodb_adapter):
        """Test log creation."""
        log_data = {
            "task_id": "test-task-123",
            "level": "INFO",
            "message": "Test log message"
        }

        mock_result = AsyncMock(acknowledged=True)
        mongodb_adapter.db.logs.insert_one.return_value = mock_result

        result = await mongodb_adapter.create_log(log_data)

        assert result is True
        mongodb_adapter.db.logs.insert_one.assert_called_once()

    async def test_get_logs(self, mongodb_adapter):
        """Test log retrieval with filters."""
        mock_logs = [
            {"_id": "1", "task_id": "task-1", "level": "ERROR", "message": "Error 1"},
            {"_id": "2", "task_id": "task-1", "level": "ERROR", "message": "Error 2"}
        ]

        mock_cursor = MagicMock()
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_cursor.skip = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)
        mock_cursor.to_list = AsyncMock(return_value=mock_logs)

        mongodb_adapter.db.logs.find = MagicMock(return_value=mock_cursor)

        result = await mongodb_adapter.get_logs(
            task_id="task-1",
            level="ERROR",
            limit=10,
            skip=0
        )

        assert len(result) == 2
        assert all("_id" not in log for log in result)

    async def test_health_check_success(self, mongodb_adapter):
        """Test health check when database is healthy."""
        mongodb_adapter.client.admin.command = AsyncMock(return_value={"ok": 1})

        result = await mongodb_adapter.health_check()

        assert result is True

    async def test_health_check_failure(self, mongodb_adapter):
        """Test health check when database is unhealthy."""
        from pymongo.errors import ConnectionFailure

        mongodb_adapter.client.admin.command = AsyncMock(
            side_effect=ConnectionFailure("Connection failed")
        )

        result = await mongodb_adapter.health_check()

        assert result is False

    async def test_close_connection(self, mongodb_adapter):
        """Test closing database connection."""
        await mongodb_adapter.close()

        mongodb_adapter.client.close.assert_called_once()
        assert mongodb_adapter._initialized is False

    async def test_error_handling_create_task(self, mongodb_adapter):
        """Test error handling in create_task."""
        mongodb_adapter.db.tasks.insert_one.side_effect = Exception("Database error")

        result = await mongodb_adapter.create_task("task-123", {"status": "accepted"})

        assert result is False

    async def test_error_handling_get_task(self, mongodb_adapter):
        """Test error handling in get_task."""
        mongodb_adapter.db.tasks.find_one.side_effect = Exception("Database error")

        result = await mongodb_adapter.get_task("task-123")

        assert result is None
