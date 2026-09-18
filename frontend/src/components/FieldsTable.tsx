import { Check, X } from "lucide-react";
import type { FieldResult } from "../types";

interface FieldsTableProps {
  fields: Record<string, FieldResult>;
}

function humanizeFieldName(name: string): string {
  return name.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function confidenceClasses(confidence: number, isPresent: boolean): string {
  if (!isPresent) return "text-slate-400 dark:text-slate-600";
  if (confidence >= 0.85) return "text-emerald-600 dark:text-emerald-400";
  if (confidence >= 0.6) return "text-amber-600 dark:text-amber-400";
  return "text-red-600 dark:text-red-400";
}

export function FieldsTable({ fields }: FieldsTableProps) {
  const entries = Object.entries(fields);

  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[560px] text-left text-sm">
          <thead>
            <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500 dark:border-slate-800 dark:text-slate-400">
              <th className="px-4 py-3 font-medium">Field</th>
              <th className="px-4 py-3 font-medium">Value</th>
              <th className="px-4 py-3 font-medium">Confidence</th>
              <th className="px-4 py-3 font-medium">Valid</th>
              <th className="px-4 py-3 font-medium">Issue</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
            {entries.map(([name, field]) => (
              <tr key={name} className="text-slate-700 dark:text-slate-300">
                <td className="px-4 py-3 font-medium text-slate-900 dark:text-white">{humanizeFieldName(name)}</td>
                <td className="max-w-[220px] truncate px-4 py-3" title={field.value ?? undefined}>
                  {field.value ?? <span className="text-slate-400 dark:text-slate-600">—</span>}
                </td>
                <td className={`px-4 py-3 font-medium tabular-nums ${confidenceClasses(field.confidence, field.is_present)}`}>
                  {field.is_present ? `${Math.round(field.confidence * 100)}%` : "—"}
                </td>
                <td className="px-4 py-3">
                  {field.is_valid ? (
                    <Check className="h-4 w-4 text-emerald-500" />
                  ) : (
                    <X className="h-4 w-4 text-red-500" />
                  )}
                </td>
                <td className="px-4 py-3 text-xs text-slate-500 dark:text-slate-400">{field.issue ?? ""}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
