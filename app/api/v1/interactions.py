"""
Drug Interaction Checker API (Feature 4)

POST /api/v1/interactions/check          — check arbitrary medication list
GET  /api/v1/interactions/my-medications — check authenticated user's saved medications
"""
from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.dependencies import get_current_user
from app.middleware.rate_limiter import limiter
from app.models.interaction import InteractionCheckRequest, InteractionCheckResponse
from app.services.interaction_service import check_interactions
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/interactions", tags=["interactions"])

_executor = ThreadPoolExecutor(max_workers=2)


@router.post("/check", response_model=InteractionCheckResponse)
@limiter.limit("5/minute")
async def interaction_check(
    http_request: Request,
    request: InteractionCheckRequest,
    user: dict = Depends(get_current_user),
) -> InteractionCheckResponse:
    """Check drug-drug interactions for the provided medication list."""
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        _executor,
        lambda: check_interactions(request.medications),
    )
    return InteractionCheckResponse(**result)


@router.get("/my-medications", response_model=InteractionCheckResponse)
async def my_medication_interactions(
    user: dict = Depends(get_current_user),
) -> InteractionCheckResponse:
    """Check interactions for the authenticated user's saved medication list."""
    medications = user.get("medications") or []
    if not medications:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No medications found in your profile. Please update your medications first.",
        )
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        _executor,
        lambda: check_interactions(medications),
    )
    return InteractionCheckResponse(**result)
