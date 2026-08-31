import MonitorForm from "@/components/monitor-form";

export const metadata = {
  title: "New Monitor — PulseWatch",
  description: "Add a new HTTP uptime monitor.",
};

export default function NewMonitorPage() {
  return (
    <div className="max-w-lg mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold gradient-text">New Monitor</h1>
        <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>
          Configure an HTTP endpoint to be checked at a regular interval.
        </p>
      </div>

      <div className="glass-card p-6">
        <MonitorForm />
      </div>
    </div>
  );
}
