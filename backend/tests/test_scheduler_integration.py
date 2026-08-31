"""Scheduler integration test.

Creates a monitor in the test database, starts a temporary HTTP server that
returns 200, runs one scheduler cycle, then verifies that:
 1. The monitor's ``current_status`` is updated to ``UP``.
 2. A ``CheckResult`` row is persisted in the database.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from pytest_httpserver import HTTPServer
from sqlalchemy import JSON, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import SessionLocal
from app.models.check_result import CheckResult
from app.models.monitor import Monitor
from app.scheduler.monitor_scheduler import run_scheduled_checks


# ── SQLite patch (same strategy as conftest.py) ───────────────────────────────

def _patch_models_for_sqlite() -> None:
    Monitor.__table__.c.expected_status_codes.type = JSON()
    Monitor.__table__.c.expected_status_codes.server_default = None
    Monitor.__table__.c.is_active.server_default = None
    Monitor.__table__.c.current_status.server_default = None
    Monitor.__table__.c.consecutive_failures.server_default = None
    Monitor.__table__.c.created_at.server_default = None
    Monitor.__table__.c.updated_at.server_default = None
    Monitor.__table__.c.updated_at.onupdate = None
    CheckResult.__table__.c.created_at.server_default = None
    # Remove the PostgreSQL partial index (WHERE is_active = true)
    indexes_to_remove = [
        idx for idx in Monitor.__table__.indexes
        if idx.name == "ix_monitors_active_next_run"
    ]
    for idx in indexes_to_remove:
        Monitor.__table__.indexes.discard(idx)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def integration_engine():
    """Fresh in-memory SQLite engine for the scheduler integration test."""

    _patch_models_for_sqlite()
    _engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(_engine)
    yield _engine
    _engine.dispose()


@pytest.fixture(scope="function")
def integration_session(integration_engine, monkeypatch):
    """Session factory redirected to the integration engine."""

    TestingSession = sessionmaker(
        bind=integration_engine, autoflush=False, autocommit=False
    )

    # Patch the SessionLocal used by the scheduler module so it uses our test DB.
    monkeypatch.setattr(
        "app.scheduler.monitor_scheduler.SessionLocal", TestingSession
    )

    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


# ── Test ──────────────────────────────────────────────────────────────────────

def test_scheduler_runs_check_and_persists_result(
    integration_session, httpserver: HTTPServer
):
    """Run one scheduler cycle and verify a check result is stored."""

    # Register a simple 200 OK handler on the test HTTP server.
    httpserver.expect_request("/probe").respond_with_data("OK", status=200)
    target_url = httpserver.url_for("/probe")

    now = datetime.now(timezone.utc)

    # Seed a monitor that is immediately due (next_run_at = now - 1 s).
    monitor = Monitor(
        name="Integration Monitor",
        url=target_url,
        interval_seconds=60,
        timeout_seconds=5.0,
        expected_status_codes=[200],
        is_active=True,
        current_status="UNKNOWN",
        consecutive_failures=0,
        next_run_at=now - timedelta(seconds=1),
        created_at=now,
        updated_at=now,
    )
    integration_session.add(monitor)
    integration_session.commit()
    integration_session.refresh(monitor)
    monitor_id = monitor.id

    # Run one scheduler cycle.
    attempted = run_scheduled_checks()
    assert attempted == 1

    # Reload the monitor and verify it's marked UP.
    integration_session.expire_all()
    updated_monitor = integration_session.get(Monitor, monitor_id)
    assert updated_monitor is not None
    assert updated_monitor.current_status == "UP"
    assert updated_monitor.last_checked_at is not None

    # Verify that a CheckResult was persisted.
    results = (
        integration_session.query(CheckResult)
        .filter_by(monitor_id=monitor_id)
        .all()
    )
    assert len(results) == 1
    assert results[0].status == "SUCCESS"
    assert results[0].http_status_code == 200
    assert results[0].latency_ms is not None
