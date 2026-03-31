"""Pydantic models for Feedback Loop (Feature 11)."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, field_validator


class FeedbackCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    query_id: str
    rating: Literal[1, 2, 3, 4, 5]
    comment: Optional[str] = ""

    @field_validator("query_id")
    @classmethod
    def query_id_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("query_id must not be empty")
        return v


class FeedbackStats(BaseModel):
    avg_rating: float
    total_count: int
    rating_distribution: dict
