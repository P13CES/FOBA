"""Idempotent webhook ingestion backed by event_logs.

Every inbound event is inserted once, keyed by (source, event_id). A redelivery
from Square/Shopify hits the unique constraint and returns the existing row
instead of double-processing.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import EventLog

RECEIVED = "received"
PROCESSED = "processed"
FAILED = "failed"


async def ingest_event(
    db: AsyncSession,
    *,
    source: str,
    event_id: str,
    event_type: str,
    payload: dict,
) -> tuple[EventLog, bool]:
    """Insert the event. Returns (row, is_duplicate)."""
    log = EventLog(
        source=source, event_id=event_id, event_type=event_type, payload=payload
    )
    db.add(log)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        existing = (
            await db.execute(
                select(EventLog).where(
                    EventLog.source == source, EventLog.event_id == event_id
                )
            )
        ).scalar_one_or_none()
        if existing is None:
            raise  # not a duplicate key conflict; surface the real error
        return existing, True
    return log, False


async def mark_processed(db: AsyncSession, log: EventLog) -> None:
    log.status = PROCESSED
    log.processed_at = datetime.now(timezone.utc)
    await db.commit()


async def mark_failed(db: AsyncSession, log: EventLog, error: str) -> None:
    log.status = FAILED
    log.error = error
    log.processed_at = datetime.now(timezone.utc)
    await db.commit()
