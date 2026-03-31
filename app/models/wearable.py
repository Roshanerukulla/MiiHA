"""Pydantic models for Wearable Integration (Feature 15)."""
from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, field_validator

SUPPORTED_METRIC_TYPES = {
    "heart_rate",
    "steps",
    "sleep_hours",
    "blood_pressure_systolic",
    "blood_pressure_diastolic",
    "weight",
    "blood_glucose",
    "spo2",
}


class HealthMetric(BaseModel):
    type: str
    value: float
    unit: str
    timestamp: str  # ISO 8601

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in SUPPORTED_METRIC_TYPES:
            raise ValueError(
                f"Unsupported metric type '{v}'. "
                f"Supported: {sorted(SUPPORTED_METRIC_TYPES)}"
            )
        return v


class WearableSyncRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    source: Literal["apple_health", "google_fit", "manual"]
    metrics: List[HealthMetric]

    @field_validator("metrics")
    @classmethod
    def metrics_not_empty(cls, v: List[HealthMetric]) -> List[HealthMetric]:
        if not v:
            raise ValueError("metrics list must not be empty")
        return v


class WearableSyncResponse(BaseModel):
    inserted_count: int
    source: str


class MetricSummary(BaseModel):
    metric_type: str
    avg_value: float
    unit: str
    data_points: int
    days: int
