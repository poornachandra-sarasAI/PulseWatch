from datetime import datetime, timezone
import unittest

from app.scheduler.monitor_scheduler import _next_run_after


class NextRunAfterTests(unittest.TestCase):
    def test_uses_the_original_schedule_when_a_check_completes_quickly(self) -> None:
        scheduled_for = datetime(2026, 8, 30, 10, 0, tzinfo=timezone.utc)
        completed_at = datetime(2026, 8, 30, 10, 0, 3, tzinfo=timezone.utc)

        next_run_at = _next_run_after(
            scheduled_for=scheduled_for,
            interval_seconds=60,
            completed_at=completed_at,
        )

        self.assertEqual(next_run_at, datetime(2026, 8, 30, 10, 1, tzinfo=timezone.utc))

    def test_skips_intervals_missed_while_the_scheduler_was_delayed(self) -> None:
        scheduled_for = datetime(2026, 8, 30, 10, 0, tzinfo=timezone.utc)
        completed_at = datetime(2026, 8, 30, 10, 3, 1, tzinfo=timezone.utc)

        next_run_at = _next_run_after(
            scheduled_for=scheduled_for,
            interval_seconds=60,
            completed_at=completed_at,
        )

        self.assertEqual(next_run_at, datetime(2026, 8, 30, 10, 4, tzinfo=timezone.utc))


if __name__ == "__main__":
    unittest.main()
