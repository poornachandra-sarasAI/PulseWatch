import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PulseWatch — HTTP Uptime Monitor",
  description:
    "PulseWatch monitors your HTTP endpoints and tracks uptime, latency, and failures in real time.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen antialiased">
        {/* ── Top nav ──────────────────────────────────────────────────────── */}
        <nav
          className="sticky top-0 z-50 border-b"
          style={{
            background: "rgba(8, 13, 24, 0.85)",
            backdropFilter: "blur(16px)",
            borderColor: "var(--border)",
          }}
        >
          <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
            <a href="/" className="flex items-center gap-2.5">
              {/* Pulse icon */}
              <svg
                width="28"
                height="28"
                viewBox="0 0 28 28"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
              >
                <rect width="28" height="28" rx="7" fill="url(#grad)" />
                <polyline
                  points="3,14 8,14 10,8 13,20 16,10 19,18 21,14 25,14"
                  fill="none"
                  stroke="white"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
                <defs>
                  <linearGradient id="grad" x1="0" y1="0" x2="28" y2="28">
                    <stop offset="0%" stopColor="#0ea5e9" />
                    <stop offset="100%" stopColor="#818cf8" />
                  </linearGradient>
                </defs>
              </svg>
              <span className="font-bold text-lg tracking-tight gradient-text">
                PulseWatch
              </span>
            </a>

            <a
              href="/monitors"
              className="btn-primary"
              style={{ padding: "8px 16px", fontSize: "13px" }}
            >
              <svg
                width="14"
                height="14"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M12 4v16m8-8H4"
                />
              </svg>
              New Monitor
            </a>
          </div>
        </nav>

        {/* ── Page content ─────────────────────────────────────────────────── */}
        <main className="max-w-6xl mx-auto px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
