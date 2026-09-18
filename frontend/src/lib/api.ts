import type {
  Batch,
  BatchDetail,
  DashboardSummary,
  DocumentType,
  DocumentTypeField,
  HealthResponse,
  MatchConfig,
  MatchRule,
  ProcessResponse,
  TokenResponse,
  User,
} from "../types";

// No trailing slash, no hardcoded localhost fallback baked into production
// builds — VITE_API_URL must be set at build/deploy time (see .env.example).
// Falling back to localhost only makes sense for local `npm run dev`.
export const API_BASE_URL: string =
  (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "") ??
  "http://localhost:8000";

export class ApiRequestError extends Error {
  status?: number;

  constructor(message: string, status?: number) {
    super(message);
    this.name = "ApiRequestError";
    this.status = status;
  }
}

export async function checkHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/api/health`);
  if (!response.ok) {
    throw new ApiRequestError(`Health check failed (HTTP ${response.status})`, response.status);
  }
  return response.json() as Promise<HealthResponse>;
}

/**
 * Upload + process a document. Uses XMLHttpRequest (not fetch) because it's
 * the only browser API that exposes real upload-progress events, which
 * drives the "Uploading" stage's progress bar honestly instead of faking it.
 */
export function processDocument(
  file: File,
  onUploadProgress: (percent: number) => void,
): Promise<ProcessResponse> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${API_BASE_URL}/api/process`);
    xhr.timeout = 120_000; // generous ceiling for larger scans / multi-page PDFs

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) {
        onUploadProgress(Math.round((event.loaded / event.total) * 100));
      }
    };

    xhr.onload = () => {
      let body: unknown = null;
      try {
        body = JSON.parse(xhr.responseText);
      } catch {
        // Non-JSON response (e.g. a proxy error page) — handled below via status check.
      }

      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(body as ProcessResponse);
        return;
      }

      const detail =
        body && typeof body === "object" && "detail" in body
          ? String((body as { detail: unknown }).detail)
          : `Request failed with status ${xhr.status}.`;
      reject(new ApiRequestError(detail, xhr.status));
    };

    xhr.onerror = () => {
      reject(
        new ApiRequestError(
          "Could not reach the processing server. It may be offline, waking up, or unreachable from this network — please try again in a moment.",
        ),
      );
    };

    xhr.ontimeout = () => {
      reject(
        new ApiRequestError(
          "The server took too long to respond. Large or multi-page documents can take longer — please try again.",
        ),
      );
    };

    const formData = new FormData();
    formData.append("file", file);
    xhr.send(formData);
  });
}

// --- Authenticated client -------------------------------------------------

const TOKEN_STORAGE_KEY = "aidp_token";

export function getStoredToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_STORAGE_KEY);
  } catch {
    return null; // localStorage can throw in some private-browsing modes
  }
}

export function setStoredToken(token: string | null): void {
  try {
    if (token) localStorage.setItem(TOKEN_STORAGE_KEY, token);
    else localStorage.removeItem(TOKEN_STORAGE_KEY);
  } catch {
    // best-effort only — session just won't survive a refresh in this browser
  }
}

async function authFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getStoredToken();
  const headers = new Headers(options.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (options.body && !(options.body instanceof FormData)) headers.set("Content-Type", "application/json");

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
  } catch {
    throw new ApiRequestError("Could not reach the processing server. Please check your connection and try again.");
  }

  let body: unknown = null;
  const text = await response.text();
  if (text) {
    try {
      body = JSON.parse(text);
    } catch {
      // non-JSON body (rare) — fall through to the status-based error below
    }
  }

  if (!response.ok) {
    const detail =
      body && typeof body === "object" && "detail" in body
        ? String((body as { detail: unknown }).detail)
        : `Request failed with status ${response.status}.`;
    throw new ApiRequestError(detail, response.status);
  }

  return body as T;
}

