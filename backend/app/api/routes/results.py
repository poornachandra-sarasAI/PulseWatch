"""REST endpoints for check-result history and uptime summaries."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.result_history import (
    CheckResultRead,
    LatestResult,
    MonitorSummary,
    ResultHistoryPage,
)
from app.services.monitor_service import (
    get_monitor,
    get_monitor_summary,
    list_check_results,
)

router = APIRouter(prefix="/api/monitors", tags=["results"])


@router.get("/{monitor_id}/results", response_model=ResultHistoryPage)
def list_results_endpoint(
    monitor_id: UUID,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    before: datetime | None = None,
    db: Session = Depends(get_db),
) -> ResultHistoryPage:
    """Return paginated check-result history for one monitor, newest-first.

    Use the *before* cursor (an ISO-8601 UTC timestamp from *next_before* in a
    prior response) to fetch the next page of older results.
    """

    if get_monitor(db, monitor_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Monitor not found")

    results = list_check_results(db, monitor_id, limit=limit, before=before)
    items = [CheckResultRead.model_validate(r) for r in results]

    next_before: datetime | None = None
    if len(results) == limit:
        # The oldest item in this page becomes the next cursor.
        next_before = results[-1].checked_at

    return ResultHistoryPage(items=items, next_before=next_before)


@router.get("/{monitor_id}/summary", response_model=MonitorSummary)
def get_summary_endpoint(
    monitor_id: UUID,
    window_hours: Annotated[int, Query(ge=1, le=168)] = 24,
    db: Session = Depends(get_db),
) -> MonitorSummary:
    """Return uptime and latency statistics for one monitor over a time window.

    Metrics are *null* rather than zero when the monitor has no history in the
    requested window, so callers can distinguish "no data" from "zero uptime".
    """

    if get_monitor(db, monitor_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Monitor not found")

    summary = get_monitor_summary(db, monitor_id, window_hours=window_hours)

    latest_result = None
    if summary["latest_result"] is not None:
        latest_result = LatestResult.model_validate(summary["latest_result"])

    return MonitorSummary(
        window_hours=summary["window_hours"],
        total_checks=summary["total_checks"],
        successful_checks=summary["successful_checks"],
        uptime_pct=summary["uptime_pct"],
        avg_latency_ms=summary["avg_latency_ms"],
        latest_result=latest_result,
    )
