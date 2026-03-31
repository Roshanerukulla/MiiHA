"""
Symptom Checker API (Feature 3)

POST /api/v1/symptoms/check — analyse symptoms and return structured diagnosis hints
"""
from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, Depends, Request

from app.core.dependencies import get_current_user
from app.middleware.rate_limiter import limiter
from app.models.symptom import SymptomCheckRequest, SymptomCheckResponse
from app.services.symptom_service import check_symptoms
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/symptoms", tags=["symptoms"])

_executor = ThreadPoolExecutor(max_workers=2)


@router.post("/check", response_model=SymptomCheckResponse)
@limiter.limit("5/minute")
async def symptom_check(
    http_request: Request,
    request: SymptomCheckRequest,
    user: dict = Depends(get_current_user),
) -> SymptomCheckResponse:
    """
    Analyse the provided symptoms and return possible conditions,
    urgency level, and recommended next steps.
    """
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        _executor,
        lambda: check_symptoms(
            symptoms=request.symptoms,
            duration_days=request.duration_days,
            severity=request.severity,
            age=request.age,
            gender=request.gender,
        ),
    )
    return SymptomCheckResponse(**result)
