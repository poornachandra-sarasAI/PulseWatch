"""Database operations for PulseWatch monitors.

This module is intentionally independent of FastAPI routes and the scheduler.
It owns the application-level rules for creating and retrieving monitor rows.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.check_result import CheckResult
from app.models.monitor import Monitor
from app.schemas.check_result import CheckResultCreate, CheckStatus
from app.schemas.monitor import MonitorCreate


class DuplicateMonitorURL(ValueError):
    """Raised when a monitor already exists for the requested URL."""


def create_monitor(db: Session, monitor_input: MonitorCreate) -> Monitor:
    """Persist a new monitor and schedule its first check immediately.

    An immediate first run gives the user feedback as soon as a monitor is
    created instead of making them wait one complete monitoring interval.
    """

    existing_monitor_id = db.scalar(
        select(Monitor.id).where(Monitor.url == monitor_input.url).limit(1)
    )
    if existing_monitor_id is not None:
        raise DuplicateMonitorURL("A monitor already exists for this URL")

    now = datetime.now(timezone.utc)
    monitor = Monitor(
        name=monitor_input.name,
        url=monitor_input.url,
        interval_seconds=monitor_input.interval_seconds,
        timeout_seconds=monitor_input.timeout_seconds,
        expected_status_codes=monitor_input.expected_status_codes,
        is_active=True,
        current_status="UNKNOWN",
        consecutive_failures=0,
        next_run_at=now,
        created_at=now,
        updated_at=now,
    )
    db.add(monitor)

    try:
        db.commit()
        db.refresh(monitor)
    except IntegrityError as error:
        db.rollback()
        # The database constraint also protects against two concurrent creates.
        raise DuplicateMonitorURL("A monitor already exists for this URL") from error
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


def pause_monitor(db: Session, monitor_id: UUID) -> Monitor | None:
    """Pause a monitor so later scheduler cycles no longer select it."""

    monitor = db.get(Monitor, monitor_id)
    if monitor is None:
        return None

    monitor.is_active = False
    try:
        db.commit()
        db.refresh(monitor)
    except SQLAlchemyError:
        db.rollback()
        raise

    return monitor


def delete_monitor(db: Session, monitor_id: UUID) -> bool:
    """Delete a monitor and its check history through the foreign-key cascade."""

    monitor = db.get(Monitor, monitor_id)
    if monitor is None:
        return False

    db.delete(monitor)
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise

    return True


def list_due_monitors(
    db: Session, *, now: datetime, limit: int = 100
) -> list[Monitor]:
    """Return the next batch of active monitors whose scheduled time has arrived.

    V0 assumes one scheduler process. A future multi-scheduler design will add
    row claiming or queue-based dispatch before this query is used concurrently.
    The comparison uses the naive UTC timestamp to support both PostgreSQL
    (timezone-aware) and SQLite test databases (naive).
    """

    # SQLite stores datetimes without timezone.  Strip the tz-info from *now*
    # so the comparison is consistently naive-vs-naive on SQLite and
    # aware-vs-aware on PostgreSQL (which preserves the timezone column).
    now_utc = now.replace(tzinfo=None) if now.tzinfo is not None else now

    statement = (
        select(Monitor)
        .where(Monitor.is_active.is_(True), Monitor.next_run_at <= now_utc)
        .order_by(Monitor.next_run_at)
        .limit(limit)
    )
    return list(db.scalars(statement))


def record_check_result(
    db: Session,
    *,
    monitor_id: UUID,
    result: CheckResultCreate,
    next_run_at: datetime,
) -> CheckResult | None:
    """Atomically save one check and update its monitor's current state."""

    monitor = db.get(Monitor, monitor_id)
    if monitor is None:
        return None

    check_result = CheckResult(
        monitor_id=monitor_id,
        checked_at=result.checked_at,
        status=result.status.value,
        http_status_code=result.http_status_code,
        latency_ms=result.latency_ms,
        error_type=result.error_type.value if result.error_type else None,
        error_message=result.error_message,
        created_at=datetime.now(timezone.utc),
    )
    monitor.last_checked_at = result.checked_at
    monitor.next_run_at = next_run_at

    if result.status == CheckStatus.SUCCESS:
        monitor.current_status = "UP"
        monitor.consecutive_failures = 0
    else:
        monitor.current_status = "DOWN"
        monitor.consecutive_failures += 1

    db.add(check_result)
    try:
        db.commit()
        db.refresh(check_result)
    except SQLAlchemyError:
        db.rollback()
        raise

    return check_result


def list_check_results(
    db: Session,
    monitor_id: UUID,
    *,
    limit: int = 50,
    before: datetime | None = None,
) -> list[CheckResult]:
    """Return check results for a monitor, newest-first, with cursor pagination.

    Uses the existing (monitor_id, checked_at) composite index for efficiency.
    Pass *before* (an ISO-8601 UTC timestamp) to fetch results older than that time.
    """

    statement = (
        select(CheckResult)
        .where(CheckResult.monitor_id == monitor_id)
        .order_by(CheckResult.checked_at.desc())
        .limit(limit)
    )
    if before is not None:
        statement = statement.where(CheckResult.checked_at < before)

    return list(db.scalars(statement))


def get_monitor_summary(
    db: Session,
    monitor_id: UUID,
    *,
    window_hours: int = 24,
) -> dict:
    """Return aggregate uptime statistics for a monitor over a time window.

    Returns null metrics rather than dividing by zero when the monitor has no
    results in the requested window.
    """

    since = datetime.now(timezone.utc) - timedelta(hours=window_hours)

    total_checks: int = db.scalar(
        select(func.count()).where(
            CheckResult.monitor_id == monitor_id,
            CheckResult.checked_at >= since,
        )
    ) or 0

    successful_checks: int = db.scalar(
        select(func.count()).where(
            CheckResult.monitor_id == monitor_id,
            CheckResult.checked_at >= since,
            CheckResult.status == "SUCCESS",
        )
    ) or 0

    avg_latency_ms: float | None = db.scalar(
        select(func.avg(CheckResult.latency_ms)).where(
            CheckResult.monitor_id == monitor_id,
            CheckResult.checked_at >= since,
            CheckResult.status == "SUCCESS",
        )
    )

    latest_result: CheckResult | None = db.scalar(
        select(CheckResult)
        .where(CheckResult.monitor_id == monitor_id)
        .order_by(CheckResult.checked_at.desc())
        .limit(1)
    )

    uptime_pct: float | None = None
    if total_checks > 0:
        uptime_pct = round((successful_checks / total_checks) * 100, 2)

    return {
        "window_hours": window_hours,
        "total_checks": total_checks,
        "successful_checks": successful_checks,
        "uptime_pct": uptime_pct,
        "avg_latency_ms": float(avg_latency_ms) if avg_latency_ms is not None else None,
        "latest_result": latest_result,
    }
