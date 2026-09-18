import { useEffect, useState } from "react";
import { Plus } from "lucide-react";
import { Modal } from "../components/Modal";
import { createUser, listUsers, updateUser } from "../lib/api";
import type { Role, User } from "../types";

const ROLES: Role[] = ["admin", "manager", "executive"];

function formatLastActive(value: string | null): string {
  if (!value) return "Never";
  const diffMs = Date.now() - new Date(value).getTime();
  const hours = Math.floor(diffMs / (1000 * 60 * 60));
  if (hours < 1) return "Just now";
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

export function Users() {
  const [users, setUsers] = useState<User[]>([]);
  const [error, setError] = useState("");
  const [isCreating, setIsCreating] = useState(false);

  const load = () => listUsers().then(setUsers).catch(() => setError("Could not load users."));
  useEffect(() => {
    load();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-white">Users</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">Demo accounts for this project</p>
        </div>
        <button
          type="button"
          onClick={() => setIsCreating(true)}
          className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3.5 py-2 text-sm font-medium text-white hover:bg-indigo-500"
        >
          <Plus className="h-4 w-4" /> Add User
        </button>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500 dark:border-slate-800 dark:text-slate-400">
            <tr>
              <th className="px-4 py-3 font-medium">Name</th>
              <th className="px-4 py-3 font-medium">Username</th>
              <th className="px-4 py-3 font-medium">Role</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">Last active</th>
              <th className="px-4 py-3 font-medium"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
            {users.map((user) => (
              <tr key={user.id}>
                <td className="px-4 py-3 font-medium text-slate-900 dark:text-white">{user.name}</td>
                <td className="px-4 py-3 text-slate-500 dark:text-slate-400">{user.username}</td>
                <td className="px-4 py-3">
                  <select
                    value={user.role}
                    onChange={async (e) => {
                      await updateUser(user.id, { role: e.target.value });
                      load();
                    }}
                    className="rounded-md border border-slate-300 px-2 py-1 text-xs capitalize dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                  >
                    {ROLES.map((r) => (
                      <option key={r} value={r}>
                        {r}
                      </option>
                    ))}
                  </select>
                </td>
                <td className="px-4 py-3">
                  <button
                    type="button"
                    onClick={async () => {
                      await updateUser(user.id, { is_active: !user.is_active });
                      load();
                    }}
                    className={`rounded-full px-2 py-0.5 text-[11px] font-medium ${
                      user.is_active
                        ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-400"
                        : "bg-slate-100 text-slate-500 dark:bg-slate-800"
                    }`}
                  >
                    {user.is_active ? "Active" : "Disabled"}
                  </button>
                </td>
                <td className="px-4 py-3 text-xs text-slate-500 dark:text-slate-400">{formatLastActive(user.last_active_at)}</td>
                <td className="px-4 py-3"></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {isCreating && (
        <CreateUserModal
          onClose={() => setIsCreating(false)}
          onCreated={() => {
            setIsCreating(false);
            load();
          }}
        />
      )}
    </div>
  );
}

function CreateUserModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [role, setRole] = useState<Role>("executive");
  const [error, setError] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  const handleSave = async () => {
    setIsSaving(true);
    setError("");
    try {
      await createUser({ username, password, name, role });
      onCreated();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create user.");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Modal
      title="Add User"
      onClose={onClose}
      footer={
        <>
          <button type="button" onClick={onClose} className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium dark:border-slate-700">
            Cancel
          </button>
          <button
            type="button"
            onClick={handleSave}
            disabled={isSaving || !username || !password || !name}
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:bg-slate-300"
          >
            {isSaving ? "Saving…" : "Create"}
          </button>
        </>
      }
    >
      <div className="space-y-3">
        {error && <p className="rounded-lg bg-red-50 px-3 py-2 text-xs text-red-700 dark:bg-red-950/50 dark:text-red-400">{error}</p>}
        <Input label="Full name" value={name} onChange={setName} />
        <Input label="Username" value={username} onChange={setUsername} />
        <Input label="Password" value={password} onChange={setPassword} type="password" />
        <div>
          <label className="text-xs font-medium text-slate-700 dark:text-slate-300">Role</label>
          <select
            value={role}
            onChange={(e) => setRole(e.target.value as Role)}
            className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm capitalize dark:border-slate-700 dark:bg-slate-800 dark:text-white"
          >
            {ROLES.map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </select>
        </div>
      </div>
    </Modal>
  );
}

function Input({
  label,
  value,
  onChange,
  type = "text",
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
}) {
  return (
    <div>
      <label className="text-xs font-medium text-slate-700 dark:text-slate-300">{label}</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-white"
      />
    </div>
  );
}
