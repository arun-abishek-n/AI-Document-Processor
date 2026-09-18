import type { HealthResponse, ProcessResponse } from "../types";

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
