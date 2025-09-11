from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class EvidenceSource(BaseModel):
    url: str
    title: str
    fetched_at: datetime = Field(default_factory=datetime.utcnow)

class Evidence(BaseModel):
    id: str
    source: EvidenceSource
    excerpt: str
    hash: Optional[str] = None
    tool_call_id: Optional[str] = None
    score: Optional[float] = None
    tags: list[str] = []
    cit_key: Optional[str] = None
