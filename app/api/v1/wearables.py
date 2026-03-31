"""
Wearable Integration API (Feature 15)

POST /api/v1/wearables/sync            — sync health metrics from a wearable source
GET  /api/v1/wearables/metrics         — retrieve metrics (filtered by type/days)
GET  /api/v1/wearables/summary         — 7-day averages for all tracked metrics
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_current_user
from app.models.wearable import MetricSummary, WearableSyncRequest, WearableSyncResponse
from app.services.wearable_service import get_metrics, get_metrics_summary, sync_metrics
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/wearables", tags=["wearables"])


@router.post("/sync", response_model=WearableSyncResponse)
async def sync_wearable_data(
    request: WearableSyncRequest,
    user: dict = Depends(get_current_user),
) -> WearableSyncResponse:
    """Sync health metrics from a wearable device or manual entry."""
    user_id = str(user["_id"])
    metrics_dicts = [m.model_dump() for m in request.metrics]
    inserted = await sync_metrics(
        user_id=user_id,
        source=request.source,
        metrics=metrics_dicts,
    )
    return WearableSyncResponse(inserted_count=inserted, source=request.source)


@router.get("/metrics")
async def get_user_metrics(
    type: Optional[str] = Query(default=None, description="Metric type to filter by"),
    days: int = Query(default=7, ge=1, le=365, description="Number of days to look back"),
    user: dict = Depends(get_current_user),
) -> List[dict]:
    """Retrieve health metrics for the authenticated user."""
    user_id = str(user["_id"])
    return await get_metrics(user_id=user_id, metric_type=type, days=days)


@router.get("/summary", response_model=List[MetricSummary])
async def wearable_summary(
    days: int = Query(default=7, ge=1, le=365, description="Number of days to summarise"),
    user: dict = Depends(get_current_user),
) -> List[MetricSummary]:
    """Return average values for all tracked metrics over the specified period."""
    user_id = str(user["_id"])
    summaries = await get_metrics_summary(user_id=user_id, days=days)
    return [MetricSummary(**s) for s in summaries]
