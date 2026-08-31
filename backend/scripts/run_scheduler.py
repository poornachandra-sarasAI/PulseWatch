"""Start the PulseWatch v0 scheduler as a separate process."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

BACKEND_DIRECTORY = Path(__file__).resolve().parents[1]
if str(BACKEND_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIRECTORY))

from app.scheduler.monitor_scheduler import run_forever, run_scheduled_checks


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the PulseWatch scheduler.")
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=5.0,
        help="Seconds between scheduler polls (default: 5).",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run one scheduler cycle, then exit.",
    )
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    if arguments.once:
        attempted_checks = run_scheduled_checks()
        logging.info("Completed %s scheduled check(s)", attempted_checks)
        return 0

    run_forever(poll_interval_seconds=arguments.poll_interval)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
