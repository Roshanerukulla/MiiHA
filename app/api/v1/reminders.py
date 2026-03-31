"""
Medication Reminders API (Feature 7)

POST   /api/v1/reminders                — create a reminder
GET    /api/v1/reminders                — list user's reminders
DELETE /api/v1/reminders/{reminder_id}  — delete a reminder
"""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_current_user
from app.models.reminder import ReminderCreate, ReminderResponse
from app.services.reminder_service import (
    create_reminder,
    delete_reminder,
    list_reminders,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/reminders", tags=["reminders"])


@router.post("", response_model=ReminderResponse, status_code=status.HTTP_201_CREATED)
async def add_reminder(
    request: ReminderCreate,
    user: dict = Depends(get_current_user),
) -> ReminderResponse:
    """Create a new medication reminder."""
    user_id = str(user["_id"])
    doc = await create_reminder(
        user_id=user_id,
        medication=request.medication,
        time=request.time,
        frequency=request.frequency,
        notes=request.notes or "",
    )
    return ReminderResponse(
        reminder_id=doc["reminder_id"],
        medication=doc["medication"],
        time=doc["time"],
        frequency=doc["frequency"],
        notes=doc.get("notes", ""),
        user_id=doc["user_id"],
        created_at=doc["created_at"],
        active=doc.get("active", True),
    )


@router.get("", response_model=List[ReminderResponse])
async def get_reminders(
    user: dict = Depends(get_current_user),
) -> List[ReminderResponse]:
    """List all active reminders for the authenticated user."""
    user_id = str(user["_id"])
    docs = await list_reminders(user_id)
    return [
        ReminderResponse(
            reminder_id=d["reminder_id"],
            medication=d["medication"],
            time=d["time"],
            frequency=d["frequency"],
            notes=d.get("notes", ""),
            user_id=d["user_id"],
            created_at=d["created_at"],
            active=d.get("active", True),
        )
        for d in docs
    ]


@router.delete("/{reminder_id}", status_code=status.HTTP_200_OK)
async def remove_reminder(
    reminder_id: str,
    user: dict = Depends(get_current_user),
) -> dict:
    """Delete (deactivate) a medication reminder."""
    user_id = str(user["_id"])
    found = await delete_reminder(user_id, reminder_id)
    if not found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found",
        )
    return {"message": "Reminder deleted successfully"}
