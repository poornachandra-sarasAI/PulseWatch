"use client";

import { use, useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  getMonitor,
  getMonitorSummary,
  getResultHistory,
  pauseMonitor,
  deleteMonitor,
} from "@/lib/api";
import type { Monitor, MonitorSummary, CheckResult } from "@/types/monitor";
import StatusBadge from "@/components/status-badge";
import LatencyChart from "@/components/latency-chart";
import ResultHistoryTable from "@/components/result-history-table";

// ── Helpers ──────────────────────────────────────────────────────────────────

function formatTs(iso: string | null): string {
  if (!iso) return "Never";
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

// ── Skeleton ─────────────────────────────────────────────────────────────────

function Skeleton() {
  return (
    <div className="space-y-6 fade-in">
      <div className="skeleton h-8 w-64" />
      <div className="glass-card p-6 space-y-4">
        <div className="skeleton h-4 w-full" />
        <div className="skeleton h-4 w-3/4" />
        <div className="skeleton h-4 w-1/2" />
      </div>
      <div className="glass-card p-6">
        <div className="skeleton h-40" />
      </div>
    </div>
  );
}

// ── Config block ─────────────────────────────────────────────────────────────

function ConfigRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-start gap-4 py-3" style={{ borderBottom: "1px solid var(--border)" }}>
      <dt className="text-sm w-44 shrink-0" style={{ color: "var(--text-muted)" }}>
        {label}
      </dt>
      <dd className="text-sm" style={{ color: "var(--text-secondary)" }}>
        {value}
      </dd>
    </div>
  );
}

// ── Metric chip ───────────────────────────────────────────────────────────────

function MetricChip({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color?: string;
}) {
  return (
    <div className="metric-chip">
      <span
        className="metric-chip-value"
        style={{ color: color ?? "var(--text-primary)" }}
      >
        {value}
      </span>
      <span className="metric-chip-label">{label}</span>
    </div>
  );
}

// ── Page ─────────────────────────────────────────────────────────────────────

