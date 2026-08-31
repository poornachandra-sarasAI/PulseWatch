"""API integration tests for PulseWatch monitor and result-history endpoints.

All tests run against an in-memory SQLite database via the ``client`` fixture
defined in conftest.py — no PostgreSQL instance is required.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest

from app.models.check_result import CheckResult
from app.models.monitor import Monitor


# ── Helpers ──────────────────────────────────────────────────────────────────

MONITOR_PAYLOAD = {
    "name": "Test Monitor",
    "url": "https://example.com/health",
    "interval_seconds": 60,
    "timeout_seconds": 5.0,
    "expected_status_codes": [200],
}


def create_monitor(client, payload=None):
    """POST /api/monitors and return the JSON body."""
    return client.post("/api/monitors", json=payload or MONITOR_PAYLOAD)


def seed_results(db_session, monitor_id: str, count: int) -> list[CheckResult]:
    """Insert *count* SUCCESS results spaced 1 minute apart (newest first)."""
    results = []
    base = datetime.now(timezone.utc)
    mid = UUID(monitor_id)  # ensure UUID object for PG_UUID column
    for i in range(count):
        r = CheckResult(
            monitor_id=mid,
            checked_at=base - timedelta(minutes=i),
            status="SUCCESS",
            http_status_code=200,
            latency_ms=100.0 + i,
            created_at=base,
        )
        db_session.add(r)
        results.append(r)
    db_session.commit()
    for r in results:
        db_session.refresh(r)
    return results


# ── Monitor CRUD ──────────────────────────────────────────────────────────────

def test_create_monitor_returns_201(client):
    response = create_monitor(client)
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == MONITOR_PAYLOAD["name"]
    assert body["url"] == MONITOR_PAYLOAD["url"]
    assert "id" in body


def test_duplicate_url_returns_409(client):
    create_monitor(client)
    response = create_monitor(client)
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_list_monitors_returns_persisted_monitors(client):
    create_monitor(client)
    response = client.get("/api/monitors")
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 1
    assert items[0]["url"] == MONITOR_PAYLOAD["url"]


def test_get_existing_monitor_returns_200(client):
    created = create_monitor(client).json()
    response = client.get(f"/api/monitors/{created['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_unknown_monitor_returns_404(client):
    response = client.get(f"/api/monitors/{uuid.uuid4()}")
    assert response.status_code == 404


def test_pause_monitor_sets_is_active_false(client):
    created = create_monitor(client).json()
    assert created["is_active"] is True

    response = client.patch(f"/api/monitors/{created['id']}/pause")
    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_delete_monitor_returns_204(client, db_session):
    created = create_monitor(client).json()
    monitor_id = created["id"]

    # Seed some check results.
    seed_results(db_session, monitor_id, 3)
    assert db_session.query(CheckResult).filter_by(monitor_id=UUID(monitor_id)).count() == 3

    # Delete the monitor.
    response = client.delete(f"/api/monitors/{monitor_id}")
    assert response.status_code == 204

    # Monitor and its check history should be gone.
    response = client.get(f"/api/monitors/{monitor_id}")
    assert response.status_code == 404
    assert db_session.query(CheckResult).filter_by(monitor_id=UUID(monitor_id)).count() == 0


# ── Result history ────────────────────────────────────────────────────────────

def test_result_history_unknown_monitor_returns_404(client):
    response = client.get(f"/api/monitors/{uuid.uuid4()}/results")
    assert response.status_code == 404


def test_result_history_returns_newest_first(client, db_session):
    created = create_monitor(client).json()
    seed_results(db_session, created["id"], 5)

    response = client.get(f"/api/monitors/{created['id']}/results")
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 5
    # Verify descending order.
    timestamps = [item["checked_at"] for item in items]
    assert timestamps == sorted(timestamps, reverse=True)


def test_result_history_respects_limit(client, db_session):
    created = create_monitor(client).json()
    seed_results(db_session, created["id"], 10)

    response = client.get(f"/api/monitors/{created['id']}/results?limit=3")
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 3
    assert body["next_before"] is not None


def test_result_history_respects_before_cursor(client, db_session):
    created = create_monitor(client).json()
    results = seed_results(db_session, created["id"], 6)

    # The first call returns the 3 newest results.
    r1 = client.get(f"/api/monitors/{created['id']}/results?limit=3")
    assert r1.status_code == 200
    page1 = r1.json()
    assert len(page1["items"]) == 3
    cursor = page1["next_before"]
    assert cursor is not None

    # The second call with the cursor returns the next 3.
    r2 = client.get(f"/api/monitors/{created['id']}/results?limit=3&before={cursor}")
    assert r2.status_code == 200
    page2 = r2.json()
    assert len(page2["items"]) == 3

    # Pages must not overlap.
    ids_page1 = {item["id"] for item in page1["items"]}
    ids_page2 = {item["id"] for item in page2["items"]}
    assert ids_page1.isdisjoint(ids_page2)


def test_result_history_next_before_is_null_on_last_page(client, db_session):
    created = create_monitor(client).json()
    seed_results(db_session, created["id"], 2)

    response = client.get(f"/api/monitors/{created['id']}/results?limit=50")
    assert response.status_code == 200
    assert response.json()["next_before"] is None


# ── Summary ──────────────────────────────────────────────────────────────────

def test_summary_unknown_monitor_returns_404(client):
    response = client.get(f"/api/monitors/{uuid.uuid4()}/summary")
    assert response.status_code == 404


def test_summary_returns_null_metrics_for_empty_history(client):
    created = create_monitor(client).json()

    response = client.get(f"/api/monitors/{created['id']}/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["total_checks"] == 0
    assert body["uptime_pct"] is None
    assert body["avg_latency_ms"] is None
    assert body["latest_result"] is None


def test_summary_returns_correct_metrics(client, db_session):
    created = create_monitor(client).json()
    monitor_id = created["id"]

    # Add 4 SUCCESS + 1 FAILURE result within the last 24 h.
    base = datetime.now(timezone.utc)
    mid = UUID(monitor_id)
    for i in range(4):
        r = CheckResult(
            monitor_id=mid,
            checked_at=base - timedelta(minutes=i + 1),
            status="SUCCESS",
            http_status_code=200,
            latency_ms=100.0,
            created_at=base,
        )
        db_session.add(r)
    failure = CheckResult(
        monitor_id=mid,
        checked_at=base - timedelta(minutes=5),
        status="FAILURE",
        http_status_code=503,
        latency_ms=None,
        error_type="UNEXPECTED_STATUS",
        created_at=base,
    )
    db_session.add(failure)
    db_session.commit()

    response = client.get(f"/api/monitors/{monitor_id}/summary?window_hours=24")
    assert response.status_code == 200
    body = response.json()

    assert body["total_checks"] == 5
    assert body["successful_checks"] == 4
    assert body["uptime_pct"] == 80.0
    assert body["avg_latency_ms"] == 100.0
    assert body["latest_result"] is not None
