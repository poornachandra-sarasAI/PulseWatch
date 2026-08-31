"""Single-process, time-based scheduler for PulseWatch v0."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from time import sleep
from uuid import UUID

from app.db.session import SessionLocal
from app.schemas.monitor import MonitorConfig
from app.services.check_runner import run_check
from app.services.monitor_service import list_due_monitors, record_check_result


logger = logging.getLogger(__name__)
DEFAULT_POLL_INTERVAL_SECONDS = 5.0
DEFAULT_BATCH_SIZE = 100


@dataclass(frozen=True)
class ScheduledMonitor:
    """A monitor snapshot that can be checked after its database session closes."""

    monitor_id: UUID
    config: MonitorConfig
    scheduled_for: datetime
    interval_seconds: int


def run_scheduled_checks(
    *, now: datetime | None = None, batch_size: int = DEFAULT_BATCH_SIZE
) -> int:
    """Run one polling cycle and return the number of checks attempted."""

    poll_time = now or datetime.now(timezone.utc)
    due_monitors = _load_due_monitors(poll_time, batch_size)

    for scheduled_monitor in due_monitors:
        _run_and_record(scheduled_monitor)

    return len(due_monitors)


def run_forever(*, poll_interval_seconds: float = DEFAULT_POLL_INTERVAL_SECONDS) -> None:
    """Run scheduler cycles until the process is stopped."""

    if poll_interval_seconds <= 0:
        raise ValueError("poll_interval_seconds must be positive")

    logger.info("PulseWatch scheduler started; polling every %s seconds", poll_interval_seconds)
    while True:
        try:
            attempted_checks = run_scheduled_checks()
            if attempted_checks:
                logger.info("Completed %s scheduled check(s)", attempted_checks)
        except Exception:
            logger.exception("Scheduler cycle failed")

        sleep(poll_interval_seconds)


def _load_due_monitors(now: datetime, batch_size: int) -> list[ScheduledMonitor]:
    with SessionLocal() as db:
        monitors = list_due_monitors(db, now=now, limit=batch_size)
        return [
            ScheduledMonitor(
                monitor_id=monitor.id,
                config=MonitorConfig(
                    monitor_id=monitor.id,
                    url=monitor.url,
                    timeout_seconds=monitor.timeout_seconds,
                    expected_status_codes=monitor.expected_status_codes,
                ),
                # SQLite returns naive datetimes; ensure UTC-aware for comparisons.
                scheduled_for=(
                    monitor.next_run_at.replace(tzinfo=timezone.utc)
                    if monitor.next_run_at.tzinfo is None
                    else monitor.next_run_at
                ),
                interval_seconds=monitor.interval_seconds,
            )
            for monitor in monitors
        ]


def _run_and_record(scheduled_monitor: ScheduledMonitor) -> None:
    result = run_check(scheduled_monitor.config)
    completed_at = datetime.now(timezone.utc)
    next_run_at = _next_run_after(
        scheduled_for=scheduled_monitor.scheduled_for,
        interval_seconds=scheduled_monitor.interval_seconds,
        completed_at=completed_at,
    )

    try:
        with SessionLocal() as db:
            persisted_result = record_check_result(
                db,
                monitor_id=scheduled_monitor.monitor_id,
                result=result,
                next_run_at=next_run_at,
            )
            if persisted_result is None:
                logger.warning(
                    "Monitor %s was deleted before its result could be saved",
                    scheduled_monitor.monitor_id,
                )
    except Exception:
        logger.exception("Could not save check result for monitor %s", scheduled_monitor.monitor_id)


def _next_run_after(
    *, scheduled_for: datetime, interval_seconds: int, completed_at: datetime
) -> datetime:
    """Return the first future scheduled time, skipping missed intervals.

    Basing this on the original scheduled time prevents slow checks from
    permanently drifting later with every cycle.
    """

    next_run_at = scheduled_for + timedelta(seconds=interval_seconds)
    while next_run_at <= completed_at:
        next_run_at += timedelta(seconds=interval_seconds)
    return next_run_at
