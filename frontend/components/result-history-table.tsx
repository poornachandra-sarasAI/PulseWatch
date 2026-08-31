"use client";

import { useState } from "react";
import { getResultHistory } from "@/lib/api";
import type { CheckResult } from "@/types/monitor";
import StatusBadge from "./status-badge";

interface ResultHistoryTableProps {
  monitorId: string;
  initialItems: CheckResult[];
  initialNextBefore: string | null;
}

function formatTs(iso: string): string {
  return new Date(iso).toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function formatLatency(ms: number | null): string {
  if (ms === null) return "—";
  if (ms < 1000) return `${Math.round(ms)}ms`;
  return `${(ms / 1000).toFixed(2)}s`;
}

export default function ResultHistoryTable({
  monitorId,
  initialItems,
  initialNextBefore,
}: ResultHistoryTableProps) {
  const [items, setItems] = useState<CheckResult[]>(initialItems);
  const [nextBefore, setNextBefore] = useState<string | null>(initialNextBefore);
  const [loading, setLoading] = useState(false);

  async function loadMore() {
    if (!nextBefore || loading) return;
    setLoading(true);
    try {
      const page = await getResultHistory(monitorId, { before: nextBefore, limit: 50 });
      setItems((prev) => [...prev, ...page.items]);
      setNextBefore(page.next_before);
    } catch {
      // silently swallow pagination errors
    } finally {
      setLoading(false);
    }
  }

  if (items.length === 0) {
    return (
      <div
        className="flex items-center justify-center py-10 rounded-lg text-sm"
        style={{
          background: "rgba(255,255,255,0.02)",
          border: "1px solid var(--border)",
          color: "var(--text-muted)",
        }}
      >
        No check results recorded yet.
      </div>
    );
  }

  return (
    <div>
      <div className="overflow-x-auto rounded-lg" style={{ border: "1px solid var(--border)" }}>
        <table className="pw-table">
          <thead>
            <tr>
              <th>Time</th>
              <th>Status</th>
              <th>HTTP Code</th>
              <th>Latency</th>
              <th>Error Type</th>
              <th>Error Message</th>
            </tr>
          </thead>
          <tbody>
            {items.map((r) => (
              <tr key={r.id}>
                <td style={{ color: "var(--text-secondary)", whiteSpace: "nowrap" }}>
                  {formatTs(r.checked_at)}
                </td>
                <td>
                  <StatusBadge status={r.status} size="sm" />
                </td>
                <td>
                  {r.http_status_code !== null ? (
                    <span
                      style={{
                        color:
                          r.http_status_code >= 200 && r.http_status_code < 300
                            ? "var(--green)"
                            : "var(--red)",
                        fontWeight: 500,
                      }}
                    >
                      {r.http_status_code}
                    </span>
                  ) : (
                    <span style={{ color: "var(--text-muted)" }}>—</span>
                  )}
                </td>
                <td>
                  <span
                    style={{
                      color:
                        r.latency_ms === null
                          ? "var(--text-muted)"
                          : r.latency_ms < 500
                          ? "var(--green)"
                          : r.latency_ms < 1000
                          ? "var(--yellow)"
                          : "var(--red)",
                      fontWeight: 500,
                    }}
                  >
                    {formatLatency(r.latency_ms)}
                  </span>
                </td>
                <td>
                  {r.error_type ? (
                    <span
                      className="text-xs font-mono px-2 py-0.5 rounded"
                      style={{
                        background: "var(--red-dim)",
                        color: "var(--red)",
                        border: "1px solid rgba(244,63,94,0.2)",
                      }}
                    >
                      {r.error_type}
                    </span>
                  ) : (
                    <span style={{ color: "var(--text-muted)" }}>—</span>
                  )}
                </td>
                <td
                  className="max-w-xs truncate text-xs"
                  style={{ color: "var(--text-muted)" }}
                  title={r.error_message ?? undefined}
                >
                  {r.error_message ?? "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Load more */}
      {nextBefore && (
        <div className="mt-4 flex justify-center">
          <button
            onClick={loadMore}
            disabled={loading}
            className="btn-secondary text-sm"
          >
            {loading ? "Loading…" : "Load more results"}
          </button>
        </div>
      )}
    </div>
  );
}
