"""Run one PulseWatch HTTP check from the command line.

Example:
    python backend/scripts/run_check.py https://example.com --expected-status 200
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from uuid import uuid4

# Running this file directly places ``backend/scripts`` on sys.path, rather
# than ``backend``. Add the backend directory so the app package can be found.
BACKEND_DIRECTORY = Path(__file__).resolve().parents[1]
if str(BACKEND_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIRECTORY))

from pydantic import ValidationError

from app.schemas.check_result import CheckStatus
from app.schemas.monitor import MonitorConfig
from app.services.check_runner import run_check


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run one PulseWatch synthetic HTTP check and print its JSON result."
    )
    parser.add_argument("url", help="Absolute HTTP or HTTPS URL to check.")
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="Maximum request duration in seconds (default: 5).",
    )
    parser.add_argument(
        "--expected-status",
        type=int,
        nargs="+",
        default=[200],
        metavar="STATUS_CODE",
        help="One or more successful HTTP status codes (default: 200).",
    )
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()

    try:
        monitor = MonitorConfig(
            monitor_id=uuid4(),
            url=arguments.url,
            timeout_seconds=arguments.timeout,
            expected_status_codes=arguments.expected_status,
        )
    except ValidationError as error:
        print(error, file=sys.stderr)
        return 2

    result = run_check(monitor)
    print(json.dumps(result.model_dump(mode="json"), indent=2))

    return 0 if result.status is CheckStatus.SUCCESS else 1


if __name__ == "__main__":
    raise SystemExit(main())
