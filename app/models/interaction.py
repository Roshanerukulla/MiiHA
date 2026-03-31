"""Pydantic models for Drug Interaction Checker (Feature 4)."""
from __future__ import annotations

from typing import List

from pydantic import BaseModel, ConfigDict, field_validator


class DrugInteractionEntry(BaseModel):
    drug_a: str
    drug_b: str
    severity: str
    description: str


class InteractionCheckRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    medications: List[str]

    @field_validator("medications")
    @classmethod
    def validate_medications(cls, v: List[str]) -> List[str]:
        v = [m.strip() for m in v if m.strip()]
        if not v:
            raise ValueError("At least 1 medication is required")
        if len(v) > 20:
            raise ValueError("At most 20 medications allowed")
        return v


class InteractionCheckResponse(BaseModel):
    interactions: List[DrugInteractionEntry]
    safe_combinations: List[str]
    warnings: List[str]
