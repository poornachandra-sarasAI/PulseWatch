"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { listMonitors } from "@/lib/api";
import type { Monitor } from "@/types/monitor";
import MonitorCard from "@/components/monitor-card";

function SkeletonCard() {
  return (
    <div className="glass-card p-5 space-y-3">
      <div className="skeleton h-4 w-2/3" />
      <div className="skeleton h-3 w-1/2" />
      <div className="skeleton h-8 w-full" />
      <div className="grid grid-cols-3 gap-3">
        <div className="skeleton h-10" />
        <div className="skeleton h-10" />
        <div className="skeleton h-10" />
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-24 fade-in">
      {/* Animated pulse icon */}
      <div className="relative mb-6">
        <div
          className="absolute inset-0 rounded-full animate-ping"
          style={{
            background: "var(--accent-dim)",
            animationDuration: "2s",
          }}
        />
        <div
          className="relative w-16 h-16 rounded-full flex items-center justify-center"
          style={{ background: "var(--accent-dim)", border: "1px solid var(--accent)" }}
        >
          <svg
            width="28"
            height="28"
            viewBox="0 0 28 28"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <polyline
              points="1,14 6,14 8,6 11,22 14,10 17,18 20,14 27,14"
              fill="none"
              stroke="var(--accent)"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>
      </div>

      <h2 className="text-xl font-semibold mb-2" style={{ color: "var(--text-primary)" }}>
        No monitors yet
      </h2>
      <p className="text-sm mb-8 text-center max-w-sm" style={{ color: "var(--text-secondary)" }}>
        Create your first monitor to start tracking uptime and latency for your HTTP endpoints.
      </p>
      <Link href="/monitors" className="btn-primary">
        <svg
          width="14"
          height="14"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.5"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
        </svg>
        Create your first monitor
      </Link>
    </div>
  );
}

export default function DashboardPage() {
  const [monitors, setMonitors] = useState<Monitor[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchMonitors = useCallback(async () => {
    try {
      const data = await listMonitors();
      setMonitors(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load monitors");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMonitors();
    // Poll every 15 seconds to pick up scheduler status updates
    const interval = setInterval(fetchMonitors, 15_000);
    return () => clearInterval(interval);
  }, [fetchMonitors]);

  return (
    <div>
      {/* Page header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold gradient-text">Monitors</h1>
          <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>
            {loading
              ? "Loading…"
              : `${monitors.length} monitor${monitors.length !== 1 ? "s" : ""} configured`}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchMonitors}
            className="btn-secondary"
            style={{ padding: "8px 14px", fontSize: "13px" }}
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
            Refresh
          </button>
        </div>
      </div>

      {/* Error */}
      {error && !loading && (
        <div
          className="px-4 py-3 rounded-lg text-sm mb-6 flex items-center gap-2"
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
          Could not reach the API: {error}
        </div>
      )}

      {/* Skeletons */}
      {loading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(3)].map((_, i) => <SkeletonCard key={i} />)}
        </div>
      )}

      {/* Empty state */}
      {!loading && monitors.length === 0 && !error && <EmptyState />}

      {/* Monitor grid */}
      {!loading && monitors.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {monitors.map((m) => (
            <MonitorCard key={m.id} monitor={m} />
          ))}
        </div>
      )}
    </div>
  );
}
