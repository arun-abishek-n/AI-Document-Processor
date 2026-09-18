import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { AlertTriangle, ArrowLeft, CheckCircle2, Download, Loader2, XCircle } from "lucide-react";
import { FieldsTable } from "../components/FieldsTable";
import { TextPanel } from "../components/TextPanel";
import { JsonPanel } from "../components/JsonPanel";
import { getBatch } from "../lib/api";
import { downloadFile } from "../lib/export";
import type { BatchDetail as BatchDetailType, MatchRuleResult } from "../types";

const RULE_ICON: Record<string, typeof CheckCircle2> = {
  passed: CheckCircle2,
  warning: AlertTriangle,
  failed: XCircle,
};

const RULE_COLOR: Record<string, string> = {
  passed: "text-emerald-500",
  warning: "text-amber-500",
  failed: "text-red-500",
};

export function BatchDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [batch, setBatch] = useState<BatchDetailType | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id) return;
    getBatch(Number(id))
      .then(setBatch)
      .catch(() => setError("Could not load this batch."));
  }, [id]);

  if (error) return <p className="text-sm text-red-600">{error}</p>;
  if (!batch) {
    return (
      <div className="flex items-center gap-2 text-sm text-slate-500">
        <Loader2 className="h-4 w-4 animate-spin" /> Loading…
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={() => navigate("/process")}
          className="inline-flex items-center gap-1.5 text-sm font-medium text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
        >
          <ArrowLeft className="h-4 w-4" /> Back to Process
        </button>
        <button
          type="button"
          onClick={() => downloadFile(JSON.stringify(batch, null, 2), `batch-${batch.id}.json`, "application/json")}
          className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
        >
          <Download className="h-3.5 w-3.5" /> Download JSON
        </button>
      </div>

      <div>
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-white">{batch.name}</h1>
          <StatusBanner status={batch.status} />
        </div>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          {batch.match_config_name} &middot; {batch.document_count} document(s) &middot; {batch.processing_time_seconds}s
        </p>
      </div>

      {batch.rule_results.length > 0 && (
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <p className="text-sm font-semibold text-slate-900 dark:text-white">Match Result</p>
          <div className="mt-3 space-y-3">
            {batch.rule_results.map((rule) => (
              <RuleRow key={rule.id} rule={rule} />
            ))}
          </div>
        </div>
      )}

      <div className="space-y-6">
        {batch.documents.map((doc) => (
          <div key={doc.id} className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-semibold text-slate-900 dark:text-white">{doc.original_filename}</p>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  {doc.document_type_name ?? "Unassigned"} &middot; {Math.round(doc.overall_confidence * 100)}% confidence &middot;{" "}
                  {doc.page_count} page(s)
                </p>
              </div>
            </div>
            <FieldsTable fields={doc.extracted_fields} />
            <div className="grid gap-4 lg:grid-cols-2">
              <TextPanel text={doc.raw_text} />
              <JsonPanel data={doc.extracted_fields} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function StatusBanner({ status }: { status: string }) {
  const styles: Record<string, string> = {
    matched: "bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-400",
    exception: "bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-400",
    failed: "bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-400",
    pending_confirmation: "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300",
  };
  return (
    <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${styles[status] ?? "bg-slate-100 text-slate-600"}`}>
      {status.replace("_", " ")}
    </span>
  );
}

function RuleRow({ rule }: { rule: MatchRuleResult }) {
  const Icon = RULE_ICON[rule.status] ?? AlertTriangle;
  const color = RULE_COLOR[rule.status] ?? "text-slate-400";
  const values = rule.detail.values ?? {};

  return (
    <div className="flex items-start gap-3 rounded-xl border border-slate-100 p-3 dark:border-slate-800">
      <Icon className={`mt-0.5 h-4 w-4 shrink-0 ${color}`} />
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium text-slate-900 dark:text-white">{rule.rule_name}</p>
        <div className="mt-1 flex flex-wrap gap-x-4 gap-y-0.5 text-xs text-slate-500 dark:text-slate-400">
          {Object.entries(values).map(([name, value]) => (
            <span key={name}>
              <span className="text-slate-400">{name}:</span> {value ?? "—"}
            </span>
          ))}
        </div>
        {rule.detail.reason && <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{rule.detail.reason}</p>}
        {rule.detail.difference_percent !== undefined && (
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            Difference: {rule.detail.difference_percent}%
            {rule.detail.tolerance_percent !== undefined && ` (tolerance: ${rule.detail.tolerance_percent}%)`}
          </p>
        )}
      </div>
    </div>
  );
}
