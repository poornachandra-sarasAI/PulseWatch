"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createMonitor } from "@/lib/api";
import type { MonitorCreate } from "@/types/monitor";

export default function MonitorForm() {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [statusCodesInput, setStatusCodesInput] = useState("200");

  const [form, setForm] = useState<Omit<MonitorCreate, "expected_status_codes">>({
    name: "",
    url: "",
    interval_seconds: 60,
    timeout_seconds: 5,
  });

  function handleChange(
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) {
    const { name, value } = e.target;
    setFieldErrors((prev) => ({ ...prev, [name]: "" }));
    setError(null);

    if (name === "expected_status_codes") {
      setStatusCodesInput(value);
    } else if (name === "interval_seconds" || name === "timeout_seconds") {
      setForm((prev) => ({ ...prev, [name]: parseFloat(value) || 0 }));
    } else {
      setForm((prev) => ({ ...prev, [name]: value }));
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    setFieldErrors({});

    const parsedCodes = statusCodesInput
      .split(",")
      .map((s) => parseInt(s.trim(), 10))
      .filter((n) => !Number.isNaN(n));

    if (parsedCodes.length === 0) {
      setFieldErrors((prev) => ({
        ...prev,
        expected_status_codes: "Please provide at least one valid status code (e.g. 200).",
      }));
      setSubmitting(false);
      return;
    }

    try {
      const monitor = await createMonitor({
        ...form,
        expected_status_codes: parsedCodes,
      });
      router.push(`/monitors/${monitor.id}`);
    } catch (err: unknown) {
      const apiErr = err as { status?: number; body?: { detail: unknown } };
      if (apiErr?.status === 409) {
        setError("A monitor already exists for this URL. Each URL must be unique.");
      } else if (apiErr?.status === 422 && Array.isArray(apiErr?.body?.detail)) {
        const fe: Record<string, string> = {};
        for (const d of apiErr.body!.detail as { loc: string[]; msg: string }[]) {
          const field = d.loc[d.loc.length - 1];
          fe[field] = d.msg;
        }
        setFieldErrors(fe);
      } else {
        setError(
          err instanceof Error ? err.message : "Something went wrong. Please try again."
        );
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {/* Global error */}
      {error && (
        <div
          className="px-4 py-3 rounded-lg text-sm flex items-start gap-2"
          style={{
            background: "var(--red-dim)",
            border: "1px solid rgba(244,63,94,0.3)",
            color: "#f87171",
          }}
        >
          <svg
            className="mt-0.5 shrink-0"
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
      )}

      <Field label="Monitor Name" error={fieldErrors.name}>
        <input
          id="name"
          name="name"
          type="text"
          className="form-input"
          placeholder="My API"
          value={form.name}
          onChange={handleChange}
          required
        />
      </Field>

      <Field label="URL" error={fieldErrors.url}>
        <input
          id="url"
          name="url"
          type="url"
          className="form-input"
          placeholder="https://api.example.com/health"
          value={form.url}
          onChange={handleChange}
          required
        />
      </Field>

      <div className="grid grid-cols-2 gap-4">
        <Field label="Interval (seconds)" error={fieldErrors.interval_seconds}>
          <input
            id="interval_seconds"
            name="interval_seconds"
            type="number"
            min={1}
            max={86400}
            className="form-input"
            value={form.interval_seconds}
            onChange={handleChange}
            required
          />
        </Field>

        <Field label="Timeout (seconds)" error={fieldErrors.timeout_seconds}>
          <input
            id="timeout_seconds"
            name="timeout_seconds"
            type="number"
            min={1}
            max={60}
            step={0.5}
            className="form-input"
            value={form.timeout_seconds}
            onChange={handleChange}
            required
          />
        </Field>
      </div>

      <Field
        label="Expected Status Codes (comma-separated)"
        error={fieldErrors.expected_status_codes}
      >
        <input
          id="expected_status_codes"
          name="expected_status_codes"
          type="text"
          className="form-input"
          placeholder="200, 201"
          value={statusCodesInput}
          onChange={handleChange}
          required
        />
      </Field>

      <div className="flex gap-3 pt-2">
        <button type="submit" className="btn-primary" disabled={submitting}>
          {submitting ? (
            <>
              <svg
                className="animate-spin"
                width="14"
                height="14"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                viewBox="0 0 24 24"
              >
                <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
              </svg>
              Creating…
            </>
          ) : (
            <>
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
              Create Monitor
            </>
          )}
        </button>

        <a href="/" className="btn-secondary">
          Cancel
        </a>
      </div>
    </form>
  );
}

function Field({
  label,
  error,
  children,
}: {
  label: string;
  error?: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label className="form-label">{label}</label>
      {children}
      {error && (
        <p className="mt-1 text-xs" style={{ color: "var(--red)" }}>
          {error}
        </p>
      )}
    </div>
  );
}
