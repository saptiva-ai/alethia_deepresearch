from datetime import datetime

from pydantic import BaseModel, Field


class EvidenceSource(BaseModel):
    url: str
    title: str
    fetched_at: datetime = Field(default_factory=datetime.utcnow)


class Evidence(BaseModel):
    id: str
    source: EvidenceSource
    excerpt: str
    hash: str | None = None
    tool_call_id: str | None = None
    score: float | None = None
    tags: list[str] = []
    cit_key: str | None = None
