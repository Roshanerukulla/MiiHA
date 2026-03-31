"""
Wearable Integration Service (Feature 15)

Stores health metrics from wearables and computes summaries.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from app.db.mongodb import db
from app.utils.logger import get_logger

logger = get_logger(__name__)

COLLECTION = "health_metrics"


async def sync_metrics(
    user_id: str,
    source: str,
    metrics: list[dict],
) -> int:
    """
    Insert health metrics for a user. Returns number of inserted documents.
    """
    try:
        if not metrics:
            return 0
        docs = []
        for m in metrics:
            docs.append(
                {
                    "user_id": user_id,
                    "source": source,
                    "type": m["type"],
                    "value": m["value"],
                    "unit": m["unit"],
                    "timestamp": m.get("timestamp", datetime.utcnow().isoformat()),
                    "recorded_at": datetime.utcnow(),
                }
            )
        result = await db[COLLECTION].insert_many(docs)
        logger.info("Inserted %d health metrics for user %s", len(result.inserted_ids), user_id)
        return len(result.inserted_ids)
    except Exception as exc:
        logger.error("Failed to sync metrics: %s", exc)
        raise


async def get_metrics(
    user_id: str,
    metric_type: Optional[str] = None,
    days: int = 7,
) -> list[dict]:
    """Retrieve user metrics filtered by type and date range."""
    try:
        since = datetime.utcnow() - timedelta(days=days)
        query: dict = {"user_id": user_id, "recorded_at": {"$gte": since}}
        if metric_type:
            query["type"] = metric_type
        cursor = db[COLLECTION].find(query).sort("recorded_at", -1)
        docs = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            docs.append(doc)
        return docs
    except Exception as exc:
        logger.error("Failed to retrieve metrics: %s", exc)
        return []


async def get_metrics_summary(user_id: str, days: int = 7) -> list[dict]:
    """Compute 7-day averages for all tracked metric types."""
    try:
        since = datetime.utcnow() - timedelta(days=days)
        pipeline = [
            {
                "$match": {
                    "user_id": user_id,
                    "recorded_at": {"$gte": since},
                }
            },
            {
                "$group": {
                    "_id": {"type": "$type", "unit": "$unit"},
                    "avg_value": {"$avg": "$value"},
                    "data_points": {"$sum": 1},
                }
            },
            {"$sort": {"_id.type": 1}},
        ]
        cursor = db[COLLECTION].aggregate(pipeline)
        summaries = []
        async for doc in cursor:
            summaries.append(
                {
                    "metric_type": doc["_id"]["type"],
                    "avg_value": round(doc["avg_value"], 2),
                    "unit": doc["_id"]["unit"],
                    "data_points": doc["data_points"],
                    "days": days,
                }
            )
        return summaries
    except Exception as exc:
        logger.error("Failed to compute metrics summary: %s", exc)
        return []


async def get_recent_metrics_for_profile(user_id: str, days: int = 7) -> dict:
    """
    Return a flat dict of metric_type -> avg_value for use in the RAG user profile.
    """
    summaries = await get_metrics_summary(user_id, days=days)
    return {
        f"{s['metric_type']} ({s['unit']})": s["avg_value"]
        for s in summaries
    }