export function login(username: string, password: string): Promise<TokenResponse> {
  return authFetch<TokenResponse>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

export function getMe(): Promise<User> {
  return authFetch<User>("/api/auth/me");
}

// --- Document types ---------------------------------------------------

export interface DocumentTypeInput {
  name: string;
  description: string;
  status: "draft" | "configured";
  fields: DocumentTypeField[];
}

export const listDocumentTypes = () => authFetch<DocumentType[]>("/api/document-types");
export const createDocumentType = (payload: DocumentTypeInput) =>
  authFetch<DocumentType>("/api/document-types", { method: "POST", body: JSON.stringify(payload) });
export const updateDocumentType = (id: number, payload: DocumentTypeInput) =>
  authFetch<DocumentType>(`/api/document-types/${id}`, { method: "PUT", body: JSON.stringify(payload) });
export const deleteDocumentType = (id: number) =>
  authFetch<void>(`/api/document-types/${id}`, { method: "DELETE" });

// --- Match configurations -----------------------------------------------

export interface MatchConfigInput {
  name: string;
  match_type: "2-way" | "3-way";
  is_active: boolean;
  document_type_ids: number[];
  rules: MatchRule[];
}

export const listMatchConfigs = () => authFetch<MatchConfig[]>("/api/match-configs");
export const createMatchConfig = (payload: MatchConfigInput) =>
  authFetch<MatchConfig>("/api/match-configs", { method: "POST", body: JSON.stringify(payload) });
export const updateMatchConfig = (id: number, payload: MatchConfigInput) =>
  authFetch<MatchConfig>(`/api/match-configs/${id}`, { method: "PUT", body: JSON.stringify(payload) });
export const deleteMatchConfig = (id: number) =>
  authFetch<void>(`/api/match-configs/${id}`, { method: "DELETE" });

// --- Users ---------------------------------------------------------------

export interface UserCreateInput {
  username: string;
  password: string;
  name: string;
  role: string;
}

export interface UserUpdateInput {
  name?: string;
  role?: string;
  is_active?: boolean;
  password?: string;
}

export const listUsers = () => authFetch<User[]>("/api/users");
export const createUser = (payload: UserCreateInput) =>
  authFetch<User>("/api/users", { method: "POST", body: JSON.stringify(payload) });
export const updateUser = (id: number, payload: UserUpdateInput) =>
  authFetch<User>(`/api/users/${id}`, { method: "PATCH", body: JSON.stringify(payload) });

// --- Batches / matching workflow ------------------------------------------

export const listBatches = () => authFetch<Batch[]>("/api/batches");
export const getBatch = (id: number) => authFetch<BatchDetail>(`/api/batches/${id}`);

export function createBatch(
  files: File[],
  matchConfigId: number,
  onUploadProgress: (percent: number) => void,
): Promise<BatchDetail> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${API_BASE_URL}/api/batches`);
    xhr.timeout = 180_000; // several documents OCR'd sequentially can take a while
    const token = getStoredToken();
    if (token) xhr.setRequestHeader("Authorization", `Bearer ${token}`);

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) onUploadProgress(Math.round((event.loaded / event.total) * 100));
    };

    xhr.onload = () => {
      let body: unknown = null;
      try {
        body = JSON.parse(xhr.responseText);
      } catch {
        // handled by status check below
      }
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(body as BatchDetail);
        return;
      }
      const detail =
        body && typeof body === "object" && "detail" in body
          ? String((body as { detail: unknown }).detail)
          : `Request failed with status ${xhr.status}.`;
      reject(new ApiRequestError(detail, xhr.status));
    };

    xhr.onerror = () => reject(new ApiRequestError("Could not reach the processing server."));
    xhr.ontimeout = () => reject(new ApiRequestError("The server took too long to respond."));

    const formData = new FormData();
    files.forEach((file) => formData.append("files", file));
    formData.append("match_config_id", String(matchConfigId));
    xhr.send(formData);
  });
}

export const assignDocumentType = (batchId: number, docId: number, documentTypeId: number) =>
  authFetch<BatchDetail>(`/api/batches/${batchId}/documents/${docId}`, {
    method: "PATCH",
    body: JSON.stringify({ document_type_id: documentTypeId }),
  });

export const matchBatch = (batchId: number) =>
  authFetch<BatchDetail>(`/api/batches/${batchId}/match`, { method: "POST" });

export const getDashboardSummary = () => authFetch<DashboardSummary>("/api/dashboard/summary");
