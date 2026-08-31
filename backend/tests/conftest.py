"""Shared pytest fixtures for PulseWatch tests.

All tests run against in-memory SQLite.  The Monitor and CheckResult models
use PostgreSQL-specific constructs that we patch before DDL:
  - ARRAY(SMALLINT)  →  JSON
  - server_default=text("now()") → None  (ORM inserts datetimes in Python)
  - onupdate=func.now()  →  None
  - partial index (WHERE is_active = true) → dropped for SQLite compatibility
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import JSON, Index, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.check_result import CheckResult
from app.models.monitor import Monitor


# ── SQLite compatibility patch ────────────────────────────────────────────────

def _patch_models_for_sqlite() -> None:
    """Make every PostgreSQL-specific column and index SQLite-compatible.

    Sets server_default=None and onupdate=None so the ORM never tries to call
    PostgreSQL functions.  Removes the partial index which uses PostgreSQL DDL.
    """
    # Monitor timestamp columns
    Monitor.__table__.c.expected_status_codes.type = JSON()
    Monitor.__table__.c.expected_status_codes.server_default = None
    Monitor.__table__.c.is_active.server_default = None
    Monitor.__table__.c.current_status.server_default = None
    Monitor.__table__.c.consecutive_failures.server_default = None
    Monitor.__table__.c.created_at.server_default = None
    Monitor.__table__.c.updated_at.server_default = None
    Monitor.__table__.c.updated_at.onupdate = None

    # CheckResult timestamp column
    CheckResult.__table__.c.created_at.server_default = None

    # Remove the PostgreSQL partial index (WHERE is_active = true) from the
    # table's index list so SQLite doesn't choke on it.
    indexes_to_remove = [
        idx for idx in Monitor.__table__.indexes
        if idx.name == "ix_monitors_active_next_run"
    ]
    for idx in indexes_to_remove:
        Monitor.__table__.indexes.discard(idx)


# ── Engine / session fixtures ─────────────────────────────────────────────────

@pytest.fixture(scope="function")
def engine():
    """Fresh in-memory SQLite engine with all tables created."""

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
def db_session(engine):
    """Provide one SQLAlchemy session bound to the test engine."""

    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(engine):
    """FastAPI TestClient whose DB dependency is redirected to the test engine."""

    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()
