import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, OperationFailure

from ports.database_port import DatabasePort

logger = logging.getLogger(__name__)


class MongoDBDatabase(DatabasePort):
    """MongoDB implementation of DatabasePort."""

    def __init__(self, connection_url: str, database_name: str):
        """
        Initialize MongoDB client.

        Args:
            connection_url: MongoDB connection URL
            database_name: Database name to use
        """
        self.connection_url = connection_url
        self.database_name = database_name
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        self._initialized = False

    async def initialize(self):
        """Initialize the MongoDB connection."""
        if self._initialized:
            return

        try:
            self.client = AsyncIOMotorClient(self.connection_url)
            self.db = self.client[self.database_name]

            # Create indexes
            await self.db.tasks.create_index("task_id", unique=True)
            await self.db.tasks.create_index("status")
            await self.db.tasks.create_index("created_at")

            await self.db.reports.create_index("task_id", unique=True)
            await self.db.reports.create_index("created_at")

            await self.db.logs.create_index("task_id")
            await self.db.logs.create_index("level")
            await self.db.logs.create_index("timestamp")

            self._initialized = True
            logger.info(f"MongoDB initialized: {self.database_name}")

        except Exception as e:
            logger.error(f"Failed to initialize MongoDB: {e}")
            raise

    # === Task Operations ===

    async def create_task(self, task_id: str, task_data: Dict[str, Any]) -> bool:
        """Create a new task record."""
        if not self._initialized:
            await self.initialize()

        try:
            task_document = {
                "task_id": task_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                **task_data
            }

            result = await self.db.tasks.insert_one(task_document)
            logger.info(f"Task created: {task_id}")
            return result.acknowledged

        except Exception as e:
            logger.error(f"Failed to create task {task_id}: {e}")
            return False

    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a task by ID."""
        if not self._initialized:
            await self.initialize()

        try:
            task = await self.db.tasks.find_one({"task_id": task_id})
            if task:
                # Remove MongoDB's _id field
                task.pop("_id", None)
            return task

        except Exception as e:
            logger.error(f"Failed to get task {task_id}: {e}")
            return None

    async def update_task(self, task_id: str, task_data: Dict[str, Any]) -> bool:
        """Update an existing task."""
        if not self._initialized:
            await self.initialize()

        try:
            update_data = {
                **task_data,
                "updated_at": datetime.utcnow()
            }

            result = await self.db.tasks.update_one(
                {"task_id": task_id},
                {"$set": update_data}
            )

            if result.modified_count > 0:
                logger.info(f"Task updated: {task_id}")
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to update task {task_id}: {e}")
            return False

    async def delete_task(self, task_id: str) -> bool:
        """Delete a task by ID."""
        if not self._initialized:
            await self.initialize()

        try:
            result = await self.db.tasks.delete_one({"task_id": task_id})
            if result.deleted_count > 0:
                logger.info(f"Task deleted: {task_id}")
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to delete task {task_id}: {e}")
            return False

    async def list_tasks(
        self,
        status: Optional[str] = None,
        limit: int = 100,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """List tasks with optional filtering."""
        if not self._initialized:
            await self.initialize()

        try:
            query = {}
            if status:
                query["status"] = status

            cursor = self.db.tasks.find(query).sort("created_at", -1).skip(skip).limit(limit)
            tasks = await cursor.to_list(length=limit)

            # Remove MongoDB's _id field from all tasks
            for task in tasks:
                task.pop("_id", None)

            return tasks

        except Exception as e:
            logger.error(f"Failed to list tasks: {e}")
            return []

    # === Report Operations ===

    async def create_report(self, task_id: str, report_data: Dict[str, Any]) -> bool:
        """Create or update a research report."""
        if not self._initialized:
            await self.initialize()

        try:
            report_document = {
                "task_id": task_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                **report_data
            }

            # Use upsert to create or update
            result = await self.db.reports.update_one(
                {"task_id": task_id},
                {"$set": report_document},
                upsert=True
            )

            logger.info(f"Report created/updated for task: {task_id}")
            return result.acknowledged

        except Exception as e:
            logger.error(f"Failed to create report for task {task_id}: {e}")
            return False

    async def get_report(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a report by task ID."""
        if not self._initialized:
            await self.initialize()

        try:
            report = await self.db.reports.find_one({"task_id": task_id})
            if report:
                # Remove MongoDB's _id field
                report.pop("_id", None)
            return report

        except Exception as e:
            logger.error(f"Failed to get report for task {task_id}: {e}")
            return None

    async def list_reports(
        self,
        limit: int = 100,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """List all reports."""
        if not self._initialized:
            await self.initialize()

        try:
            cursor = self.db.reports.find().sort("created_at", -1).skip(skip).limit(limit)
            reports = await cursor.to_list(length=limit)

            # Remove MongoDB's _id field from all reports
            for report in reports:
                report.pop("_id", None)

            return reports

        except Exception as e:
            logger.error(f"Failed to list reports: {e}")
            return []

    # === Log Operations ===

    async def create_log(self, log_data: Dict[str, Any]) -> bool:
        """Create a log entry."""
        if not self._initialized:
            await self.initialize()

        try:
            log_document = {
                "timestamp": datetime.utcnow(),
                **log_data
            }

            result = await self.db.logs.insert_one(log_document)
            return result.acknowledged

        except Exception as e:
            logger.error(f"Failed to create log: {e}")
            return False

    async def get_logs(
        self,
        task_id: Optional[str] = None,
        level: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """Retrieve logs with optional filtering."""
        if not self._initialized:
            await self.initialize()

        try:
            query = {}

            if task_id:
                query["task_id"] = task_id
            if level:
                query["level"] = level
            if start_time or end_time:
                query["timestamp"] = {}
                if start_time:
                    query["timestamp"]["$gte"] = start_time
                if end_time:
                    query["timestamp"]["$lte"] = end_time

            cursor = self.db.logs.find(query).sort("timestamp", -1).skip(skip).limit(limit)
            logs = await cursor.to_list(length=limit)

            # Remove MongoDB's _id field from all logs
            for log in logs:
                log.pop("_id", None)

            return logs

        except Exception as e:
            logger.error(f"Failed to get logs: {e}")
            return []

    # === Health Check ===

    async def health_check(self) -> bool:
        """Check if the database is available and healthy."""
        try:
            if not self._initialized:
                await self.initialize()

            # Ping the database
            await self.client.admin.command("ping")
            return True

        except (ConnectionFailure, OperationFailure) as e:
            logger.error(f"MongoDB health check failed: {e}")
            return False

    async def close(self) -> None:
        """Close database connections."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
            self._initialized = False
