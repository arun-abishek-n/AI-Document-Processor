import { Clock, FileType, Layers, ScanText } from "lucide-react";
import type { ProcessResponse } from "../types";

interface OverviewCardsProps {
  result: ProcessResponse;
}

export function OverviewCards({ result }: OverviewCardsProps) {
  const cards = [
    { icon: FileType, label: "File type", value: result.file_type.toUpperCase() },
    { icon: Layers, label: "Pages", value: String(result.page_count) },
    { icon: Clock, label: "Processing time", value: `${result.processing_time_seconds}s` },
    { icon: ScanText, label: "OCR engine", value: result.ocr_engine },
  ];

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      {cards.map(({ icon: Icon, label, value }) => (
        <div
          key={label}
          className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900"
        >
          <Icon className="h-4 w-4 text-indigo-500" />
          <p className="mt-2 truncate text-sm font-semibold text-slate-900 dark:text-white">{value}</p>
          <p className="text-xs text-slate-500 dark:text-slate-400">{label}</p>
        </div>
      ))}
    </div>
  );
}