export default function MonitorDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const router = useRouter();
  const { id } = use(params);

  const [monitor, setMonitor] = useState<Monitor | null>(null);
  const [summary, setSummary] = useState<MonitorSummary | null>(null);
  const [chartResults, setChartResults] = useState<CheckResult[]>([]);
  const [historyItems, setHistoryItems] = useState<CheckResult[]>([]);
  const [historyNextBefore, setHistoryNextBefore] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pausing, setPausing] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const fetchAll = useCallback(async () => {
    try {
      const [mon, summ, history] = await Promise.all([
        getMonitor(id),
        getMonitorSummary(id, 24),
        getResultHistory(id, { limit: 50 }),
      ]);
      setMonitor(mon);
      setSummary(summ);
      setChartResults(history.items);
      setHistoryItems(history.items);
      setHistoryNextBefore(history.next_before);
      setError(null);
    } catch (err: unknown) {
      const apiErr = err as { status?: number };
      if (apiErr?.status === 404) {
        setError("Monitor not found.");
      } else {
        setError(err instanceof Error ? err.message : "Failed to load monitor");
      }
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, 15_000);
    return () => clearInterval(interval);
  }, [fetchAll]);

  async function handlePause() {
    if (!monitor) return;
    setPausing(true);
    try {
      const updated = await pauseMonitor(id);
      setMonitor(updated);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Pause failed");
    } finally {
      setPausing(false);
    }
  }

  async function handleDelete() {
    if (
      !window.confirm(
        `Delete monitor "${monitor?.name}"?\n\nThis will permanently remove the monitor and all its check history.`
      )
    )
      return;

    setDeleting(true);
    try {
      await deleteMonitor(id);
      router.push("/");
    } catch (err) {
      alert(err instanceof Error ? err.message : "Delete failed");
      setDeleting(false);
    }
  }

  if (loading) return <Skeleton />;

  if (error) {
    return (
      <div className="fade-in">
        <div
          className="px-4 py-3 rounded-lg text-sm flex items-center gap-2 mb-6"
          style={{
            background: "var(--red-dim)",
            border: "1px solid rgba(244,63,94,0.3)",
            color: "#f87171",
          }}
        >
          <svg
            width="14"
            height="14"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            viewBox="0 0 24 24"
          >
            <circle cx="12" cy="12" r="10" />
            <path d="M12 8v4m0 4h.01" strokeLinecap="round" />
          </svg>
          {error}
        </div>
        <a href="/" className="btn-secondary">
          ← Back to dashboard
        </a>
      </div>
    );
  }

  if (!monitor) return null;

  const uptimePct =
    summary?.uptime_pct !== null && summary?.uptime_pct !== undefined
      ? `${summary.uptime_pct}%`
      : "—";

  const avgLatency =
    summary?.avg_latency_ms !== null && summary?.avg_latency_ms !== undefined
      ? formatLatency(summary.avg_latency_ms)
      : "—";

  return (
    <div className="space-y-6 fade-in">
      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <a
              href="/"
              className="text-sm"
              style={{ color: "var(--text-muted)" }}
            >
              ← Monitors
            </a>
          </div>
          <h1 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>
            {monitor.name}
          </h1>
          <p className="text-sm mt-1 font-mono" style={{ color: "var(--text-muted)" }}>
            {monitor.url}
          </p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <StatusBadge status={monitor.current_status} isActive={monitor.is_active} />

          {monitor.is_active && (
            <button
              onClick={handlePause}
              disabled={pausing}
              className="btn-secondary"
              style={{ padding: "8px 14px", fontSize: "13px" }}
              id="pause-monitor-btn"
            >
              {pausing ? "Pausing…" : "⏸ Pause"}
            </button>
          )}

          <button
            onClick={handleDelete}
            disabled={deleting}
            className="btn-danger"
            style={{ padding: "8px 14px", fontSize: "13px" }}
            id="delete-monitor-btn"
          >
            {deleting ? "Deleting…" : "🗑 Delete"}
          </button>

          <button
            onClick={fetchAll}
            className="btn-secondary"
            style={{ padding: "8px 12px", fontSize: "13px" }}
            title="Refresh"
          >
            <svg
              width="14"
              height="14"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
          </button>
        </div>
      </div>

      {/* ── Summary metrics ────────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <MetricChip
          label="24h Uptime"
          value={uptimePct}
          color={
            summary?.uptime_pct === null
              ? "var(--text-muted)"
              : summary!.uptime_pct! >= 99
              ? "var(--green)"
              : summary!.uptime_pct! >= 95
              ? "var(--yellow)"
              : "var(--red)"
          }
        />
        <MetricChip label="Avg Latency (24h)" value={avgLatency} />
        <MetricChip
          label="Total Checks (24h)"
          value={summary ? String(summary.total_checks) : "—"}
        />
        <MetricChip
          label="Consecutive Fails"
          value={String(monitor.consecutive_failures)}
          color={monitor.consecutive_failures > 0 ? "var(--red)" : undefined}
        />
      </div>

      {/* ── Configuration ──────────────────────────────────────────────────── */}
      <div className="glass-card p-6">
        <h2 className="text-sm font-semibold mb-4" style={{ color: "var(--text-primary)" }}>
          Configuration
        </h2>
        <dl>
          <ConfigRow label="Status" value={<StatusBadge status={monitor.current_status} isActive={monitor.is_active} size="sm" />} />
          <ConfigRow label="URL" value={<span className="font-mono text-xs">{monitor.url}</span>} />
          <ConfigRow label="Interval" value={`${monitor.interval_seconds}s`} />
          <ConfigRow label="Timeout" value={`${monitor.timeout_seconds}s`} />
          <ConfigRow
            label="Expected Codes"
            value={monitor.expected_status_codes.join(", ")}
          />
          <ConfigRow label="Last Checked" value={formatTs(monitor.last_checked_at)} />
          <ConfigRow label="Next Run" value={formatTs(monitor.next_run_at)} />
          <ConfigRow
            label="Created"
            value={new Date(monitor.created_at).toLocaleDateString()}
          />
        </dl>
      </div>

      {/* ── Latency chart ──────────────────────────────────────────────────── */}
      <div className="glass-card p-6">
        <h2 className="text-sm font-semibold mb-4" style={{ color: "var(--text-primary)" }}>
          Latency — last 50 checks
        </h2>
        <LatencyChart results={chartResults} />
      </div>

      {/* ── Result history ─────────────────────────────────────────────────── */}
      <div className="glass-card p-6">
        <h2 className="text-sm font-semibold mb-4" style={{ color: "var(--text-primary)" }}>
          Check History
        </h2>
        <ResultHistoryTable
          monitorId={id}
          initialItems={historyItems}
          initialNextBefore={historyNextBefore}
        />
      </div>
    </div>
  );
}
