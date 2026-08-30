"""Create the initial monitoring tables.

Revision ID: 0001_initial_monitoring_schema
Revises:
Create Date: 2026-08-30
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0001_initial_monitoring_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "monitors",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("interval_seconds", sa.Integer(), nullable=False),
        sa.Column("timeout_seconds", sa.Float(), nullable=False),
        sa.Column(
            "expected_status_codes",
            postgresql.ARRAY(sa.SmallInteger()),
            server_default=sa.text("ARRAY[200]::smallint[]"),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "current_status",
            sa.String(length=20),
            server_default=sa.text("'UNKNOWN'"),
            nullable=False,
        ),
        sa.Column(
            "consecutive_failures",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("interval_seconds > 0", name="ck_monitors_interval_positive"),
        sa.CheckConstraint(
            "timeout_seconds > 0 AND timeout_seconds <= 60",
            name="ck_monitors_timeout_range",
        ),
        sa.CheckConstraint(
            "consecutive_failures >= 0", name="ck_monitors_failures_nonnegative"
        ),
        sa.CheckConstraint(
            "current_status IN ('UNKNOWN', 'UP', 'DOWN')",
            name="ck_monitors_current_status",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_monitors_active_next_run",
        "monitors",
        ["next_run_at"],
        postgresql_where=sa.text("is_active = true"),
    )

    op.create_table(
        "check_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("monitor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("http_status_code", sa.SmallInteger(), nullable=True),
        sa.Column("latency_ms", sa.Float(), nullable=True),
        sa.Column("error_type", sa.String(length=50), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("status IN ('SUCCESS', 'FAILURE')", name="ck_check_results_status"),
        sa.CheckConstraint(
            "http_status_code IS NULL OR http_status_code BETWEEN 100 AND 599",
            name="ck_check_results_http_status_range",
        ),
        sa.CheckConstraint(
            "latency_ms IS NULL OR latency_ms >= 0",
            name="ck_check_results_latency_nonnegative",
        ),
        sa.ForeignKeyConstraint(["monitor_id"], ["monitors.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_check_results_monitor_checked_at",
        "check_results",
        ["monitor_id", "checked_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_check_results_monitor_checked_at", table_name="check_results")
    op.drop_table("check_results")
    op.drop_index("ix_monitors_active_next_run", table_name="monitors")
    op.drop_table("monitors")
