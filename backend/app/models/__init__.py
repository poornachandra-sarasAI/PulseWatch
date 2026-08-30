"""Import models so SQLAlchemy and Alembic see all mapped tables."""

from app.models.check_result import CheckResult
from app.models.monitor import Monitor

__all__ = ["CheckResult", "Monitor"]
