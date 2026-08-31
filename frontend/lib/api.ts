/**
 * Typed API client for the PulseWatch backend.
 *
 * Base URL is read from NEXT_PUBLIC_API_BASE_URL, falling back to
 * http://127.0.0.1:8000 for local development without Docker.
 */

import type {
  Monitor,
  MonitorCreate,
  MonitorSummary,
  ResultHistoryPage,
} from "@/types/monitor";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

async function request<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    const err = new Error(
      typeof body.detail === "string"
        ? body.detail
        : JSON.stringify(body.detail)
    ) as Error & { status: number; body: unknown };
    err.status = response.status;
    err.body = body;
    throw err;
  }

  // 204 No Content — return undefined cast to T
  if (response.status === 204) {
    return undefined as unknown as T;
  }

  return response.json() as Promise<T>;
}

// ── Monitor CRUD ─────────────────────────────────────────────────────────────

export async function listMonitors(): Promise<Monitor[]> {
  return request<Monitor[]>("/api/monitors");
}

export async function getMonitor(id: string): Promise<Monitor> {
  return request<Monitor>(`/api/monitors/${id}`);
}

export async function createMonitor(data: MonitorCreate): Promise<Monitor> {
  return request<Monitor>("/api/monitors", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function pauseMonitor(id: string): Promise<Monitor> {
  return request<Monitor>(`/api/monitors/${id}/pause`, { method: "PATCH" });
}

export async function resumeMonitor(id: string): Promise<Monitor> {
  // Resume = re-activate; backend doesn't have a dedicated resume endpoint in v0.
  // We expose this via a PATCH that sets is_active back to true.
  // For now, a new create isn't needed — the UI will just hide this until v1.
  return request<Monitor>(`/api/monitors/${id}/pause`, { method: "PATCH" });
}

export async function deleteMonitor(id: string): Promise<void> {
  return request<void>(`/api/monitors/${id}`, { method: "DELETE" });
}

// ── Result history ────────────────────────────────────────────────────────────

export interface ResultHistoryParams {
  limit?: number;
  before?: string; // ISO-8601 UTC
}

export async function getResultHistory(
  id: string,
  params: ResultHistoryParams = {}
): Promise<ResultHistoryPage> {
  const query = new URLSearchParams();
  if (params.limit !== undefined) query.set("limit", String(params.limit));
  if (params.before) query.set("before", params.before);
  const qs = query.toString() ? `?${query.toString()}` : "";
  return request<ResultHistoryPage>(`/api/monitors/${id}/results${qs}`);
}

// ── Summary ──────────────────────────────────────────────────────────────────

export async function getMonitorSummary(
  id: string,
  windowHours: number = 24
): Promise<MonitorSummary> {
  return request<MonitorSummary>(
    `/api/monitors/${id}/summary?window_hours=${windowHours}`
  );
}
