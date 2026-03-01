from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

EventTypeLiteral = Literal["working", "idle", "absent", "product_count"]


class AIEventIn(BaseModel):
    timestamp: datetime
    worker_id: str
    workstation_id: str
    event_type: EventTypeLiteral
    confidence: float = Field(ge=0.0, le=1.0)
    count: int = Field(default=1, ge=0)

    @field_validator("count")
    @classmethod
    def count_for_non_product_events(cls, value: int) -> int:
        return value


class IngestResponse(BaseModel):
    inserted: int
    duplicates: int


class SeedResponse(BaseModel):
    status: str
    workers: int
    workstations: int
    events: int
