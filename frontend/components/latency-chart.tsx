"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import type { CheckResult } from "@/types/monitor";

interface LatencyChartProps {
  results: CheckResult[];
}

interface ChartPoint {
  time: string;
  latency: number | null;
  status: "SUCCESS" | "FAILURE";
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function CustomTooltip({ active, payload }: any) {
  if (!active || !payload?.length) return null;
  const d = payload[0]?.payload as ChartPoint;
  return (
    <div
      className="rounded-lg px-3 py-2 text-xs"
      style={{
        background: "rgba(15,23,42,0.95)",
        border: "1px solid var(--border)",
        color: "var(--text-secondary)",
        boxShadow: "0 8px 24px rgba(0,0,0,0.4)",
      }}
    >
      <p style={{ color: "var(--text-primary)", fontWeight: 600 }}>{d.time}</p>
      {d.latency !== null ? (
        <p style={{ color: d.status === "SUCCESS" ? "var(--green)" : "var(--red)" }}>
          {d.status === "SUCCESS" ? `${Math.round(d.latency)}ms` : "FAILED"}
        </p>
      ) : (
        <p style={{ color: "var(--red)" }}>FAILED</p>
      )}
    </div>
  );
}

export default function LatencyChart({ results }: LatencyChartProps) {
  if (results.length === 0) {
    return (
      <div
        className="flex items-center justify-center h-40 rounded-lg"
        style={{ background: "rgba(255,255,255,0.02)", border: "1px solid var(--border)" }}
      >
        <p className="text-sm" style={{ color: "var(--text-muted)" }}>
          No data yet
        </p>
      </div>
    );
  }

  // Chart shows data chronologically (oldest → newest)
  const data: ChartPoint[] = [...results]
    .reverse()
    .map((r) => ({
      time: new Date(r.checked_at).toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      }),
      latency: r.latency_ms,
      status: r.status,
    }));

  const maxLatency = Math.max(...data.map((d) => d.latency ?? 0));
  const yMax = Math.max(maxLatency * 1.2, 100);

  return (
    <ResponsiveContainer width="100%" height={200}>
      <LineChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
        <CartesianGrid
          strokeDasharray="3 3"
          stroke="rgba(99,130,180,0.1)"
          vertical={false}
        />
        <XAxis
          dataKey="time"
          tick={{ fill: "var(--text-muted)", fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          interval="preserveStartEnd"
        />
        <YAxis
          tick={{ fill: "var(--text-muted)", fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          domain={[0, yMax]}
          tickFormatter={(v: number) => `${v}ms`}
          width={52}
        />
        <Tooltip content={<CustomTooltip />} />
        <Line
          type="monotone"
          dataKey="latency"
          stroke="var(--accent)"
          strokeWidth={2}
          dot={(props) => {
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            const point = (props as any).payload as ChartPoint;
            if (point.status === "FAILURE") {
              return (
                <circle
                  key={props.key}
                  cx={props.cx}
                  cy={props.cy}
                  r={4}
                  fill="var(--red)"
                  stroke="var(--red)"
                />
              );
            }
            return (
              <circle
                key={props.key}
                cx={props.cx}
                cy={props.cy}
                r={3}
                fill="var(--accent)"
                stroke="transparent"
              />
            );
          }}
          activeDot={{ r: 5, fill: "var(--accent)" }}
          connectNulls={false}
        />
        {/* Highlight failure points at y=0 */}
        {data
          .filter((d) => d.status === "FAILURE")
          .map((d, i) => (
            <ReferenceLine
              key={i}
              x={d.time}
              stroke="rgba(244,63,94,0.2)"
              strokeDasharray="4 4"
            />
          ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
