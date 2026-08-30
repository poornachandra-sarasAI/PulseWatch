"""Database operations for PulseWatch monitors.

This module is intentionally independent of FastAPI routes and the scheduler.
It owns the application-level rules for creating and retrieving monitor rows.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.monitor import Monitor
from app.schemas.monitor import MonitorCreate


def create_monitor(db: Session, monitor_input: MonitorCreate) -> Monitor:
    """Persist a new monitor and schedule its first check immediately.

    An immediate first run gives the user feedback as soon as a monitor is
    created instead of making them wait one complete monitoring interval.
    """

    monitor = Monitor(
        name=monitor_input.name,
        url=monitor_input.url,
        interval_seconds=monitor_input.interval_seconds,
        timeout_seconds=monitor_input.timeout_seconds,
        expected_status_codes=monitor_input.expected_status_codes,
        next_run_at=datetime.now(timezone.utc),
    )
    db.add(monitor)

    try:
        db.commit()
        db.refresh(monitor)
    except SQLAlchemyError:
        db.rollback()
        raise

    return monitor


def get_monitor(db: Session, monitor_id: UUID) -> Monitor | None:
    """Return one monitor by ID, or ``None`` when it does not exist."""

    return db.get(Monitor, monitor_id)


def list_monitors(db: Session, *, include_inactive: bool = True) -> list[Monitor]:
    """Return monitors in newest-first order for the future dashboard."""

    statement = select(Monitor).order_by(Monitor.created_at.desc())
    if not include_inactive:
        statement = statement.where(Monitor.is_active.is_(True))

    return list(db.scalars(statement))
