from __future__ import annotations

from pydantic import BaseModel


class ResearchSubTask(BaseModel):
    id: str
    query: str
    sources: list[str] = ["web"]  # e.g., web, pdf, etc.
    completed: bool = False


class ResearchPlan(BaseModel):
    main_query: str
    sub_tasks: list[ResearchSubTask] = []
