import { Code2, FileStack } from "lucide-react";

interface HeaderProps {
  backendStatus: "checking" | "online" | "offline";
}

const REPO_URL = "https://github.com/arun-abishek-n/AI-Document-Processor";

export function Header({ backendStatus }: HeaderProps) {
  return (
    <header className="sticky top-0 z-20 border-b border-slate-200/80 bg-white/80 backdrop-blur-md dark:border-slate-800/80 dark:bg-slate-950/80">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3 sm:px-6">
        <div className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-600 text-white shadow-sm shadow-indigo-600/30">
            <FileStack className="h-5 w-5" strokeWidth={2.25} />
          </div>
          <div className="leading-tight">
            <p className="text-sm font-semibold tracking-tight text-slate-900 dark:text-white">
              AI Smart Document Processing
            </p>
            <p className="text-[11px] font-medium text-slate-500 dark:text-slate-400">
              OCR &middot; Extraction &middot; Validation
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <StatusBadge status={backendStatus} />
          <a
            href={REPO_URL}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1.5 rounded-md border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-700 transition hover:border-slate-300 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
          >
            <Code2 className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Source</span>
          </a>
        </div>
      </div>
    </header>
  );
}

function StatusBadge({ status }: { status: HeaderProps["backendStatus"] }) {
  const config = {
    checking: { dot: "bg-slate-400 animate-pulse", label: "Checking API…", text: "text-slate-500 dark:text-slate-400" },
    online: { dot: "bg-emerald-500", label: "API online", text: "text-emerald-700 dark:text-emerald-400" },
    offline: { dot: "bg-red-500", label: "API unreachable", text: "text-red-700 dark:text-red-400" },
  }[status];

  return (
    <div className={`hidden items-center gap-1.5 text-xs font-medium sm:flex ${config.text}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${config.dot}`} />
      {config.label}
    </div>
  );
}
