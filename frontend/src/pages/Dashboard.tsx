import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { AlertTriangle, CheckCircle2, Clock3, Gauge, Loader2 } from "lucide-react";
import { getDashboardSummary } from "../lib/api";
import type { DashboardSummary } from "../types";

const STATUS_LABELS: Record<string, string> = {
  pending_confirmation: "Pending Confirmation",
  matching: "Matching",
  matched: "Matched",
  exception: "Exception",
  failed: "Failed",
};

const STATUS_COLORS: Record<string, string> = {
  pending_confirmation: "#94a3b8",
  matching: "#6366f1",
  matched: "#10b981",
  exception: "#f59e0b",
  failed: "#ef4444",
};

export function Dashboard() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getDashboardSummary()
      .then(setSummary)
      .catch(() => setError("Could not load dashboard data."));
  }, []);

  if (error) {
    return <p className="text-sm text-red-600">{error}</p>;
  }
  if (!summary) {
    return (
      <div className="flex items-center gap-2 text-sm text-slate-500">
        <Loader2 className="h-4 w-4 animate-spin" /> Loading dashboard…
      </div>
    );
  }

  const hasActivity = summary.processed_count + summary.in_flight > 0;
  const statusData = Object.entries(summary.pipeline_status_counts).map(([status, count]) => ({
    status,
    label: STATUS_LABELS[status] ?? status,
    count,
    color: STATUS_COLORS[status] ?? "#94a3b8",
  }));
  const docTypeData = Object.entries(summary.doc_type_distribution).map(([name, count]) => ({ name, count }));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-white">Dashboard</h1>
        <p className="text-sm text-slate-500 dark:text-slate-400">Document processing overview</p>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
        <KpiCard icon={CheckCircle2} label="Processed" value={summary.processed_count} sublabel="batches completed" />
        <KpiCard icon={Gauge} label="Match Rate" value={`${Math.round(summary.match_rate * 100)}%`} sublabel="all rules passed" />
        <KpiCard icon={AlertTriangle} label="Open Exceptions" value={summary.open_exceptions} sublabel="need review" accent="amber" />
        <KpiCard icon={Gauge} label="Avg Confidence" value={`${Math.round(summary.avg_confidence * 100)}%`} sublabel="extraction quality" />
        <KpiCard icon={Clock3} label="In Flight" value={summary.in_flight} sublabel="being processed" />
      </div>

      {!hasActivity ? (
        <div className="rounded-2xl border border-slate-200 bg-white p-10 text-center dark:border-slate-800 dark:bg-slate-900">
          <p className="text-sm font-medium text-slate-900 dark:text-white">No activity yet</p>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Process a batch from the Process page to see pipeline status and analytics here.
          </p>
        </div>
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          <ChartCard title="Pipeline Status" subtitle="Where work sits right now">
            {statusData.length === 0 ? (
              <EmptyChart />
            ) : statusData.length === 1 ? (
              // A single-category "pie" is a degenerate 100%-one-color circle
              // with no real proportion to show — a plain stat reads better
              // than a chart here, and sidesteps a genuine Recharts rendering
              // bug where a lone Pie slice's sweep angle comes out wrong.
              <div className="flex h-[220px] flex-col items-center justify-center gap-2">
                <span className="h-3 w-3 rounded-full" style={{ backgroundColor: statusData[0].color }} />
                <p className="text-2xl font-semibold text-slate-900 dark:text-white">{statusData[0].count}</p>
                <p className="text-sm text-slate-500 dark:text-slate-400">All batches: {statusData[0].label}</p>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie data={statusData} dataKey="count" nameKey="label" innerRadius={50} outerRadius={80} paddingAngle={2}>
                    {statusData.map((entry) => (
                      <Cell key={entry.status} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            )}
            <Legend items={statusData.map((d) => ({ label: d.label, color: d.color, count: d.count }))} />
          </ChartCard>

          <ChartCard title="Document Type Distribution" subtitle="Confirmed types across all documents">
            {docTypeData.length === 0 ? (
              <EmptyChart />
            ) : (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={docTypeData}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                  <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </ChartCard>
        </div>
      )}
    </div>
  );
}

function KpiCard({
  icon: Icon,
  label,
  value,
  sublabel,
  accent,
}: {
  icon: typeof Gauge;
  label: string;
  value: string | number;
  sublabel: string;
  accent?: "amber";
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className={`flex h-7 w-7 items-center justify-center rounded-md ${accent === "amber" ? "bg-amber-50 text-amber-600 dark:bg-amber-950" : "bg-indigo-50 text-indigo-600 dark:bg-indigo-950"}`}>
        <Icon className="h-3.5 w-3.5" />
      </div>
      <p className="mt-3 text-2xl font-semibold tabular-nums text-slate-900 dark:text-white">{value}</p>
      <p className="text-xs font-medium text-slate-500 dark:text-slate-400">{label}</p>
      <p className="text-[11px] text-slate-400 dark:text-slate-500">{sublabel}</p>
    </div>
  );
}

function ChartCard({ title, subtitle, children }: { title: string; subtitle: string; children: React.ReactNode }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <p className="text-sm font-semibold text-slate-900 dark:text-white">{title}</p>
      <p className="text-xs text-slate-500 dark:text-slate-400">{subtitle}</p>
      <div className="mt-3">{children}</div>
    </div>
  );
}

function EmptyChart() {
  return <div className="flex h-[220px] items-center justify-center text-sm text-slate-400">No activity in this window</div>;
}

function Legend({ items }: { items: { label: string; color: string; count: number }[] }) {
  return (
    <div className="mt-3 flex flex-wrap gap-3">
      {items.map((item) => (
        <div key={item.label} className="flex items-center gap-1.5 text-xs text-slate-600 dark:text-slate-300">
          <span className="h-2 w-2 rounded-full" style={{ backgroundColor: item.color }} />
          {item.label} ({item.count})
        </div>
      ))}
    </div>
  );
}
