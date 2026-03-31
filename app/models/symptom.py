"""Pydantic models for Symptom Checker (Feature 3)."""
from __future__ import annotations

from typing import List, Literal

from pydantic import BaseModel, ConfigDict, field_validator


class SymptomCheckRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    symptoms: List[str]
    duration_days: int
    severity: Literal["mild", "moderate", "severe"]
    age: int
    gender: str

    @field_validator("symptoms")
    @classmethod
    def symptoms_not_empty(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("At least one symptom is required")
        return [s.strip() for s in v if s.strip()]

    @field_validator("age")
    @classmethod
    def age_valid(cls, v: int) -> int:
        if v < 0 or v > 130:
            raise ValueError("Age must be between 0 and 130")
        return v

    @field_validator("duration_days")
    @classmethod
    def duration_valid(cls, v: int) -> int:
        if v < 0:
            raise ValueError("duration_days must be non-negative")
        return v


class SymptomCheckResponse(BaseModel):
    possible_conditions: List[str]
    urgency: str
    next_steps: List[str]
    disclaimer: str
