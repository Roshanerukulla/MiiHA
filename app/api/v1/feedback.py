"""
Feedback Loop API (Feature 11)

POST /api/v1/feedback       — submit rating + comment for a query
GET  /api/v1/feedback/stats — admin-only aggregate stats
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_admin_user, get_current_user
from app.models.feedback import FeedbackCreate, FeedbackStats
from app.services.feedback_service import get_feedback_stats, submit_feedback
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_feedback(
    request: FeedbackCreate,
    user: dict = Depends(get_current_user),
) -> dict:
    """Submit a rating and optional comment for a previous query response."""
    user_id = str(user["_id"])
    doc = await submit_feedback(
        user_id=user_id,
        query_id=request.query_id,
        rating=request.rating,
        comment=request.comment or "",
    )
    return {"message": "Feedback submitted", "feedback_id": doc["_id"]}


@router.get("/stats", response_model=FeedbackStats)
async def feedback_stats(
    admin: dict = Depends(get_admin_user),
) -> FeedbackStats:
    """Return aggregate feedback statistics. Requires admin privileges."""
    stats = await get_feedback_stats()
    return FeedbackStats(**stats)
