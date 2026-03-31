"""
Streaming Responses API (Feature 6)

POST /api/v1/query/stream — stream RAG answer tokens via Server-Sent Events
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.core.dependencies import get_current_user
from app.middleware.rate_limiter import limiter
from app.services.query_service import _query_rag_stream_sync
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["stream"])


class StreamQueryRequest(BaseModel):
    query: str
    top_k: int = 15


@router.post("/query/stream")
@limiter.limit("5/minute")
async def stream_query(
    request: Request,
    query_request: StreamQueryRequest,
    user: dict = Depends(get_current_user),
) -> StreamingResponse:
    """
    Stream RAG answer tokens as Server-Sent Events.

    Each event: `data: <token>\\n\\n`
    Final event: `data: [DONE]\\n\\n`
    """
    user_profile = dict(user)

    # Build generator
    def event_generator():
        yield from _query_rag_stream_sync(
            query=query_request.query,
            top_k=query_request.top_k,
            history=None,
            user_profile=user_profile,
        )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
