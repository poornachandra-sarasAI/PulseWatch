"""Structured output produced by one synthetic HTTP check."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class CheckStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


class CheckErrorType(str, Enum):
    TIMEOUT = "TIMEOUT"
    CONNECTION_ERROR = "CONNECTION_ERROR"
    INVALID_CONFIGURATION = "INVALID_CONFIGURATION"
    UNEXPECTED_STATUS = "UNEXPECTED_STATUS"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class CheckResultCreate(BaseModel):
    """A result ready for the persistence layer to save.

    The database assigns this record's own ID; the runner only supplies the
    monitor it belongs to and the facts observed during the check.
    """

    monitor_id: UUID
    checked_at: datetime
    status: CheckStatus
    http_status_code: int | None = Field(default=None, ge=100, le=599)
    latency_ms: float | None = Field(default=None, ge=0)
    error_type: CheckErrorType | None = None
    error_message: str | None = Field(default=None, max_length=500)
