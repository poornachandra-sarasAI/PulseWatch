from app.schemas.monitor import MonitorConfig
from app.services.check_runner import run_check


monitor_config = MonitorConfig(
    monitor_id="11111111-1111-1111-1111-111111111111",
    url="https://mohanpoornachandra.com",
    timeout_seconds=10.0,
    expected_status_codes=[200, 201],
)

check_result = run_check(monitor_config)

print(check_result)