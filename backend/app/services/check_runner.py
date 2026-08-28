"""Execute one synthetic HTTP monitor check."""

from __future__ import annotations

from datetime import datetime, timezone
from time import perf_counter

import httpx

from app.schemas.check_result import CheckErrorType, CheckResultCreate, CheckStatus
from app.schemas.monitor import MonitorConfig


def run_check(monitor: MonitorConfig) -> CheckResultCreate:
    """Run one HTTP GET check and return a result suitable for persistence.

    The function deliberately has no database, scheduling, or alerting logic.
    Failures are returned as structured values so a bad endpoint cannot crash
    the scheduler that invoked this check.
    """

    checked_at = datetime.now(timezone.utc)
    started_at = perf_counter()

    try:
        timeout = httpx.Timeout(monitor.timeout_seconds)
        with httpx.Client(
            timeout=timeout,
            follow_redirects=False,
            headers={"User-Agent": "PulseWatch/0.1"},
        ) as client:
            response = client.get(monitor.url)

        latency_ms = _elapsed_ms(started_at)

        if response.status_code in monitor.expected_status_codes:
            return CheckResultCreate(
                monitor_id=monitor.monitor_id,
                checked_at=checked_at,
                status=CheckStatus.SUCCESS,
                http_status_code=response.status_code,
                latency_ms=latency_ms,
            )

        return CheckResultCreate(
            monitor_id=monitor.monitor_id,
            checked_at=checked_at,
            status=CheckStatus.FAILURE,
            http_status_code=response.status_code,
            latency_ms=latency_ms,
            error_type=CheckErrorType.UNEXPECTED_STATUS,
            error_message=(
                f"Expected one of {monitor.expected_status_codes}; "
                f"received HTTP {response.status_code}."
            ),
        )

    except (httpx.InvalidURL, httpx.UnsupportedProtocol):
        return _failure_result(
            monitor=monitor,
            checked_at=checked_at,
            started_at=started_at,
            error_type=CheckErrorType.INVALID_CONFIGURATION,
            error_message="The monitor URL could not be requested.",
        )
    except httpx.TimeoutException:
        return _failure_result(
            monitor=monitor,
            checked_at=checked_at,
            started_at=started_at,
            error_type=CheckErrorType.TIMEOUT,
            error_message=f"Request timed out after {monitor.timeout_seconds} seconds.",
        )
    except httpx.RequestError as error:
        return _failure_result(
            monitor=monitor,
            checked_at=checked_at,
            started_at=started_at,
            error_type=CheckErrorType.CONNECTION_ERROR,
            error_message=f"Request failed with {error.__class__.__name__}.",
        )
    except Exception as error:  # Defensive boundary for the scheduler.
        return _failure_result(
            monitor=monitor,
            checked_at=checked_at,
            started_at=started_at,
            error_type=CheckErrorType.INTERNAL_ERROR,
            error_message=f"Unexpected runner error: {error.__class__.__name__}.",
        )


def _failure_result(
    *,
    monitor: MonitorConfig,
    checked_at: datetime,
    started_at: float,
    error_type: CheckErrorType,
    error_message: str,
) -> CheckResultCreate:
    return CheckResultCreate(
        monitor_id=monitor.monitor_id,
        checked_at=checked_at,
        status=CheckStatus.FAILURE,
        latency_ms=_elapsed_ms(started_at),
        error_type=error_type,
        error_message=error_message,
    )


def _elapsed_ms(started_at: float) -> float:
    """Return a readable, non-negative latency measurement in milliseconds."""

    return round(max(0.0, (perf_counter() - started_at) * 1_000), 2)
