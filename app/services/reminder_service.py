"""
Medication Reminder Service (Feature 7)

CRUD operations for reminders stored in MongoDB `reminders` collection.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from bson import ObjectId

from app.db.mongodb import db
from app.utils.logger import get_logger

logger = get_logger(__name__)

COLLECTION = "reminders"


async def create_reminder(
    user_id: str,
    medication: str,
    time: str,
    frequency: str,
    notes: str,
) -> dict:
    """Insert a new reminder document and return it with reminder_id."""
    try:
        doc = {
            "user_id": user_id,
            "medication": medication,
            "time": time,
            "frequency": frequency,
            "notes": notes,
            "active": True,
            "created_at": datetime.utcnow(),
        }
        result = await db[COLLECTION].insert_one(doc)
        doc["reminder_id"] = str(result.inserted_id)
        doc["_id"] = str(result.inserted_id)
        return doc
    except Exception as exc:
        logger.error("Failed to create reminder: %s", exc)
        raise


async def list_reminders(user_id: str) -> list[dict]:
    """Return all active reminders for the user."""
    try:
        cursor = db[COLLECTION].find({"user_id": user_id, "active": True})
        reminders = []
        async for doc in cursor:
            doc["reminder_id"] = str(doc["_id"])
            doc["_id"] = str(doc["_id"])
            reminders.append(doc)
        return reminders
    except Exception as exc:
        logger.error("Failed to list reminders for user %s: %s", user_id, exc)
        return []


async def delete_reminder(user_id: str, reminder_id: str) -> bool:
    """Soft-delete a reminder (set active=False). Returns True if found."""
    try:
        result = await db[COLLECTION].update_one(
            {"_id": ObjectId(reminder_id), "user_id": user_id},
            {"$set": {"active": False}},
        )
        return result.matched_count > 0
    except Exception as exc:
        logger.error("Failed to delete reminder %s: %s", reminder_id, exc)
        return False


async def get_due_reminders(current_time_hhmm: str) -> list[dict]:
    """
    Return all active reminders whose `time` matches the current HH:MM.
    Used by the scheduler.
    """
    try:
        cursor = db[COLLECTION].find({"active": True, "time": current_time_hhmm})
        due = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            due.append(doc)
        return due
    except Exception as exc:
        logger.error("Failed to fetch due reminders at %s: %s", current_time_hhmm, exc)
        return []
