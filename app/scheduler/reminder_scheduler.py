"""
Medication Reminder Scheduler (Feature 7)

Uses APScheduler AsyncIOScheduler to check for due reminders every minute.
When a reminder is due it is logged and optionally sent via email (aiosmtplib).
"""
from __future__ import annotations

from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

scheduler = AsyncIOScheduler()


async def _send_reminder_email(
    to_email: str,
    medication: str,
    time_str: str,
    notes: str,
) -> None:
    """Send a reminder email via aiosmtplib if SMTP is configured."""
    if not settings.smtp_host:
        return
    try:
        import aiosmtplib
        from email.mime.text import MIMEText

        subject = f"MIHA Medication Reminder: {medication}"
        body = (
            f"Hi,\n\n"
            f"This is your scheduled reminder to take: {medication}\n"
            f"Scheduled time: {time_str}\n"
        )
        if notes:
            body += f"Notes: {notes}\n"
        body += "\n— MIHA Health Assistant"

        message = MIMEText(body)
        message["From"] = settings.smtp_user or "miha@health.app"
        message["To"] = to_email
        message["Subject"] = subject

        await aiosmtplib.send(
            message,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_user,
            password=settings.smtp_password,
            start_tls=True,
        )
        logger.info("Reminder email sent to %s for %s", to_email, medication)
    except Exception as exc:
        logger.warning("Failed to send reminder email to %s: %s", to_email, exc)


async def _check_and_fire_reminders() -> None:
    """
    Called every minute by the scheduler.

    Fetches reminders due at the current HH:MM and processes them.
    """
    try:
        from app.db.mongodb import db
        from app.services.reminder_service import get_due_reminders

        now = datetime.now()
        current_hhmm = now.strftime("%H:%M")
        due = await get_due_reminders(current_hhmm)

        if not due:
            return

        logger.info("Found %d due reminder(s) at %s", len(due), current_hhmm)

        for reminder in due:
            user_id = reminder.get("user_id")
            medication = reminder.get("medication", "Unknown")
            time_str = reminder.get("time", current_hhmm)
            notes = reminder.get("notes", "")
            frequency = reminder.get("frequency", "daily")

            logger.info(
                "Reminder due — user=%s medication=%s frequency=%s",
                user_id,
                medication,
                frequency,
            )

            # Attempt email if user has an email address
            try:
                user_doc = await db.users.find_one({"_id": __import__("bson").ObjectId(user_id)})
                if user_doc and user_doc.get("email"):
                    await _send_reminder_email(
                        to_email=user_doc["email"],
                        medication=medication,
                        time_str=time_str,
                        notes=notes,
                    )
            except Exception as exc:
                logger.warning("Could not look up user for reminder: %s", exc)

    except Exception as exc:
        logger.error("Reminder check failed: %s", exc)


def start_scheduler() -> None:
    """Add the reminder job and start the scheduler."""
    scheduler.add_job(
        _check_and_fire_reminders,
        trigger="interval",
        minutes=1,
        id="reminder_check",
        replace_existing=True,
        misfire_grace_time=30,
    )
    scheduler.start()
    logger.info("Reminder scheduler started")


def stop_scheduler() -> None:
    """Gracefully shut down the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Reminder scheduler stopped")
