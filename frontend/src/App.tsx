import { Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { AppLayout } from "./layouts/AppLayout";
import { Login } from "./pages/Login";
import { Dashboard } from "./pages/Dashboard";
import { DocumentTypes } from "./pages/DocumentTypes";
import { MatchConfigs } from "./pages/MatchConfigs";
import { Users } from "./pages/Users";
import { Process } from "./pages/Process";
import { BatchDetailPage } from "./pages/BatchDetail";

function AppRoutes() {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return <div className="flex min-h-screen items-center justify-center text-sm text-slate-500">Loading…</div>;
  }

  return (
    <Routes>
      <Route path="/login" element={<Login />} />

      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <AppLayout>
              <Dashboard />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/document-types"
        element={
          <ProtectedRoute allowedRoles={["admin", "manager"]}>
            <AppLayout>
              <DocumentTypes />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/match-configs"
        element={
          <ProtectedRoute allowedRoles={["admin", "manager"]}>
            <AppLayout>
              <MatchConfigs />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/users"
        element={
          <ProtectedRoute allowedRoles={["admin"]}>
            <AppLayout>
              <Users />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/process"
        element={
          <ProtectedRoute>
            <AppLayout>
              <Process />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/process/:id"
        element={
          <ProtectedRoute>
            <AppLayout>
              <BatchDetailPage />
            </AppLayout>
          </ProtectedRoute>
        }
      />

      <Route path="/" element={<Navigate to={user ? "/dashboard" : "/login"} replace />} />
      <Route path="*" element={<Navigate to={user ? "/dashboard" : "/login"} replace />} />
    </Routes>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  );
}

export default App;
