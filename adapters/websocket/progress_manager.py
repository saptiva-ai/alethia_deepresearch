"""
WebSocket Progress Manager for real-time research updates.

This manager handles WebSocket connections and broadcasts progress updates
to clients monitoring research tasks.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

from fastapi import WebSocket


@dataclass
class ProgressUpdate:
    """Represents a progress update for a research task."""

    task_id: str
    timestamp: str
    event_type: str  # started, iteration, evidence, evaluation, gap_analysis, refinement, completed, failed
    message: str
    data: dict[str, Any] | None = None

    def to_json(self) -> str:
        """Convert to JSON string for WebSocket transmission."""
        return json.dumps(asdict(self))

    @classmethod
    def create(
        cls,
        task_id: str,
        event_type: str,
        message: str,
        data: dict[str, Any] | None = None,
    ) -> ProgressUpdate:
        """Factory method to create a progress update with current timestamp."""
        return cls(
            task_id=task_id,
            timestamp=datetime.utcnow().isoformat(),
            event_type=event_type,
            message=message,
            data=data,
        )


class ProgressManager:
    """
    Manages WebSocket connections and broadcasts progress updates.

    Singleton pattern to ensure only one manager exists across the application.
    """

    _instance: ProgressManager | None = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # Store active WebSocket connections per task_id
        self._connections: dict[str, list[WebSocket]] = {}
        # Create lock when event loop is available
        self._lock = asyncio.Lock()
        self._initialized = True

    async def connect(self, websocket: WebSocket, task_id: str):
        """Register a new WebSocket connection for a task."""
        await websocket.accept()

        async with self._lock:
            if task_id not in self._connections:
                self._connections[task_id] = []
            self._connections[task_id].append(websocket)

        print(f"📡 WebSocket connected for task {task_id} (total: {len(self._connections[task_id])})")

    async def disconnect(self, websocket: WebSocket, task_id: str):
        """Remove a WebSocket connection."""
        async with self._lock:
            if task_id in self._connections:
                if websocket in self._connections[task_id]:
                    self._connections[task_id].remove(websocket)
                    print(f"📡 WebSocket disconnected for task {task_id} (remaining: {len(self._connections[task_id])})")

                # Clean up empty lists
                if not self._connections[task_id]:
                    del self._connections[task_id]

    async def broadcast(self, update: ProgressUpdate):
        """
        Broadcast a progress update to all clients watching this task.

        Failed connections are automatically removed.
        """
        task_id = update.task_id

        async with self._lock:
            if task_id not in self._connections:
                # No one is watching this task
                return

            connections = self._connections[task_id].copy()

        # Broadcast to all connections (outside the lock to avoid deadlock)
        failed_connections = []

        for websocket in connections:
            try:
                await websocket.send_text(update.to_json())
            except Exception as e:
                print(f"⚠️  Failed to send to WebSocket: {e}")
                failed_connections.append(websocket)

        # Remove failed connections
        if failed_connections:
            async with self._lock:
                for websocket in failed_connections:
                    if task_id in self._connections and websocket in self._connections[task_id]:
                        self._connections[task_id].remove(websocket)

    def has_listeners(self, task_id: str) -> bool:
        """Check if anyone is listening to updates for this task."""
        return task_id in self._connections and len(self._connections[task_id]) > 0

    def get_connection_count(self, task_id: str) -> int:
        """Get the number of active connections for a task."""
        return len(self._connections.get(task_id, []))


# Global singleton instance
_progress_manager: ProgressManager | None = None


def get_progress_manager() -> ProgressManager:
    """Get or create the global progress manager instance."""
    global _progress_manager
    if _progress_manager is None:
        _progress_manager = ProgressManager()
    return _progress_manager
