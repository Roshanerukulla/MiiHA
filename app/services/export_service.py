"""
Health Report Export Service (Feature 8)

Generates PDF and CSV exports for authenticated users.
"""
from __future__ import annotations

import csv
import io
from datetime import datetime, timedelta
from typing import Optional

from bson import ObjectId

from app.db.mongodb import db
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def _get_query_history(user_id: str, days: int = 30) -> list[dict]:
    """Retrieve query_history for the last `days` days."""
    since = datetime.utcnow() - timedelta(days=days)
    cursor = db.query_history.find(
        {"user_id": user_id, "timestamp": {"$gte": since}}
    ).sort("timestamp", -1)
    docs = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        docs.append(doc)
    return docs


async def _get_reminders(user_id: str) -> list[dict]:
    cursor = db.reminders.find({"user_id": user_id, "active": True})
    docs = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        docs.append(doc)
    return docs


async def generate_pdf_report(user: dict) -> bytes:
    """
    Generate a PDF health report for the user using reportlab.

    Returns raw PDF bytes.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )
        from reportlab.lib import colors

        user_id = str(user.get("_id", ""))
        queries = await _get_query_history(user_id, days=30)
        reminders = await _get_reminders(user_id)

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2 * cm)
        styles = getSampleStyleSheet()
        elements = []

        title_style = ParagraphStyle(
            "Title",
            parent=styles["Heading1"],
            fontSize=18,
            spaceAfter=12,
        )
        heading_style = ParagraphStyle(
            "Heading",
            parent=styles["Heading2"],
            fontSize=14,
            spaceAfter=8,
        )
        normal_style = styles["Normal"]

        # --- Title ---
        elements.append(Paragraph("MIHA Health Report", title_style))
        elements.append(
            Paragraph(
                f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
                normal_style,
            )
        )
        elements.append(Spacer(1, 0.5 * cm))

        # --- User Profile ---
        elements.append(Paragraph("User Profile", heading_style))
        name = user.get("preferred_name") or user.get("first_name") or "N/A"
        profile_data = [
            ["Field", "Value"],
            ["Name", name],
            ["Email", user.get("email", "N/A")],
            ["Gender", str(user.get("gender", "N/A"))],
            ["Date of Birth", user.get("birthdate", "N/A")],
            ["Medications", ", ".join(user.get("medications") or []) or "None"],
        ]
        profile_table = Table(profile_data, colWidths=[5 * cm, 12 * cm])
        profile_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4A90D9")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F0F4FF")]),
                    ("PADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        elements.append(profile_table)
        elements.append(Spacer(1, 0.5 * cm))

        # --- Reminders ---
        elements.append(Paragraph("Active Medication Reminders", heading_style))
        if reminders:
            reminder_data = [["Medication", "Time", "Frequency", "Notes"]]
            for r in reminders:
                reminder_data.append(
                    [r.get("medication", ""), r.get("time", ""), r.get("frequency", ""), r.get("notes", "")]
                )
            r_table = Table(reminder_data, colWidths=[5 * cm, 3 * cm, 4 * cm, 5 * cm])
            r_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4A90D9")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F0F4FF")]),
                        ("PADDING", (0, 0), (-1, -1), 6),
                    ]
                )
            )
            elements.append(r_table)
        else:
            elements.append(Paragraph("No active reminders.", normal_style))
        elements.append(Spacer(1, 0.5 * cm))

        # --- Query History ---
        elements.append(Paragraph("Recent Queries (Last 30 Days)", heading_style))
        if queries:
            for q in queries[:20]:  # cap at 20 to avoid huge PDFs
                ts = q.get("timestamp")
                ts_str = ts.strftime("%Y-%m-%d %H:%M") if isinstance(ts, datetime) else str(ts)
                elements.append(
                    Paragraph(f"<b>{ts_str}</b> — {q.get('query', '')}", normal_style)
                )
                answer_preview = (q.get("answer") or "")[:200]
                if len(q.get("answer", "")) > 200:
                    answer_preview += "..."
                elements.append(Paragraph(answer_preview, normal_style))
                elements.append(Spacer(1, 0.2 * cm))
        else:
            elements.append(Paragraph("No query history in the last 30 days.", normal_style))

        doc.build(elements)
        buffer.seek(0)
        return buffer.read()

    except Exception as exc:
        logger.error("PDF generation failed: %s", exc)
        raise


async def generate_csv_report(user: dict) -> str:
    """
    Generate a CSV export of the user's query history.

    Returns CSV content as a string.
    """
    try:
        user_id = str(user.get("_id", ""))
        queries = await _get_query_history(user_id, days=30)

        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)
        writer.writerow(["date", "query", "answer"])

        for q in queries:
            ts = q.get("timestamp")
            date_str = ts.strftime("%Y-%m-%d %H:%M:%S") if isinstance(ts, datetime) else str(ts)
            writer.writerow([date_str, q.get("query", ""), q.get("answer", "")])

        return output.getvalue()

    except Exception as exc:
        logger.error("CSV generation failed: %s", exc)
        raise
