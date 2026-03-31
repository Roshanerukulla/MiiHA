"""
Admin Dashboard API (Feature 12)

All routes require is_admin=True on the user document.

GET /api/v1/admin/stats            — aggregate system statistics
GET /api/v1/admin/users            — paginated user list
GET /api/v1/admin/logs             — recent query log entries
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_admin_user
from app.db.mongodb import db
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats")
async def admin_stats(admin: dict = Depends(get_admin_user)) -> dict:
    """Return aggregate statistics about users, queries, and feedback."""
    try:
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        total_users = await db.users.count_documents({})
        total_queries = await db.query_history.count_documents({})
        queries_today = await db.query_history.count_documents(
            {"timestamp": {"$gte": today_start}}
        )

        # Average rating from feedback collection
        pipeline_rating = [
            {"$group": {"_id": None, "avg": {"$avg": "$rating"}}}
        ]
        rating_result = await db.feedback.aggregate(pipeline_rating).to_list(1)
        avg_response_rating = round(rating_result[0]["avg"], 2) if rating_result else 0.0

        # Top 5 most common queries
        pipeline_top = [
            {"$group": {"_id": "$query", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 5},
        ]
        top_raw = await db.query_history.aggregate(pipeline_top).to_list(5)
        top_queries = [{"query": r["_id"], "count": r["count"]} for r in top_raw]

        # Active users today (users who made at least one query today)
        pipeline_active = [
            {"$match": {"timestamp": {"$gte": today_start}}},
            {"$group": {"_id": "$user_id"}},
            {"$count": "active_users_today"},
        ]
        active_result = await db.query_history.aggregate(pipeline_active).to_list(1)
        active_users_today = active_result[0]["active_users_today"] if active_result else 0

        return {
            "total_users": total_users,
            "total_queries": total_queries,
            "queries_today": queries_today,
            "avg_response_rating": avg_response_rating,
            "top_queries": top_queries,
            "active_users_today": active_users_today,
        }
    except Exception as exc:
        logger.error("Admin stats failed: %s", exc)
        return {
            "total_users": 0,
            "total_queries": 0,
            "queries_today": 0,
            "avg_response_rating": 0.0,
            "top_queries": [],
            "active_users_today": 0,
        }


@router.get("/users")
async def admin_users(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    admin: dict = Depends(get_admin_user),
) -> dict:
    """Return a paginated list of all registered users."""
    try:
        skip = (page - 1) * per_page
        total = await db.users.count_documents({})
        cursor = db.users.find(
            {},
            {"hashed_password": 0}  # exclude password hash
        ).skip(skip).limit(per_page)
        users = []
        async for user in cursor:
            user["_id"] = str(user["_id"])
            users.append(user)
        return {
            "page": page,
            "per_page": per_page,
            "total": total,
            "users": users,
        }
    except Exception as exc:
        logger.error("Admin users list failed: %s", exc)
        return {"page": page, "per_page": per_page, "total": 0, "users": []}


@router.get("/logs")
async def admin_logs(
    limit: int = Query(default=100, ge=1, le=1000),
    admin: dict = Depends(get_admin_user),
) -> dict:
    """Return the most recent query log entries."""
    try:
        cursor = (
            db.query_history.find({})
            .sort("timestamp", -1)
            .limit(limit)
        )
        logs = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            logs.append(doc)
        return {"count": len(logs), "logs": logs}
    except Exception as exc:
        logger.error("Admin logs failed: %s", exc)
        return {"count": 0, "logs": []}
