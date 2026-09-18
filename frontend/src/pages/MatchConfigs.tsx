import { useEffect, useState } from "react";
import { ChevronDown, ChevronUp, Plus, Trash2, X } from "lucide-react";
import { Modal } from "../components/Modal";
import {
  createMatchConfig,
  deleteMatchConfig,
  listDocumentTypes,
  listMatchConfigs,
  updateMatchConfig,
  type MatchConfigInput,
} from "../lib/api";
import type { Comparison, DocumentType, MatchConfig, MatchRule } from "../types";

function emptyForm(): MatchConfigInput {
  return { name: "", match_type: "2-way", is_active: true, document_type_ids: [], rules: [] };
}

const COMPARISONS: { value: Comparison; label: string }[] = [
  { value: "equals", label: "Equals (text match)" },
  { value: "numeric_tolerance", label: "Numeric, within tolerance %" },
  { value: "date_equals", label: "Same date" },
];

export function MatchConfigs() {
  const [configs, setConfigs] = useState<MatchConfig[]>([]);
  const [docTypes, setDocTypes] = useState<DocumentType[]>([]);
  const [expanded, setExpanded] = useState<number | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [editing, setEditing] = useState<MatchConfig | null>(null);
  const [error, setError] = useState("");

  const load = () => {
    listMatchConfigs().then(setConfigs).catch(() => setError("Could not load match configurations."));
    listDocumentTypes().then(setDocTypes).catch(() => {});
  };
  useEffect(load, []);

  const docTypeName = (id: number) => docTypes.find((d) => d.id === id)?.name ?? `#${id}`;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-white">Match Configurations</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Named rule bundles — pick 2-4 document types per configuration, choose one per batch
          </p>
        </div>
        <button
          type="button"
          onClick={() => setIsCreating(true)}
          disabled={docTypes.length < 2}
          className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3.5 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:bg-slate-300"
        >
          <Plus className="h-4 w-4" /> New configuration
        </button>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="space-y-3">
        {configs.map((config) => (
          <div key={config.id} className="rounded-2xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
            <button
              type="button"
              onClick={() => setExpanded(expanded === config.id ? null : config.id)}
              className="flex w-full items-center justify-between px-5 py-4 text-left"
            >
              <div className="flex items-center gap-3">
                <span className="font-semibold text-slate-900 dark:text-white">{config.name}</span>
                <span className="rounded-full border border-indigo-200 bg-indigo-50 px-2 py-0.5 text-[11px] font-medium text-indigo-700 dark:border-indigo-900 dark:bg-indigo-950 dark:text-indigo-300">
                  {config.match_type}
                </span>
                {config.document_types.map((dt) => (
                  <span key={dt.document_type_id} className="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                    {docTypeName(dt.document_type_id)}
                  </span>
                ))}
                {!config.is_active && <span className="text-[11px] font-medium text-amber-600">inactive</span>}
              </div>
              <div className="flex items-center gap-3 text-xs text-slate-400">
                {config.rules.length} rules
                {expanded === config.id ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
              </div>
            </button>

            {expanded === config.id && (
              <div className="border-t border-slate-200 px-5 py-4 dark:border-slate-800">
                <table className="w-full text-left text-xs">
                  <thead className="text-slate-400">
                    <tr>
                      <th className="pb-2 font-medium">Rule</th>
                      <th className="pb-2 font-medium">Comparison</th>
                      <th className="pb-2 font-medium">Field mapping</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                    {config.rules.map((rule) => (
                      <tr key={rule.id}>
                        <td className="py-2 font-medium text-slate-800 dark:text-slate-200">{rule.name}</td>
                        <td className="py-2 text-slate-500 dark:text-slate-400">
                          {rule.comparison}
                          {rule.comparison === "numeric_tolerance" && rule.tolerance_percent != null && ` (±${rule.tolerance_percent}%)`}
                        </td>
                        <td className="py-2 text-slate-500 dark:text-slate-400">
                          {Object.entries(rule.field_map)
                            .map(([docTypeId, key]) => `${docTypeName(Number(docTypeId))}.${key}`)
                            .join("  =  ")}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <div className="mt-3 flex gap-2">
                  <button
                    type="button"
                    onClick={() => setEditing(config)}
                    className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
                  >
                    Edit
                  </button>
                  <button
                    type="button"
                    onClick={async () => {
                      if (!confirm(`Delete "${config.name}"?`)) return;
                      await deleteMatchConfig(config.id);
                      load();
                    }}
                    className="rounded-lg border border-red-200 px-3 py-1.5 text-xs font-medium text-red-600 hover:bg-red-50 dark:border-red-900 dark:hover:bg-red-950/40"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {(isCreating || editing) && (
        <MatchConfigFormModal
          docTypes={docTypes}
          initial={
            editing
              ? {
                  name: editing.name,
                  match_type: editing.match_type,
                  is_active: editing.is_active,
                  document_type_ids: editing.document_types.map((d) => d.document_type_id),
                  rules: editing.rules,
                }
              : emptyForm()
          }
          editingId={editing?.id}
          onClose={() => {
            setIsCreating(false);
            setEditing(null);
          }}
          onSaved={() => {
            setIsCreating(false);
            setEditing(null);
            load();
          }}
        />
      )}
    </div>
  );
}

function MatchConfigFormModal({
  docTypes,
  initial,
  editingId,
  onClose,
  onSaved,
}: {
  docTypes: DocumentType[];
  initial: MatchConfigInput;
  editingId?: number;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [form, setForm] = useState<MatchConfigInput>(initial);
  const [error, setError] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  const requiredCount = form.match_type === "2-way" ? 2 : 3;

  const toggleDocType = (id: number) => {
    setForm((f) => {
      const already = f.document_type_ids.includes(id);
      if (already) return { ...f, document_type_ids: f.document_type_ids.filter((x) => x !== id) };
      if (f.document_type_ids.length >= requiredCount) return f;
      return { ...f, document_type_ids: [...f.document_type_ids, id] };
    });
  };

  const addRule = () => {
    const rule: MatchRule = {
      name: "",
      comparison: "equals",
      tolerance_percent: null,
      field_map: Object.fromEntries(form.document_type_ids.map((id) => [String(id), ""])),
    };
    setForm((f) => ({ ...f, rules: [...f.rules, rule] }));
  };

  const updateRule = (index: number, patch: Partial<MatchRule>) => {
    setForm((f) => ({ ...f, rules: f.rules.map((r, i) => (i === index ? { ...r, ...patch } : r)) }));
  };

  const handleSave = async () => {
    if (form.document_type_ids.length !== requiredCount) {
      setError(`Select exactly ${requiredCount} document types for a ${form.match_type} configuration.`);
      return;
    }
    setIsSaving(true);
    setError("");
    try {
      if (editingId) await updateMatchConfig(editingId, form);
      else await createMatchConfig(form);
      onSaved();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save this configuration.");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Modal
      title={editingId ? "Edit Match Configuration" : "New Match Configuration"}
      onClose={onClose}
      widthClassName="max-w-2xl"
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

        <div className="flex gap-3">
          <div className="flex-1">
            <label className="text-xs font-medium text-slate-700 dark:text-slate-300">Name</label>
            <input
              value={form.name}
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-white"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-slate-700 dark:text-slate-300">Match type</label>
            <select
              value={form.match_type}
              onChange={(e) =>
                setForm((f) => ({ ...f, match_type: e.target.value as "2-way" | "3-way", document_type_ids: [] }))
              }
              className="mt-1 rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-white"
            >
              <option value="2-way">2-way</option>
              <option value="3-way">3-way</option>
            </select>
          </div>
        </div>

        <div>
          <label className="text-xs font-medium text-slate-700 dark:text-slate-300">
            Document types ({form.document_type_ids.length}/{requiredCount} selected, in order)
          </label>
          <div className="mt-1.5 flex flex-wrap gap-1.5">
            {docTypes.map((dt) => {
              const selected = form.document_type_ids.includes(dt.id);
              return (
                <button
                  key={dt.id}
                  type="button"
                  onClick={() => toggleDocType(dt.id)}
                  className={`rounded-full px-3 py-1 text-xs font-medium ${
                    selected
                      ? "bg-indigo-600 text-white"
                      : "border border-slate-300 text-slate-600 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
                  }`}
                >
                  {dt.name}
                </button>
              );
            })}
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between">
            <label className="text-xs font-medium text-slate-700 dark:text-slate-300">Rules</label>
            <button
              type="button"
              onClick={addRule}
              disabled={form.document_type_ids.length !== requiredCount}
              className="text-xs font-medium text-indigo-600 hover:text-indigo-500 disabled:text-slate-300"
            >
              + Add rule
            </button>
          </div>

          <div className="mt-2 space-y-2">
            {form.rules.map((rule, i) => (
              <div key={i} className="rounded-lg border border-slate-200 p-2.5 dark:border-slate-800">
                <div className="flex items-center gap-2">
                  <input
                    placeholder="Rule name (e.g. PO Number)"
                    value={rule.name}
                    onChange={(e) => updateRule(i, { name: e.target.value })}
                    className="flex-1 rounded-md border border-slate-300 px-2 py-1 text-xs dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                  />
                  <select
                    value={rule.comparison}
                    onChange={(e) => updateRule(i, { comparison: e.target.value as Comparison })}
                    className="rounded-md border border-slate-300 px-2 py-1 text-xs dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                  >
                    {COMPARISONS.map((c) => (
                      <option key={c.value} value={c.value}>
                        {c.label}
                      </option>
                    ))}
                  </select>
                  {rule.comparison === "numeric_tolerance" && (
                    <input
                      type="number"
                      placeholder="tolerance %"
                      value={rule.tolerance_percent ?? ""}
                      onChange={(e) => updateRule(i, { tolerance_percent: e.target.value ? Number(e.target.value) : null })}
                      className="w-24 rounded-md border border-slate-300 px-2 py-1 text-xs dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                    />
                  )}
                  <button
                    type="button"
                    onClick={() => setForm((f) => ({ ...f, rules: f.rules.filter((_, idx) => idx !== i) }))}
                    className="text-slate-400 hover:text-red-500"
                  >
                    <X className="h-3.5 w-3.5" />
                  </button>
                </div>
                <div className="mt-2 grid grid-cols-2 gap-2 sm:grid-cols-3">
                  {form.document_type_ids.map((docTypeId) => (
                    <div key={docTypeId}>
                      <p className="text-[11px] text-slate-400">{docTypes.find((d) => d.id === docTypeId)?.name}</p>
                      <input
                        placeholder="field key"
                        value={rule.field_map[String(docTypeId)] ?? ""}
                        onChange={(e) =>
                          updateRule(i, { field_map: { ...rule.field_map, [String(docTypeId)]: e.target.value } })
                        }
                        className="mt-0.5 w-full rounded-md border border-slate-300 px-2 py-1 text-xs dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                      />
                    </div>
                  ))}
                </div>
              </div>
            ))}
            {form.rules.length === 0 && (
              <p className="text-xs text-slate-400">
                {form.document_type_ids.length === requiredCount
                  ? "No rules yet — add at least one to compare fields across documents."
                  : `Select ${requiredCount} document types above first.`}
              </p>
            )}
          </div>
        </div>
      </div>
    </Modal>
  );
}
