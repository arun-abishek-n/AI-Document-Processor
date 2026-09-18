import { Loader2, UploadCloud } from "lucide-react";

interface ProcessingPanelProps {
  stage: "uploading" | "processing";
  fileName: string;
  uploadProgress: number;
  elapsedSeconds: number;
}

/**
 * Two honest states, not fabricated fine-grained ones: real upload progress
 * (from the browser's XHR progress event) while the file is in flight, then
 * a single "processing" state with an elapsed-time counter while the server
 * runs OCR + extraction + validation. The API is one request/response, so
 * there's no real signal for finer-grained steps — showing fake per-step
 * percentages would misrepresent what the server is actually doing.
 */
export function ProcessingPanel({ stage, fileName, uploadProgress, elapsedSeconds }: ProcessingPanelProps) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8 dark:border-slate-800 dark:bg-slate-900">
      <div className="flex flex-col items-center text-center">
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-indigo-100 text-indigo-600 dark:bg-indigo-950 dark:text-indigo-400">
          {stage === "uploading" ? (
            <UploadCloud className="h-7 w-7" />
          ) : (
            <Loader2 className="h-7 w-7 animate-spin" />
          )}
        </div>

        <p className="mt-4 text-sm font-semibold text-slate-900 dark:text-white">
          {stage === "uploading" ? "Uploading document…" : "Processing document…"}
        </p>
        <p className="mt-1 max-w-xs truncate text-xs text-slate-500 dark:text-slate-400">{fileName}</p>

        {stage === "uploading" ? (
          <div className="mt-5 w-full max-w-xs">
            <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
              <div
                className="h-full rounded-full bg-indigo-600 transition-[width] duration-150"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
            <p className="mt-2 text-xs font-medium text-slate-500 dark:text-slate-400">{uploadProgress}%</p>
          </div>
        ) : (
          <div className="mt-5 w-full max-w-sm">
            <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
              <div className="h-full w-1/3 animate-[indeterminate_1.4s_ease-in-out_infinite] rounded-full bg-indigo-600" />
            </div>
            <p className="mt-3 text-xs text-slate-500 dark:text-slate-400">
              Running OCR, field extraction, and validation on the server —{" "}
              <span className="font-medium text-slate-700 dark:text-slate-300">{elapsedSeconds}s</span> elapsed.
            </p>
            <p className="mt-1 text-[11px] text-slate-400 dark:text-slate-500">
              Larger scans and multi-page PDFs take longer.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
