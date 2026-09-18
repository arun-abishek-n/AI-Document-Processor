import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { CheckCircle2, Loader2, XCircle } from "lucide-react";
import { BatchUploadCard } from "../components/BatchUploadCard";
import { ErrorPanel } from "../components/ErrorPanel";
import {
  assignDocumentType,
  checkHealth,
  createBatch,
  listBatches,
  listDocumentTypes,
  listMatchConfigs,
  matchBatch,
} from "../lib/api";
import type { Batch, BatchDetail, DocumentType, HealthResponse, MatchConfig } from "../types";

type Stage = "idle" | "uploading" | "confirming" | "matching" | "error";

function relativeTime(iso: string): string {
  const hours = Math.floor((Date.now() - new Date(iso).getTime()) / (1000 * 60 * 60));
  if (hours < 1) return "just now";
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

const STATUS_STYLES: Record<string, string> = {
  pending_confirmation: "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300",
  matching: "bg-indigo-50 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300",
  matched: "bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-400",
  exception: "bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-400",
  failed: "bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-400",
};

export function Process() {
  const navigate = useNavigate();
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [matchConfigs, setMatchConfigs] = useState<MatchConfig[]>([]);
  const [docTypes, setDocTypes] = useState<DocumentType[]>([]);
  const [batches, setBatches] = useState<Batch[]>([]);
  const [stage, setStage] = useState<Stage>("idle");
  const [pendingBatch, setPendingBatch] = useState<BatchDetail | null>(null);
  const [errorMessage, setErrorMessage] = useState("");

  const loadBatches = () => listBatches().then(setBatches).catch(() => {});

  useEffect(() => {
    checkHealth().then(setHealth).catch(() => {});
    listMatchConfigs().then(setMatchConfigs).catch(() => {});
    listDocumentTypes().then(setDocTypes).catch(() => {});
    loadBatches();
  }, []);

  const handleUpload = async (files: File[], matchConfigId: number) => {
    setStage("uploading");
    setErrorMessage("");
    try {
      const batch = await createBatch(files, matchConfigId, () => {});
      setPendingBatch(batch);
      setStage("confirming");
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Could not upload this batch.");
      setStage("error");
    }
  };

  const handleAssign = async (docId: number, documentTypeId: number) => {
    if (!pendingBatch) return;
    const updated = await assignDocumentType(pendingBatch.id, docId, documentTypeId);
    setPendingBatch(updated);
  };

  const handleRunMatch = async () => {
    if (!pendingBatch) return;
    setStage("matching");
    try {
      await matchBatch(pendingBatch.id);
      setPendingBatch(null);
      setStage("idle");
      loadBatches();
      navigate(`/process/${pendingBatch.id}`);
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Matching failed.");
      setStage("error");
    }
  };

  const reset = () => {
    setStage("idle");
    setPendingBatch(null);
    setErrorMessage("");
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-white">Process</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">Upload document batches — classified, extracted, and matched with your configs</p>
        </div>
      </div>

      {stage === "idle" && health && (
        <BatchUploadCard
          allowedExtensions={health.allowed_extensions}
          maxFileSizeMb={health.max_file_size_mb}
          matchConfigs={matchConfigs}
          onSubmit={handleUpload}
          disabled={matchConfigs.length === 0}
          disabledReason={matchConfigs.length === 0 ? "No match configurations yet — ask an admin/manager to create one." : undefined}
        />
      )}

      {stage === "uploading" && (
        <div className="rounded-2xl border border-slate-200 bg-white p-8 text-center dark:border-slate-800 dark:bg-slate-900">
          <Loader2 className="mx-auto h-6 w-6 animate-spin text-indigo-600" />
          <p className="mt-3 text-sm font-medium text-slate-900 dark:text-white">Uploading &amp; extracting…</p>
          <p className="text-xs text-slate-500 dark:text-slate-400">Running OCR and field extraction on each document.</p>
        </div>
      )}

      {stage === "confirming" && pendingBatch && (
        <ConfirmationPanel
          batch={pendingBatch}
          docTypes={docTypes}
          onAssign={handleAssign}
          onRunMatch={handleRunMatch}
          onCancel={reset}
        />
      )}

      {stage === "matching" && (
        <div className="rounded-2xl border border-slate-200 bg-white p-8 text-center dark:border-slate-800 dark:bg-slate-900">
          <Loader2 className="mx-auto h-6 w-6 animate-spin text-indigo-600" />
          <p className="mt-3 text-sm font-medium text-slate-900 dark:text-white">Running matching rules…</p>
        </div>
      )}

      {stage === "error" && <ErrorPanel message={errorMessage} onRetry={reset} />}

      <div>
        <h2 className="mb-3 text-sm font-semibold text-slate-900 dark:text-white">Batch history</h2>
        <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500 dark:border-slate-800 dark:text-slate-400">
              <tr>
                <th className="px-4 py-3 font-medium">Batch</th>
                <th className="px-4 py-3 font-medium">Config</th>
                <th className="px-4 py-3 font-medium">Confidence</th>
                <th className="px-4 py-3 font-medium">Match</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Received</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {batches.map((batch) => (
                <tr
                  key={batch.id}
                  onClick={() => navigate(`/process/${batch.id}`)}
                  className="cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800/50"
                >
                  <td className="px-4 py-3">
                    <p className="font-medium text-slate-900 dark:text-white">{batch.name}</p>
                    <p className="text-xs text-slate-400">{batch.document_count} file(s)</p>
                  </td>
                  <td className="px-4 py-3 text-slate-500 dark:text-slate-400">{batch.match_config_name ?? "—"}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <div className="h-1.5 w-16 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
                        <div
                          className={`h-full rounded-full ${batch.overall_confidence >= 0.85 ? "bg-emerald-500" : batch.overall_confidence >= 0.6 ? "bg-amber-500" : "bg-red-500"}`}
                          style={{ width: `${Math.round(batch.overall_confidence * 100)}%` }}
                        />
                      </div>
                      <span className="text-xs text-slate-500 dark:text-slate-400">{Math.round(batch.overall_confidence * 100)}%</span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    {batch.match_passed === null ? (
                      <span className="text-slate-300">—</span>
                    ) : batch.match_passed ? (
                      <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                    ) : (
                      <XCircle className="h-4 w-4 text-red-500" />
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`rounded-full px-2 py-0.5 text-[11px] font-medium ${STATUS_STYLES[batch.status] ?? ""}`}>
                      {batch.status.replace("_", " ")}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-400">{relativeTime(batch.created_at)}</td>
                </tr>
              ))}
              {batches.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-4 py-10 text-center text-sm text-slate-400">
                    No batches yet — upload one above to get started.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function ConfirmationPanel({
  batch,
  docTypes,
  onAssign,
  onRunMatch,
  onCancel,
}: {
  batch: BatchDetail;
  docTypes: DocumentType[];
  onAssign: (docId: number, documentTypeId: number) => Promise<void>;
  onRunMatch: () => void;
  onCancel: () => void;
}) {
  const allAssigned = batch.documents.every((d) => d.document_type_id !== null);

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <p className="text-sm font-semibold text-slate-900 dark:text-white">Confirm document types</p>
      <p className="text-xs text-slate-500 dark:text-slate-400">
        Each file's type was auto-suggested from its extracted text. Review and correct any before matching.
      </p>

      <div className="mt-4 space-y-2">
        {batch.documents.map((doc) => (
          <div key={doc.id} className="flex items-center gap-3 rounded-xl border border-slate-200 p-3 dark:border-slate-800">
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-slate-900 dark:text-white">{doc.original_filename}</p>
              <p className="text-xs text-slate-400">
                {doc.suggested_document_type_name
                  ? `Suggested: ${doc.suggested_document_type_name}`
                  : "No suggestion — pick one manually"}{" "}
                &middot; {Math.round(doc.overall_confidence * 100)}% OCR confidence
              </p>
            </div>
            <select
              value={doc.document_type_id ?? ""}
              onChange={(e) => onAssign(doc.id, Number(e.target.value))}
              className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-white"
            >
              <option value="" disabled>
                Select type…
              </option>
              {docTypes.map((dt) => (
                <option key={dt.id} value={dt.id}>
                  {dt.name}
                </option>
              ))}
            </select>
          </div>
        ))}
      </div>

      <div className="mt-4 flex justify-end gap-2">
        <button type="button" onClick={onCancel} className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium dark:border-slate-700">
          Cancel
        </button>
        <button
          type="button"
          onClick={onRunMatch}
          disabled={!allAssigned}
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-500 disabled:bg-slate-300"
        >
          Run Matching
        </button>
      </div>
    </div>
  );
}
