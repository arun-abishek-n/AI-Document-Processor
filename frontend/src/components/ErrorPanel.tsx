import { AlertTriangle, RotateCcw } from "lucide-react";

interface ErrorPanelProps {
  message: string;
  onRetry: () => void;
}

export function ErrorPanel({ message, onRetry }: ErrorPanelProps) {
  return (
    <div className="rounded-2xl border border-red-200 bg-red-50 p-6 text-center shadow-sm sm:p-8 dark:border-red-900/60 dark:bg-red-950/30">
      <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-red-100 text-red-600 dark:bg-red-950 dark:text-red-400">
        <AlertTriangle className="h-7 w-7" />
      </div>
      <p className="mt-4 text-sm font-semibold text-red-900 dark:text-red-300">Processing failed</p>
      <p className="mx-auto mt-2 max-w-md text-sm text-red-700 dark:text-red-400">{message}</p>
      <button
        type="button"
        onClick={onRetry}
        className="mx-auto mt-5 inline-flex items-center gap-2 rounded-lg border border-red-300 bg-white px-4 py-2 text-sm font-medium text-red-700 transition hover:bg-red-50 dark:border-red-800 dark:bg-transparent dark:text-red-300 dark:hover:bg-red-950/50"
      >
        <RotateCcw className="h-4 w-4" />
        Try again
      </button>
    </div>
  );
}
