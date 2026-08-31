"""Response schemas for the result-history and summary endpoints."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CheckResultRead(BaseModel):
    """One persisted check result returned by the REST API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    monitor_id: UUID
    checked_at: datetime
    status: str
    http_status_code: int | None
    latency_ms: float | None
    error_type: str | None
    error_message: str | None


class ResultHistoryPage(BaseModel):
    """Paginated result history for one monitor."""

    items: list[CheckResultRead]
    next_before: datetime | None


class LatestResult(BaseModel):
    """Minimal view of the most-recent check included in the summary."""

    model_config = ConfigDict(from_attributes=True)

    checked_at: datetime
    status: str
    http_status_code: int | None
    latency_ms: float | None
    error_type: str | None
    error_message: str | None


class MonitorSummary(BaseModel):
    """Aggregated uptime statistics for a monitor over a time window."""

    window_hours: int
    total_checks: int
    successful_checks: int
    uptime_pct: float | None
    avg_latency_ms: float | None
    latest_result: LatestResult | None
