"""
Health Report Export API (Feature 8)

GET /api/v1/export/pdf — download PDF health report
GET /api/v1/export/csv — download CSV query history
"""
from __future__ import annotations

import io

from fastapi import APIRouter, Depends
from fastapi.responses import Response, StreamingResponse

from app.core.dependencies import get_current_user
from app.services.export_service import generate_csv_report, generate_pdf_report
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/export", tags=["export"])


@router.get("/pdf")
async def export_pdf(
    user: dict = Depends(get_current_user),
) -> Response:
    """Generate and download a PDF health report for the authenticated user."""
    pdf_bytes = await generate_pdf_report(user)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'attachment; filename="miha_health_report.pdf"',
            "Content-Length": str(len(pdf_bytes)),
        },
    )


@router.get("/csv")
async def export_csv(
    user: dict = Depends(get_current_user),
) -> StreamingResponse:
    """Export query history as a CSV file."""
    csv_content = await generate_csv_report(user)

    def csv_generator():
        yield csv_content

    return StreamingResponse(
        csv_generator(),
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="miha_query_history.csv"',
        },
    )
