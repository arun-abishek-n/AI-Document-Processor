import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import type { Role } from "../types";

interface ProtectedRouteProps {
  allowedRoles?: Role[];
  children: ReactNode;
}

/** Redirects to /login if unauthenticated, or to /dashboard if the current
 * user's role isn't in allowedRoles — actual route gating, not just a
 * hidden nav link (the API enforces the same roles server-side too). */
export function ProtectedRoute({ allowedRoles, children }: ProtectedRouteProps) {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return <div className="flex min-h-screen items-center justify-center text-sm text-slate-500">Loading…</div>;
  }
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to="/dashboard" replace />;
  }
  return <>{children}</>;
}
