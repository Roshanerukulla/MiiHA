"""
Conversation Memory Service (Feature 1)

Stores conversation turns in MongoDB `conversations` collection.
Loads last 5 turns as history for RAG context.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from bson import ObjectId

from app.db.mongodb import db
from app.utils.logger import get_logger

logger = get_logger(__name__)

COLLECTION = "conversations"
MAX_HISTORY_TURNS = 5


async def get_or_create_session(user_id: str, session_id: str) -> dict:
    """Retrieve an existing session document or create a new one."""
    doc = await db[COLLECTION].find_one(
        {"user_id": user_id, "session_id": session_id}
    )
    if doc is None:
        new_doc = {
            "user_id": user_id,
            "session_id": session_id,
            "turns": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        result = await db[COLLECTION].insert_one(new_doc)
        new_doc["_id"] = result.inserted_id
        return new_doc
    return doc


async def get_recent_history(user_id: str, session_id: str) -> list[dict]:
    """Return the last MAX_HISTORY_TURNS turns as plain dicts."""
    try:
        doc = await db[COLLECTION].find_one(
            {"user_id": user_id, "session_id": session_id}
        )
        if not doc:
            return []
        turns = doc.get("turns", [])
        # Return last N turns (each has role, content, timestamp)
        return [
            {"role": t["role"], "content": t["content"]}
            for t in turns[-MAX_HISTORY_TURNS:]
        ]
    except Exception as exc:
        logger.error("Failed to load history for session %s: %s", session_id, exc)
        return []


async def append_turn(
    user_id: str, session_id: str, role: str, content: str
) -> None:
    """Append a single turn to the conversation."""
    try:
        turn = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow(),
        }
        await db[COLLECTION].update_one(
            {"user_id": user_id, "session_id": session_id},
            {
                "$push": {"turns": turn},
                "$set": {"updated_at": datetime.utcnow()},
                "$setOnInsert": {
                    "user_id": user_id,
                    "session_id": session_id,
                    "created_at": datetime.utcnow(),
                },
            },
            upsert=True,
        )
    except Exception as exc:
        logger.error(
            "Failed to append turn for session %s: %s", session_id, exc
        )


async def get_full_history(user_id: str, session_id: str) -> dict:
    """Return the full conversation document."""
    try:
        doc = await db[COLLECTION].find_one(
            {"user_id": user_id, "session_id": session_id}
        )
        if not doc:
            return {"session_id": session_id, "user_id": user_id, "turns": []}
        doc["_id"] = str(doc["_id"])
        return doc
    except Exception as exc:
        logger.error("Failed to fetch history for session %s: %s", session_id, exc)
        return {"session_id": session_id, "user_id": user_id, "turns": []}


async def delete_session(user_id: str, session_id: str) -> int:
    """Delete a session. Returns number of deleted documents."""
    try:
        result = await db[COLLECTION].delete_one(
            {"user_id": user_id, "session_id": session_id}
        )
        return result.deleted_count
    except Exception as exc:
        logger.error("Failed to delete session %s: %s", session_id, exc)
        return 0
