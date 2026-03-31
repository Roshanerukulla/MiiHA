"""Pydantic models for Medication Reminders (Feature 7)."""
from __future__ import annotations

from typing import Literal, Optional
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class ReminderCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    medication: str
    time: str  # HH:MM 24-hour format
    frequency: Literal["daily", "twice_daily", "weekly"]
    notes: Optional[str] = ""

    @field_validator("medication")
    @classmethod
    def medication_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("medication must not be empty")
        return v

    @field_validator("time")
    @classmethod
    def validate_time(cls, v: str) -> str:
        import re
        if not re.match(r"^\d{2}:\d{2}$", v):
            raise ValueError("time must be in HH:MM format")
        hour, minute = int(v[:2]), int(v[3:])
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError("time must be a valid HH:MM value")
        return v


class ReminderResponse(BaseModel):
    reminder_id: str
    medication: str
    time: str
    frequency: str
    notes: Optional[str] = ""
    user_id: str
    created_at: datetime
    active: bool = True
