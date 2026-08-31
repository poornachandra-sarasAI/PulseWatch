"""Enforce one monitor per URL.

Revision ID: 0002_enforce_unique_monitor_url
Revises: 0001_initial_monitoring_schema
Create Date: 2026-08-31
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_enforce_unique_monitor_url"
down_revision = "0001_initial_monitoring_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add the database-level URL uniqueness guarantee.

    Existing duplicates must be intentionally removed through the API before
    this migration is applied; this migration never deletes user data itself.
    """

    connection = op.get_bind()
    duplicate_url_count = connection.execute(
        sa.text(
            """
            SELECT COUNT(*)
            FROM (
                SELECT url
                FROM monitors
                GROUP BY url
                HAVING COUNT(*) > 1
            ) AS duplicate_urls
            """
        )
    ).scalar_one()

    if duplicate_url_count:
        raise RuntimeError(
            "Cannot enforce unique monitor URLs while duplicate URLs exist "
            f"({duplicate_url_count} duplicate URL group(s)). "
            "Delete duplicate monitors first."
        )

    op.create_unique_constraint("uq_monitors_url", "monitors", ["url"])


def downgrade() -> None:
    op.drop_constraint("uq_monitors_url", "monitors", type_="unique")
