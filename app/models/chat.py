"""Pydantic models for Conversation Memory (Feature 1)."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, field_validator


class ConversationTurn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = None  # type: ignore[assignment]

    @field_validator("timestamp", mode="before")
    @classmethod
    def set_timestamp(cls, v):
        return v or datetime.utcnow()

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in ("user", "assistant"):
            raise ValueError("role must be 'user' or 'assistant'")
        return v


class ChatRequest(BaseModel):
    message: str
    session_id: str

    @field_validator("message")
    @classmethod
    def message_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("message must not be empty")
        if len(v) > 2000:
            raise ValueError("message must be at most 2000 characters")
        return v


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    query_id: Optional[str] = None
    cached: bool = False
    detected_language: Optional[str] = None
    translated: bool = False


class ConversationHistoryResponse(BaseModel):
    session_id: str
    user_id: str
    turns: List[ConversationTurn] = []
