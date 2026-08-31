"""Database model for a configured HTTP monitor."""

from __future__ import annotations

from typing import TYPE_CHECKING

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, SMALLINT, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.check_result import CheckResult


class Monitor(Base):
    __tablename__ = "monitors"
    __table_args__ = (
        CheckConstraint("interval_seconds > 0", name="ck_monitors_interval_positive"),
        CheckConstraint("timeout_seconds > 0 AND timeout_seconds <= 60", name="ck_monitors_timeout_range"),
        CheckConstraint("consecutive_failures >= 0", name="ck_monitors_failures_nonnegative"),
        CheckConstraint(
            "current_status IN ('UNKNOWN', 'UP', 'DOWN')",
            name="ck_monitors_current_status",
        ),
        UniqueConstraint("url", name="uq_monitors_url"),
        Index(
            "ix_monitors_active_next_run",
            "next_run_at",
            postgresql_where=text("is_active = true"),
        ),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    interval_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    timeout_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=5.0)
    expected_status_codes: Mapped[list[int]] = mapped_column(
        ARRAY(SMALLINT),
        nullable=False,
        server_default=text("ARRAY[200]::smallint[]"),
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    current_status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'UNKNOWN'")
    )
    consecutive_failures: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_run_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
        onupdate=func.now(),
    )

    check_results: Mapped[list["CheckResult"]] = relationship(
        back_populates="monitor", cascade="all, delete-orphan"
    )
