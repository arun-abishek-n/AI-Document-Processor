import { AlertTriangle, CheckCircle2, Download, FileJson, RotateCcw } from "lucide-react";
import type { ProcessResponse } from "../types";
import { baseFileName, downloadFile, resultToCsv } from "../lib/export";
import { OverviewCards } from "./OverviewCards";
import { FieldsTable } from "./FieldsTable";
import { TextPanel } from "./TextPanel";
import { JsonPanel } from "./JsonPanel";

interface ResultsDashboardProps {
  result: ProcessResponse;
  onReset: () => void;
}

export function ResultsDashboard({ result, onReset }: ResultsDashboardProps) {
  const name = baseFileName(result.source_file);

  return (
    <div className="space-y-6">
      <ValidationBanner result={result} />
      <OverviewCards result={result} />
      <FieldsTable fields={result.fields} />
      <TextPanel text={result.raw_text} />
      <JsonPanel data={result} />

      <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-200 pt-6 dark:border-slate-800">
        <button
          type="button"
          onClick={onReset}
          className="inline-flex items-center gap-2 rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
        >
          <RotateCcw className="h-4 w-4" />
          Process another document
        </button>

        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => downloadFile(JSON.stringify(result, null, 2), `${name}.json`, "application/json")}
            className="inline-flex items-center gap-2 rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
          >
            <FileJson className="h-4 w-4" />
            Download JSON
          </button>
          <button
            type="button"
            onClick={() => downloadFile(resultToCsv(result), `${name}.csv`, "text/csv")}
            className="inline-flex items-center gap-2 rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
          >
            <Download className="h-4 w-4" />
            Download CSV
          </button>
        </div>
      </div>
    </div>
  );
}

function ValidationBanner({ result }: { result: ProcessResponse }) {
  if (result.is_valid_document) {
    return (
      <div className="flex items-start gap-3 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 dark:border-emerald-900/60 dark:bg-emerald-950/30">
        <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-emerald-600 dark:text-emerald-400" />
        <div className="text-sm">
          <p className="font-medium text-emerald-900 dark:text-emerald-300">Document processed successfully</p>
          <p className="text-emerald-700 dark:text-emerald-400">
            All required fields were found and passed validation
            {result.low_confidence_fields.length > 0 &&
              ` — though ${result.low_confidence_fields.length} field(s) had low OCR confidence and may be worth a manual check.`}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 dark:border-amber-900/60 dark:bg-amber-950/30">
      <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-amber-600 dark:text-amber-400" />
      <div className="text-sm">
        <p className="font-medium text-amber-900 dark:text-amber-300">Document needs review</p>
        <div className="mt-1 space-y-0.5 text-amber-700 dark:text-amber-400">
          {result.missing_required_fields.length > 0 && (
            <p>Missing required field(s): {result.missing_required_fields.join(", ")}</p>
          )}
          {result.invalid_fields.length > 0 && <p>Invalid field(s): {result.invalid_fields.join(", ")}</p>}
        </div>
      </div>
    </div>
  );
}
