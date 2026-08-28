"""Input models used to configure a single synthetic HTTP check."""

from __future__ import annotations

from uuid import UUID
from urllib.parse import urlparse



from pydantic import BaseModel, Field, field_validator


class MonitorConfig(BaseModel):
    """The portion of a monitor needed by the check runner.

    This is intentionally separate from the database model. The runner should
    only need the configuration required to execute one request.
    """

    monitor_id: UUID
    url: str = Field(min_length=1, max_length=2_048)
    timeout_seconds: float = Field(default=5.0, gt=0, le=60)
    expected_status_codes: list[int] = Field(default_factory=lambda: [200], min_length=1)

    @field_validator("url")
    @classmethod
    def validate_http_url(cls, value: str) -> str:
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("url must be an absolute HTTP or HTTPS URL")
        return value

    @field_validator("expected_status_codes")
    @classmethod
    def validate_status_codes(cls, value: list[int]) -> list[int]:
        if any(status_code < 100 or status_code > 599 for status_code in value):
            raise ValueError("expected_status_codes must contain valid HTTP status codes")
        return value
