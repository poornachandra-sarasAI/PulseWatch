/** TypeScript types matching PulseWatch FastAPI response schemas. */

export interface Monitor {
  id: string;
  name: string;
  url: string;
  interval_seconds: number;
  timeout_seconds: number;
  expected_status_codes: number[];
  is_active: boolean;
  current_status: "UNKNOWN" | "UP" | "DOWN";
  consecutive_failures: number;
  last_checked_at: string | null;
  next_run_at: string;
  created_at: string;
  updated_at: string;
}

export interface MonitorCreate {
  name: string;
  url: string;
  interval_seconds: number;
  timeout_seconds: number;
  expected_status_codes: number[];
}

export interface CheckResult {
  id: string;
  monitor_id: string;
  checked_at: string;
  status: "SUCCESS" | "FAILURE";
  http_status_code: number | null;
  latency_ms: number | null;
  error_type: string | null;
  error_message: string | null;
}

export interface ResultHistoryPage {
  items: CheckResult[];
  next_before: string | null;
}

export interface LatestResult {
  checked_at: string;
  status: "SUCCESS" | "FAILURE";
  http_status_code: number | null;
  latency_ms: number | null;
  error_type: string | null;
  error_message: string | null;
}

export interface MonitorSummary {
  window_hours: number;
  total_checks: number;
  successful_checks: number;
  uptime_pct: number | null;
  avg_latency_ms: number | null;
  latest_result: LatestResult | null;
}

export interface ApiError {
  detail: string | { msg: string; type: string }[];
}
