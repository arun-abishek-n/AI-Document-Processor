import { type ChangeEvent, type DragEvent, useRef, useState } from "react";
import { File as FileIcon, FileImage, FileText, UploadCloud, X } from "lucide-react";
import type { MatchConfig } from "../types";

interface BatchUploadCardProps {
  allowedExtensions: string[];
  maxFileSizeMb: number;
  matchConfigs: MatchConfig[];
  onSubmit: (files: File[], matchConfigId: number) => void;
  disabled?: boolean;
  disabledReason?: string;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function fileIconFor(name: string) {
  const ext = name.split(".").pop()?.toLowerCase();
  if (ext === "pdf") return FileText;
  if (ext === "png" || ext === "jpg" || ext === "jpeg") return FileImage;
  return FileIcon;
}

export function BatchUploadCard({
  allowedExtensions,
  maxFileSizeMb,
  matchConfigs,
  onSubmit,
  disabled,
  disabledReason,
}: BatchUploadCardProps) {
  const [files, setFiles] = useState<File[]>([]);
  const [matchConfigId, setMatchConfigId] = useState<number | "">("");
  const [validationError, setValidationError] = useState<string | null>(null);
  const [isDragActive, setIsDragActive] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const acceptAttr = allowedExtensions.join(",");
  const allowedLabel = allowedExtensions.map((ext) => ext.replace(".", "").toUpperCase()).join(", ");
  const selectedConfig = matchConfigs.find((c) => c.id === matchConfigId);
  const requiredCount = selectedConfig ? (selectedConfig.match_type === "2-way" ? 2 : 3) : null;

  const addFiles = (incoming: FileList | File[]) => {
    const validated: File[] = [];
    for (const file of Array.from(incoming)) {
      const ext = `.${file.name.split(".").pop()?.toLowerCase() ?? ""}`;
      if (!allowedExtensions.includes(ext)) {
        setValidationError(`"${ext}" isn't supported. Allowed types: ${allowedLabel}.`);
        return;
      }
      const sizeMb = file.size / (1024 * 1024);
      if (sizeMb > maxFileSizeMb) {
        setValidationError(`"${file.name}" is ${sizeMb.toFixed(1)} MB, which exceeds the ${maxFileSizeMb} MB limit.`);
        return;
      }
      validated.push(file);
    }
    setValidationError(null);
    setFiles((prev) => [...prev, ...validated]);
  };

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragActive(false);
    if (disabled) return;
    if (event.dataTransfer.files?.length) addFiles(event.dataTransfer.files);
  };

  const handleBrowseChange = (event: ChangeEvent<HTMLInputElement>) => {
    if (event.target.files?.length) addFiles(event.target.files);
    event.target.value = "";
  };

  const canSubmit = matchConfigId !== "" && requiredCount !== null && files.length === requiredCount;

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6 dark:border-slate-800 dark:bg-slate-900">
      <div className="mb-4">
        <label className="text-xs font-medium text-slate-700 dark:text-slate-300">Match configuration</label>
        <select
          value={matchConfigId}
          onChange={(e) => setMatchConfigId(e.target.value ? Number(e.target.value) : "")}
          disabled={disabled}
          className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-white"
        >
          <option value="">Select a configuration…</option>
          {matchConfigs.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name} ({c.match_type})
            </option>
          ))}
        </select>
        {selectedConfig && (
          <p className="mt-1 text-[11px] text-slate-400">
            Upload exactly {requiredCount} documents, in any order — you'll confirm each one's type next.
          </p>
        )}
      </div>

      <div
        onDragOver={(e) => {
          e.preventDefault();
          if (!disabled) setIsDragActive(true);
        }}
        onDragLeave={() => setIsDragActive(false)}
        onDrop={handleDrop}
        onClick={() => !disabled && inputRef.current?.click()}
        role="button"
        tabIndex={disabled ? -1 : 0}
        onKeyDown={(e) => {
          if ((e.key === "Enter" || e.key === " ") && !disabled) inputRef.current?.click();
        }}
        aria-disabled={disabled}
        className={`flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-10 text-center transition-colors ${
          disabled
            ? "cursor-not-allowed border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-slate-900/50"
            : isDragActive
              ? "border-indigo-400 bg-indigo-50 dark:border-indigo-600 dark:bg-indigo-950/40"
              : "border-slate-300 hover:border-indigo-300 hover:bg-slate-50 dark:border-slate-700 dark:hover:border-indigo-700 dark:hover:bg-slate-800/50"
        }`}
      >
        <input ref={inputRef} type="file" multiple accept={acceptAttr} className="hidden" onChange={handleBrowseChange} disabled={disabled} />
        <div className="flex h-11 w-11 items-center justify-center rounded-full bg-indigo-100 text-indigo-600 dark:bg-indigo-950 dark:text-indigo-400">
          <UploadCloud className="h-5 w-5" />
        </div>
        <p className="mt-3 text-sm font-medium text-slate-900 dark:text-white">
          Drag &amp; drop documents, or <span className="text-indigo-600 dark:text-indigo-400">browse</span>
        </p>
        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
          {allowedLabel} &middot; up to {maxFileSizeMb} MB each
        </p>
      </div>

      {files.length > 0 && (
        <div className="mt-4 space-y-2">
          {files.map((file, i) => {
            const Icon = fileIconFor(file.name);
            return (
              <div key={i} className="flex items-center gap-3 rounded-xl border border-slate-200 bg-slate-50 p-2.5 dark:border-slate-800 dark:bg-slate-800/50">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-indigo-100 text-indigo-600 dark:bg-indigo-950 dark:text-indigo-400">
                  <Icon className="h-4 w-4" />
                </div>
                <div className="min-w-0 flex-1 text-left">
                  <p className="truncate text-sm font-medium text-slate-900 dark:text-white">{file.name}</p>
                  <p className="text-xs text-slate-500 dark:text-slate-400">{formatBytes(file.size)}</p>
                </div>
                <button
                  type="button"
                  onClick={() => setFiles((prev) => prev.filter((_, idx) => idx !== i))}
                  aria-label={`Remove ${file.name}`}
                  className="shrink-0 rounded-md p-1.5 text-slate-400 hover:bg-slate-200 hover:text-slate-700 dark:hover:bg-slate-700 dark:hover:text-slate-200"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            );
          })}
        </div>
      )}

      {validationError && (
        <p role="alert" className="mt-3 rounded-lg bg-red-50 px-3 py-2 text-xs font-medium text-red-700 dark:bg-red-950/50 dark:text-red-400">
          {validationError}
        </p>
      )}

      <button
        type="button"
        onClick={() => canSubmit && onSubmit(files, matchConfigId as number)}
        disabled={disabled || !canSubmit}
        className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-lg bg-indigo-600 px-6 py-2.5 text-sm font-semibold text-white shadow-sm shadow-indigo-600/30 transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:bg-slate-300 disabled:shadow-none dark:disabled:bg-slate-700"
      >
        Upload Batch
      </button>
      {requiredCount !== null && files.length !== requiredCount && (
        <p className="mt-2 text-center text-xs text-slate-400">
          {files.length}/{requiredCount} document(s) selected
        </p>
      )}
      {disabled && disabledReason && (
        <p className="mt-2 text-center text-xs font-medium text-amber-600 dark:text-amber-400">{disabledReason}</p>
      )}
    </div>
  );
}
