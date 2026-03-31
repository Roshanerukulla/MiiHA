"""
Conversation Memory API (Feature 1)

POST /api/v1/chat          — send a message with session context
GET  /api/v1/chat/history  — retrieve conversation history
DELETE /api/v1/chat/history/{session_id} — clear a session
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_current_user
from app.models.chat import ChatRequest, ChatResponse, ConversationHistoryResponse
from app.services import chat_service
from app.services.query_service import query_rag
from app.services.wearable_service import get_recent_metrics_for_profile
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    user: dict = Depends(get_current_user),
) -> ChatResponse:
    """Send a message within a session; RAG context includes last 5 turns."""
    user_id = str(user["_id"])

    # Load last 5 turns as history
    history = await chat_service.get_recent_history(user_id, request.session_id)

    # Enrich user profile with recent wearable metrics
    user_profile = dict(user)
    try:
        recent_metrics = await get_recent_metrics_for_profile(user_id)
        if recent_metrics:
            user_profile["recent_metrics"] = recent_metrics
    except Exception as exc:
        logger.warning("Could not load wearable metrics for chat: %s", exc)

    # Run RAG
    result = await query_rag(
        query=request.message,
        history=history,
        user_profile=user_profile,
    )

    reply = result.get("answer", "")
    query_id = result.get("query_id")

    # Persist both turns
    await chat_service.append_turn(user_id, request.session_id, "user", request.message)
    await chat_service.append_turn(user_id, request.session_id, "assistant", reply)

    return ChatResponse(
        reply=reply,
        session_id=request.session_id,
        query_id=query_id,
        cached=result.get("cached", False),
        detected_language=result.get("detected_language"),
        translated=result.get("translated", False),
    )


@router.get("/history", response_model=ConversationHistoryResponse)
async def get_history(
    session_id: str,
    user: dict = Depends(get_current_user),
) -> ConversationHistoryResponse:
    """Retrieve full conversation history for a session."""
    user_id = str(user["_id"])
    doc = await chat_service.get_full_history(user_id, session_id)
    return ConversationHistoryResponse(
        session_id=session_id,
        user_id=user_id,
        turns=doc.get("turns", []),
    )


@router.delete("/history/{session_id}")
async def delete_history(
    session_id: str,
    user: dict = Depends(get_current_user),
) -> dict:
    """Clear all turns for a conversation session."""
    user_id = str(user["_id"])
    deleted = await chat_service.delete_session(user_id, session_id)
    if deleted == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    return {"message": f"Session '{session_id}' deleted successfully"}
