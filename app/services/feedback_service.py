"""
Feedback Loop Service (Feature 11)

Stores user feedback on query responses and aggregates stats.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from bson import ObjectId

from app.db.mongodb import db
from app.utils.logger import get_logger

logger = get_logger(__name__)

COLLECTION = "feedback"


async def submit_feedback(
    user_id: str,
    query_id: str,
    rating: int,
    comment: str,
) -> dict:
    """Store feedback for a query. Returns the inserted document."""
    try:
        doc = {
            "user_id": user_id,
            "query_id": query_id,
            "rating": rating,
            "comment": comment,
            "timestamp": datetime.utcnow(),
        }
        result = await db[COLLECTION].insert_one(doc)
        doc["_id"] = str(result.inserted_id)

        # Also update the query_history document with the rating
        try:
            await db.query_history.update_one(
                {"_id": ObjectId(query_id)},
                {"$set": {"rating": rating}},
            )
        except Exception:
            pass  # Non-critical

        return doc
    except Exception as exc:
        logger.error("Failed to submit feedback: %s", exc)
        raise


async def get_feedback_stats() -> dict:
    """Aggregate feedback stats across all users."""
    try:
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "avg_rating": {"$avg": "$rating"},
                    "total_count": {"$sum": 1},
                    "r1": {"$sum": {"$cond": [{"$eq": ["$rating", 1]}, 1, 0]}},
                    "r2": {"$sum": {"$cond": [{"$eq": ["$rating", 2]}, 1, 0]}},
                    "r3": {"$sum": {"$cond": [{"$eq": ["$rating", 3]}, 1, 0]}},
                    "r4": {"$sum": {"$cond": [{"$eq": ["$rating", 4]}, 1, 0]}},
                    "r5": {"$sum": {"$cond": [{"$eq": ["$rating", 5]}, 1, 0]}},
                }
            }
        ]
        cursor = db[COLLECTION].aggregate(pipeline)
        results = await cursor.to_list(length=1)
        if not results:
            return {
                "avg_rating": 0.0,
                "total_count": 0,
                "rating_distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
            }
        r = results[0]
        return {
            "avg_rating": round(r.get("avg_rating") or 0.0, 2),
            "total_count": r.get("total_count", 0),
            "rating_distribution": {
                1: r.get("r1", 0),
                2: r.get("r2", 0),
                3: r.get("r3", 0),
                4: r.get("r4", 0),
                5: r.get("r5", 0),
            },
        }
    except Exception as exc:
        logger.error("Failed to aggregate feedback stats: %s", exc)
        return {"avg_rating": 0.0, "total_count": 0, "rating_distribution": {}}
