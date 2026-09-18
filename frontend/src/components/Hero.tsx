import { FileSearch, ScanText, ShieldCheck } from "lucide-react";

const PIPELINE_STEPS = [
  { icon: ScanText, label: "OCR extraction" },
  { icon: FileSearch, label: "Field detection" },
  { icon: ShieldCheck, label: "Validation" },
];

export function Hero() {
  return (
    <section className="mx-auto max-w-3xl px-4 pb-10 pt-14 text-center sm:px-6 sm:pt-20">
      <span className="inline-flex items-center rounded-full border border-indigo-200 bg-indigo-50 px-3 py-1 text-xs font-medium text-indigo-700 dark:border-indigo-900 dark:bg-indigo-950 dark:text-indigo-300">
        Intelligent Document Processing
      </span>

      <h1 className="mt-4 text-3xl font-semibold tracking-tight text-slate-900 sm:text-4xl md:text-5xl dark:text-white">
        Transform documents into
        <span className="text-indigo-600 dark:text-indigo-400"> structured intelligence</span>
      </h1>

      <p className="mx-auto mt-4 max-w-xl text-balance text-sm text-slate-600 sm:text-base dark:text-slate-400">
        Upload an invoice-style PDF or image. The pipeline preprocesses the scan, runs OCR,
        extracts key business fields with confidence scores, validates them, and returns
        structured JSON — in seconds.
      </p>

      <div className="mt-8 flex flex-wrap items-center justify-center gap-x-6 gap-y-3">
        {PIPELINE_STEPS.map(({ icon: Icon, label }) => (
          <div key={label} className="flex items-center gap-2 text-xs font-medium text-slate-500 dark:text-slate-400">
            <Icon className="h-4 w-4 text-indigo-500" />
            {label}
          </div>
        ))}
      </div>
    </section>
  );
}
