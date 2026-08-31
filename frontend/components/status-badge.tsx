"use client";

import type { Monitor } from "@/types/monitor";

interface StatusBadgeProps {
  status: Monitor["current_status"] | "SUCCESS" | "FAILURE";
  isActive?: boolean;
  size?: "sm" | "md";
}

const CONFIG = {
  UP: {
    label: "UP",
    dotClass: "status-dot-up",
    bg: "var(--green-dim)",
    color: "var(--green)",
    border: "rgba(34,197,94,0.25)",
  },
  DOWN: {
    label: "DOWN",
    dotClass: "status-dot-down",
    bg: "var(--red-dim)",
    color: "var(--red)",
    border: "rgba(244,63,94,0.25)",
  },
  UNKNOWN: {
    label: "UNKNOWN",
    dotClass: "status-dot-unknown",
    bg: "var(--yellow-dim)",
    color: "var(--yellow)",
    border: "rgba(245,158,11,0.25)",
  },
  SUCCESS: {
    label: "SUCCESS",
    dotClass: "status-dot-up",
    bg: "var(--green-dim)",
    color: "var(--green)",
    border: "rgba(34,197,94,0.25)",
  },
  FAILURE: {
    label: "FAILURE",
    dotClass: "status-dot-down",
    bg: "var(--red-dim)",
    color: "var(--red)",
    border: "rgba(244,63,94,0.25)",
  },
} as const;

export default function StatusBadge({
  status,
  isActive = true,
  size = "md",
}: StatusBadgeProps) {
  const cfg = CONFIG[status] ?? CONFIG.UNKNOWN;
  const dotSize = size === "sm" ? "6px" : "8px";
  const fontSize = size === "sm" ? "11px" : "12px";
  const padding = size === "sm" ? "3px 8px" : "4px 10px";

  return (
    <span
      className="inline-flex items-center gap-1.5 font-semibold rounded-full"
      style={{
        background: isActive ? cfg.bg : "rgba(71,85,105,0.2)",
        color: isActive ? cfg.color : "var(--text-muted)",
        border: `1px solid ${isActive ? cfg.border : "rgba(71,85,105,0.2)"}`,
        fontSize,
        padding,
        letterSpacing: "0.05em",
      }}
    >
      <span
        className={isActive ? cfg.dotClass : ""}
        style={{
          width: dotSize,
          height: dotSize,
          minWidth: dotSize,
          display: "inline-block",
          background: isActive ? undefined : "var(--text-muted)",
          borderRadius: "50%",
        }}
      />
      {isActive ? cfg.label : "PAUSED"}
    </span>
  );
}
