import { useState, type FormEvent } from "react";
import { Navigate } from "react-router-dom";
import { FileSearch, FileStack, Loader2, ScanText, ShieldCheck } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { ApiRequestError } from "../lib/api";

const DEMO_ACCOUNTS = [
  { role: "Admin", username: "admin", password: "admin123" },
  { role: "Manager", username: "manager", password: "manager123" },
  { role: "Executive", username: "executive", password: "executive123" },
];

export function Login() {
  const { user, login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  if (user) return <Navigate to="/dashboard" replace />;

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setIsSubmitting(true);
    setError("");
    try {
      await login(username, password);
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Could not log in. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const fillDemo = (demoUsername: string, demoPassword: string) => {
    setUsername(demoUsername);
    setPassword(demoPassword);
  };

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <div className="hidden flex-col justify-center bg-slate-900 px-12 text-white lg:flex">
        <div className="mx-auto max-w-sm">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-500">
              <FileStack className="h-5 w-5" strokeWidth={2.25} />
            </div>
            <span className="text-sm font-semibold tracking-tight">AI Smart Document Processing</span>
          </div>
          <h1 className="mt-8 text-3xl font-semibold leading-tight tracking-tight">
            Turn documents into
            <span className="text-indigo-400"> validated, structured intelligence</span>
          </h1>
          <p className="mt-4 text-sm text-slate-300">
            OCR-based extraction, configurable document types, and real 2-way/3-way matching —
            with every result computed from the documents you actually upload.
          </p>
          <div className="mt-10 space-y-4 text-sm text-slate-300">
            <div className="flex items-center gap-3">
              <ScanText className="h-4 w-4 text-indigo-400" /> OCR + field extraction
            </div>
            <div className="flex items-center gap-3">
              <FileSearch className="h-4 w-4 text-indigo-400" /> Configurable document types
            </div>
            <div className="flex items-center gap-3">
              <ShieldCheck className="h-4 w-4 text-indigo-400" /> Real 2-way / 3-way matching
            </div>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-sm">
          <div className="mb-8 lg:hidden">
            <div className="flex items-center gap-2.5">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-600 text-white">
                <FileStack className="h-5 w-5" strokeWidth={2.25} />
              </div>
              <span className="text-sm font-semibold tracking-tight text-slate-900 dark:text-white">
                AI Smart Document Processing
              </span>
            </div>
          </div>

          <h2 className="text-xl font-semibold tracking-tight text-slate-900 dark:text-white">Sign in</h2>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            This is a portfolio demo — use one of the demo accounts below.
          </p>

          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            <div>
              <label htmlFor="username" className="text-xs font-medium text-slate-700 dark:text-slate-300">
                Username
              </label>
              <input
                id="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                autoComplete="username"
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 dark:border-slate-700 dark:bg-slate-900 dark:text-white"
              />
            </div>
            <div>
              <label htmlFor="password" className="text-xs font-medium text-slate-700 dark:text-slate-300">
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 dark:border-slate-700 dark:bg-slate-900 dark:text-white"
              />
            </div>

            {error && (
              <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-xs font-medium text-red-700 dark:bg-red-950/50 dark:text-red-400">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={isSubmitting}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:bg-slate-300"
            >
              {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
              Sign in
            </button>
          </form>

          <div className="mt-8 rounded-xl border border-slate-200 p-3 dark:border-slate-800">
            <p className="mb-2 text-xs font-semibold text-slate-500 dark:text-slate-400">Demo accounts</p>
            <div className="space-y-1.5">
              {DEMO_ACCOUNTS.map((account) => (
                <button
                  key={account.username}
                  type="button"
                  onClick={() => fillDemo(account.username, account.password)}
                  className="flex w-full items-center justify-between rounded-md px-2 py-1.5 text-left text-xs transition hover:bg-slate-50 dark:hover:bg-slate-800"
                >
                  <span className="font-medium text-slate-700 dark:text-slate-300">{account.role}</span>
                  <span className="font-mono text-slate-400">
                    {account.username} / {account.password}
                  </span>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
