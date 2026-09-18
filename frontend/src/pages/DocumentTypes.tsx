import { useEffect, useState } from "react";
import { Plus, Trash2, X } from "lucide-react";
import { Modal } from "../components/Modal";
import {
  createDocumentType,
  deleteDocumentType,
  listDocumentTypes,
  updateDocumentType,
  type DocumentTypeInput,
} from "../lib/api";
import type { DocumentType, DocumentTypeField } from "../types";

const EMPTY_FIELD: DocumentTypeField = { key: "", label: "", pattern: null, is_required: false };

function emptyForm(): DocumentTypeInput {
  return { name: "", description: "", status: "draft", fields: [] };
}

export function DocumentTypes() {
  const [types, setTypes] = useState<DocumentType[]>([]);
  const [error, setError] = useState("");
  const [editing, setEditing] = useState<DocumentType | null>(null);
  const [isCreating, setIsCreating] = useState(false);

  const load = () => listDocumentTypes().then(setTypes).catch(() => setError("Could not load document types."));
  useEffect(() => {
    load();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-white">Document Types</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Each type = a sample layout + description → the fields extracted from it
          </p>
        </div>
        <button
          type="button"
          onClick={() => setIsCreating(true)}
          className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3.5 py-2 text-sm font-medium text-white hover:bg-indigo-500"
        >
          <Plus className="h-4 w-4" /> Add Document Type
        </button>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {types.map((type) => (
          <div key={type.id} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <div className="flex items-start justify-between gap-2">
              <p className="font-semibold text-slate-900 dark:text-white">{type.name}</p>
              <StatusBadge status={type.status} />
            </div>
            <p className="mt-1.5 line-clamp-3 text-xs text-slate-500 dark:text-slate-400">{type.description}</p>
            <div className="mt-3 flex flex-wrap gap-1.5">
              {type.fields.slice(0, 5).map((f) => (
                <span key={f.key} className="rounded-full border border-indigo-200 bg-indigo-50 px-2 py-0.5 text-[11px] font-medium text-indigo-700 dark:border-indigo-900 dark:bg-indigo-950 dark:text-indigo-300">
                  {f.key}
                </span>
              ))}
              {type.fields.length > 5 && (
                <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-500 dark:bg-slate-800 dark:text-slate-400">
                  +{type.fields.length - 5} more
                </span>
              )}
              {type.fields.length === 0 && (
                <span className="text-[11px] text-slate-400">No keys selected yet</span>
              )}
            </div>
            <div className="mt-4 flex gap-2">
              <button
                type="button"
                onClick={() => setEditing(type)}
                className="flex-1 rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
              >
                Edit keys
              </button>
              <button
                type="button"
                onClick={async () => {
                  if (!confirm(`Delete "${type.name}"? This cannot be undone.`)) return;
                  await deleteDocumentType(type.id);
                  load();
                }}
                className="rounded-lg border border-red-200 px-3 py-1.5 text-xs font-medium text-red-600 hover:bg-red-50 dark:border-red-900 dark:hover:bg-red-950/40"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
        ))}
      </div>

      {(isCreating || editing) && (
        <DocumentTypeFormModal
          initial={editing ?? emptyForm()}
          onClose={() => {
            setIsCreating(false);
            setEditing(null);
          }}
          onSaved={() => {
            setIsCreating(false);
            setEditing(null);
            load();
          }}
          editingId={editing?.id}
        />
      )}
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const isConfigured = status === "configured";
  return (
    <span
      className={`shrink-0 rounded-full px-2 py-0.5 text-[11px] font-medium ${
        isConfigured
          ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-400"
          : "bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-400"
      }`}
    >
      {isConfigured ? "Configured" : "Draft"}
    </span>
  );
}

function DocumentTypeFormModal({
  initial,
  editingId,
  onClose,
  onSaved,
}: {
  initial: DocumentTypeInput;
  editingId?: number;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [form, setForm] = useState<DocumentTypeInput>(initial);
  const [error, setError] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  const updateField = (index: number, patch: Partial<DocumentTypeField>) => {
    setForm((f) => ({ ...f, fields: f.fields.map((field, i) => (i === index ? { ...field, ...patch } : field)) }));
  };

  const handleSave = async () => {
    setIsSaving(true);
    setError("");
    try {
      if (editingId) await updateDocumentType(editingId, form);
      else await createDocumentType(form);
      onSaved();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save this document type.");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Modal
      title={editingId ? "Edit Document Type" : "Add Document Type"}
      onClose={onClose}
      widthClassName="max-w-xl"
      footer={
        <>
          <button type="button" onClick={onClose} className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium dark:border-slate-700">
            Cancel
          </button>
          <button
            type="button"
            onClick={handleSave}
            disabled={isSaving || !form.name.trim()}
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:bg-slate-300"
          >
            {isSaving ? "Saving…" : "Save"}
          </button>
        </>
      }
    >
      <div className="space-y-4">
        {error && <p className="rounded-lg bg-red-50 px-3 py-2 text-xs text-red-700 dark:bg-red-950/50 dark:text-red-400">{error}</p>}

        <div>
          <label className="text-xs font-medium text-slate-700 dark:text-slate-300">Name</label>
          <input
            value={form.name}
            onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
            className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-white"
          />
        </div>
        <div>
          <label className="text-xs font-medium text-slate-700 dark:text-slate-300">Description</label>
          <textarea
            value={form.description}
            onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
            rows={2}
            className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-white"
          />
        </div>
        <div>
          <label className="text-xs font-medium text-slate-700 dark:text-slate-300">Status</label>
          <select
            value={form.status}
            onChange={(e) => setForm((f) => ({ ...f, status: e.target.value as "draft" | "configured" }))}
            className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-white"
          >
            <option value="draft">Draft</option>
            <option value="configured">Configured</option>
          </select>
        </div>

        <div>
          <div className="flex items-center justify-between">
            <label className="text-xs font-medium text-slate-700 dark:text-slate-300">Extraction fields</label>
            <button
              type="button"
              onClick={() => setForm((f) => ({ ...f, fields: [...f.fields, { ...EMPTY_FIELD }] }))}
              className="text-xs font-medium text-indigo-600 hover:text-indigo-500"
            >
              + Add field
            </button>
          </div>
          <div className="mt-2 space-y-2">
            {form.fields.map((field, i) => (
              <div key={i} className="flex items-center gap-2 rounded-lg border border-slate-200 p-2 dark:border-slate-800">
                <input
                  placeholder="key (e.g. po_number)"
                  value={field.key}
                  onChange={(e) => updateField(i, { key: e.target.value })}
                  className="w-1/3 rounded-md border border-slate-300 px-2 py-1 text-xs dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                />
                <input
                  placeholder="Label (e.g. PO Number)"
                  value={field.label}
                  onChange={(e) => updateField(i, { label: e.target.value })}
                  className="flex-1 rounded-md border border-slate-300 px-2 py-1 text-xs dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                />
                <label className="flex items-center gap-1 text-[11px] text-slate-500 dark:text-slate-400">
                  <input
                    type="checkbox"
                    checked={field.is_required}
                    onChange={(e) => updateField(i, { is_required: e.target.checked })}
                  />
                  required
                </label>
                <button
                  type="button"
                  onClick={() => setForm((f) => ({ ...f, fields: f.fields.filter((_, idx) => idx !== i) }))}
                  className="text-slate-400 hover:text-red-500"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              </div>
            ))}
            {form.fields.length === 0 && <p className="text-xs text-slate-400">No fields yet — add at least one.</p>}
          </div>
          <p className="mt-1.5 text-[11px] text-slate-400">
            Leave a field's pattern unset to auto-generate one from its key (e.g. a "*_number" key expects a
            "Number"/"No."/"#" label next to it; "*_name" and "*_amount" keys are also recognized).
          </p>
        </div>
      </div>
    </Modal>
  );
}
