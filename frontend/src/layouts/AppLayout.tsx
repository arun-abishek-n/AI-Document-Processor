import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";
import {
  Activity,
  FileStack,
  FileText,
  GitCompareArrows,
  LayoutGrid,
  LogOut,
  Users as UsersIcon,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import type { Role } from "../types";

interface NavItem {
  to: string;
  label: string;
  icon: typeof LayoutGrid;
  roles: Role[];
  section: "configure" | "run";
}

const NAV_ITEMS: NavItem[] = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutGrid, roles: ["admin", "manager", "executive"], section: "run" },
  { to: "/document-types", label: "Document Types", icon: FileText, roles: ["admin", "manager"], section: "configure" },
  { to: "/match-configs", label: "Match Configs", icon: GitCompareArrows, roles: ["admin", "manager"], section: "configure" },
  { to: "/users", label: "Users", icon: UsersIcon, roles: ["admin"], section: "configure" },
  { to: "/process", label: "Process", icon: Activity, roles: ["admin", "manager", "executive"], section: "run" },
];

export function AppLayout({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  if (!user) return null;

  const visible = NAV_ITEMS.filter((item) => item.roles.includes(user.role));
  const configureItems = visible.filter((item) => item.section === "configure");
  const runItems = visible.filter((item) => item.section === "run");

  return (
    <div className="flex min-h-screen bg-slate-50 dark:bg-slate-950">
      <aside className="flex w-64 shrink-0 flex-col border-r border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
        <div className="flex items-center gap-2.5 px-5 py-4">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600 text-white">
            <FileStack className="h-4.5 w-4.5" strokeWidth={2.25} />
          </div>
          <span className="text-sm font-semibold tracking-tight text-slate-900 dark:text-white">
            AI Smart Doc Processing
          </span>
        </div>

        <nav className="flex-1 space-y-6 px-3 py-4">
          <NavSection items={runItems} />
          {configureItems.length > 0 && <NavSection title="Configure" items={configureItems} />}
        </nav>

        <div className="border-t border-slate-200 p-3 dark:border-slate-800">
          <div className="flex items-center gap-2 rounded-lg px-2 py-2">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-slate-200 text-xs font-semibold text-slate-600 dark:bg-slate-700 dark:text-slate-300">
              {user.name.slice(0, 1).toUpperCase()}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-slate-900 dark:text-white">{user.name}</p>
              <p className="truncate text-xs capitalize text-slate-500 dark:text-slate-400">{user.role}</p>
            </div>
            <button
              type="button"
              onClick={logout}
              aria-label="Log out"
              className="rounded-md p-1.5 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700 dark:hover:bg-slate-800 dark:hover:text-slate-200"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </aside>

      <main className="min-w-0 flex-1 overflow-y-auto">
        <div className="mx-auto max-w-7xl px-4 py-8 sm:px-8">{children}</div>
      </main>
    </div>
  );
}

function NavSection({ title, items }: { title?: string; items: NavItem[] }) {
  if (items.length === 0) return null;
  return (
    <div>
      {title && (
        <p className="mb-2 px-3 text-[11px] font-semibold uppercase tracking-wide text-slate-400 dark:text-slate-500">
          {title}
        </p>
      )}
      <div className="space-y-0.5">
        {items.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition ${
                isActive
                  ? "bg-indigo-50 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300"
                  : "text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
              }`
            }
          >
            <Icon className="h-4 w-4" />
            {label}
          </NavLink>
        ))}
      </div>
    </div>
  );
}
