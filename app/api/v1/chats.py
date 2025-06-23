from fastapi import APIRouter, HTTPException, Depends, Query
from datetime import datetime
from typing import List, Optional
from app.core.dependencies import get_current_user
from app.db.mongodb import db
import uuid

router = APIRouter()

# Create a new chat session
@router.post("/chat/start")
async def start_chat_session(session_name: Optional[str] = "Chat with MIIHA", current_user: dict = Depends(get_current_user)):
    session_id = f"{current_user['email']}_{uuid.uuid4().hex[:8]}"
    new_session = {
        "_id": session_id,
        "user_id": current_user['email'],
        "session_name": session_name,
        "created_at": datetime.utcnow().isoformat(),
        "messages": [],
        "total_tokens": 0
    }
    await db.chat_sessions.insert_one(new_session)
    return {"session_id": session_id, "session_name": session_name}

# Add a message to a chat session
@router.post("/chat/{session_id}/message")
async def add_message(session_id: str, role: str, content: str, tokens: int):
    message = {
        "role": role,
        "content": content,
        "timestamp": datetime.utcnow().isoformat(),
        "tokens": tokens
    }
    result = await db.chat_sessions.update_one(
        {"_id": session_id},
        {
            "$push": {"messages": message},
            "$inc": {"total_tokens": tokens}
        }
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Message added"}

# Get a full chat session
@router.get("/chat/{session_id}")
async def get_chat_session(session_id: str):
    session = await db.chat_sessions.find_one({"_id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

# List user chat sessions (with optional date filter)
@router.get("/chat/user/{user_id}")
async def list_user_sessions(user_id: str, start: Optional[str] = Query(None), end: Optional[str] = Query(None)):
    query = {"user_id": user_id}
    if start and end:
        query["created_at"] = {"$gte": start, "$lte": end}
    sessions = await db.chat_sessions.find(query).to_list(length=None)
    return [{"session_id": s["_id"], "name": s["session_name"], "created_at": s["created_at"], "total_tokens": s["total_tokens"]} for s in sessions]

# Rename a chat session
@router.put("/chat/{session_id}/rename")
async def rename_chat_session(session_id: str, new_name: str):
    result = await db.chat_sessions.update_one({"_id": session_id}, {"$set": {"session_name": new_name}})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Session renamed"}

# Delete a chat session
@router.delete("/chat/{session_id}")
async def delete_chat_session(session_id: str):
    result = await db.chat_sessions.delete_one({"_id": session_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Session deleted"}
