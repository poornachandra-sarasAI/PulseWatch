"use client";

import Link from "next/link";
import type { Monitor } from "@/types/monitor";
import StatusBadge from "./status-badge";

interface MonitorCardProps {
  monitor: Monitor;
}

function formatTimestamp(iso: string | null): string {
  if (!iso) return "Never";
  const d = new Date(iso);
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffSecs = Math.floor(diffMs / 1000);
  if (diffSecs < 60) return `${diffSecs}s ago`;
  if (diffSecs < 3600) return `${Math.floor(diffSecs / 60)}m ago`;
  if (diffSecs < 86400) return `${Math.floor(diffSecs / 3600)}h ago`;
  return d.toLocaleDateString();
}

function formatLatency(ms: number | null): string {
  if (ms === null) return "—";
  if (ms < 1000) return `${Math.round(ms)}ms`;
  return `${(ms / 1000).toFixed(2)}s`;
}

export default function MonitorCard({ monitor }: MonitorCardProps) {
  const hostname = (() => {
    try { return new URL(monitor.url).hostname; } catch { return monitor.url; }
  })();

  return (
    <Link href={`/monitors/${monitor.id}`} className="block fade-in">
      <div className="glass-card p-5 group cursor-pointer">
        {/* Header row */}
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className="min-w-0 flex-1">
            <h3
              className="font-semibold text-base truncate"
              style={{ color: "var(--text-primary)" }}
            >
              {monitor.name}
            </h3>
            <p
              className="text-xs mt-0.5 truncate"
              style={{ color: "var(--text-muted)" }}
            >
              {hostname}
            </p>
          </div>
          <StatusBadge
            status={monitor.current_status}
            isActive={monitor.is_active}
            size="sm"
          />
        </div>

        {/* URL pill */}
        <p
          className="text-xs font-mono truncate mb-4 px-2 py-1 rounded"
          style={{
            background: "rgba(255,255,255,0.04)",
            color: "var(--text-secondary)",
            border: "1px solid var(--border)",
          }}
        >
          {monitor.url}
        </p>

        {/* Metrics row */}
        <div className="grid grid-cols-3 gap-3">
          <Metric
            label="Interval"
            value={`${monitor.interval_seconds}s`}
          />
          <Metric
            label="Last check"
            value={formatTimestamp(monitor.last_checked_at)}
          />
          <Metric
            label="Consecutive fails"
            value={String(monitor.consecutive_failures)}
            highlight={monitor.consecutive_failures > 0}
          />
        </div>
      </div>
    </Link>
  );
}

function Metric({
  label,
  value,
  highlight = false,
}: {
  label: string;
  value: string;
  highlight?: boolean;
}) {
  return (
    <div>
      <p className="text-xs" style={{ color: "var(--text-muted)" }}>
        {label}
      </p>
      <p
        className="text-sm font-medium mt-0.5"
        style={{ color: highlight ? "var(--red)" : "var(--text-secondary)" }}
      >
        {value}
      </p>
    </div>
  );
}
