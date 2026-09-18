import { type ChangeEvent, type DragEvent, useCallback, useRef, useState } from "react";
import { File as FileIcon, FileImage, FileText, UploadCloud, X } from "lucide-react";

interface UploadCardProps {
  allowedExtensions: string[];
  maxFileSizeMb: number;
  onProcess: (file: File) => void;
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

export function UploadCard({
  allowedExtensions,
  maxFileSizeMb,
  onProcess,
  disabled,
  disabledReason,
}: UploadCardProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [isDragActive, setIsDragActive] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const acceptAttr = allowedExtensions.join(",");
  const allowedLabel = allowedExtensions.map((ext) => ext.replace(".", "").toUpperCase()).join(", ");

  const validateAndSetFile = useCallback(
    (file: File) => {
      const ext = `.${file.name.split(".").pop()?.toLowerCase() ?? ""}`;
      if (!allowedExtensions.includes(ext)) {
        setValidationError(`"${ext}" isn't supported. Allowed types: ${allowedLabel}.`);
        setSelectedFile(null);
        return;
      }
      const sizeMb = file.size / (1024 * 1024);
      if (sizeMb > maxFileSizeMb) {
        setValidationError(`File is ${sizeMb.toFixed(1)} MB, which exceeds the ${maxFileSizeMb} MB limit.`);
        setSelectedFile(null);
        return;
      }
      setValidationError(null);
      setSelectedFile(file);
    },
    [allowedExtensions, allowedLabel, maxFileSizeMb],
  );

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragActive(false);
    if (disabled) return;
    const file = event.dataTransfer.files?.[0];
    if (file) validateAndSetFile(file);
  };

  const handleBrowseChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) validateAndSetFile(file);
    event.target.value = ""; // allow re-selecting the same file after removal
  };

  const FileTypeIcon = selectedFile ? fileIconFor(selectedFile.name) : UploadCloud;

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6 dark:border-slate-800 dark:bg-slate-900">
      {!selectedFile ? (
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
          className={`flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-14 text-center transition-colors ${
            disabled
              ? "cursor-not-allowed border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-slate-900/50"
              : isDragActive
                ? "border-indigo-400 bg-indigo-50 dark:border-indigo-600 dark:bg-indigo-950/40"
                : "border-slate-300 hover:border-indigo-300 hover:bg-slate-50 dark:border-slate-700 dark:hover:border-indigo-700 dark:hover:bg-slate-800/50"
          }`}
        >
          <input
            ref={inputRef}
            type="file"
            accept={acceptAttr}
            className="hidden"
            onChange={handleBrowseChange}
            disabled={disabled}
          />
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-indigo-100 text-indigo-600 dark:bg-indigo-950 dark:text-indigo-400">
            <UploadCloud className="h-6 w-6" />
          </div>
          <p className="mt-4 text-sm font-medium text-slate-900 dark:text-white">
            Drag &amp; drop a document, or <span className="text-indigo-600 dark:text-indigo-400">browse</span>
          </p>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            {allowedLabel} &middot; up to {maxFileSizeMb} MB
          </p>
          {disabled && disabledReason && (
            <p className="mt-3 text-xs font-medium text-amber-600 dark:text-amber-400">{disabledReason}</p>
          )}
        </div>
      ) : (
        <div className="flex flex-col items-center gap-5 py-6">
          <div className="flex w-full max-w-sm items-center gap-3 rounded-xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-800/50">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-indigo-100 text-indigo-600 dark:bg-indigo-950 dark:text-indigo-400">
              <FileTypeIcon className="h-5 w-5" />
            </div>
            <div className="min-w-0 flex-1 text-left">
              <p className="truncate text-sm font-medium text-slate-900 dark:text-white">{selectedFile.name}</p>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                {selectedFile.type || "unknown type"} &middot; {formatBytes(selectedFile.size)}
              </p>
            </div>
            <button
              type="button"
              onClick={() => setSelectedFile(null)}
              aria-label="Remove file"
              className="shrink-0 rounded-md p-1.5 text-slate-400 transition hover:bg-slate-200 hover:text-slate-700 dark:hover:bg-slate-700 dark:hover:text-slate-200"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          <button
            type="button"
            onClick={() => onProcess(selectedFile)}
            disabled={disabled}
            className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-6 py-2.5 text-sm font-semibold text-white shadow-sm shadow-indigo-600/30 transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:bg-slate-300 disabled:shadow-none dark:disabled:bg-slate-700"
          >
            Process Document
          </button>
          {disabled && disabledReason && (
            <p className="text-xs font-medium text-amber-600 dark:text-amber-400">{disabledReason}</p>
          )}
        </div>
      )}

      {validationError && (
        <p role="alert" className="mt-3 rounded-lg bg-red-50 px-3 py-2 text-xs font-medium text-red-700 dark:bg-red-950/50 dark:text-red-400">
          {validationError}
        </p>
      )}
    </div>
  );
}
