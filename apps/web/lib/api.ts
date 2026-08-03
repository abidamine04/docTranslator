import type { ApplicationSettings, DocumentRecord, ElementRecord, Job, Provider } from "./types";

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const TOKEN_KEY = "doctranslator:admin-token";

export function getAdminToken(): string {
  return typeof window === "undefined" ? "" : sessionStorage.getItem(TOKEN_KEY) ?? "";
}

export function setAdminToken(token: string): void {
  if (typeof window === "undefined") return;
  if (token) sessionStorage.setItem(TOKEN_KEY, token);
  else sessionStorage.removeItem(TOKEN_KEY);
}

function authenticatedHeaders(initial?: HeadersInit): Headers {
  const headers = new Headers(initial);
  const token = getAdminToken();
  if (token) headers.set("X-Admin-Token", token);
  return headers;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: authenticatedHeaders(init?.headers),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail));
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

async function download(path: string): Promise<Blob> {
  const response = await fetch(`${API_URL}${path}`, { headers: authenticatedHeaders() });
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(typeof body.detail === "string" ? body.detail : "Download failed");
  }
  return response.blob();
}

export const api = {
  upload: (file: File, onProgress: (percent: number) => void) =>
    new Promise<{ document: DocumentRecord; job: Job }>((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open("POST", `${API_URL}/api/documents/upload`);
      const token = getAdminToken();
      if (token) xhr.setRequestHeader("X-Admin-Token", token);
      xhr.upload.onprogress = (event) => event.lengthComputable && onProgress((event.loaded / event.total) * 100);
      xhr.onerror = () => reject(new Error("Upload failed. Check the API connection."));
      xhr.onload = () => {
        try {
          const body = JSON.parse(xhr.responseText);
          xhr.status < 300 ? resolve(body) : reject(new Error(body.detail ?? "Upload failed"));
        } catch {
          reject(new Error("The server returned an invalid response"));
        }
      };
      const form = new FormData();
      form.append("file", file);
      xhr.send(form);
    }),
  document: (id: string) => request<DocumentRecord>(`/api/documents/${id}`, { cache: "no-store" }),
  elements: (id: string) => request<ElementRecord[]>(`/api/documents/${id}/elements`, { cache: "no-store" }),
  providers: () => request<Provider[]>("/api/providers", { cache: "no-store" }),
  settings: () => request<ApplicationSettings>("/api/settings", { cache: "no-store" }),
  saveSettings: (body: ApplicationSettings, token: string) =>
    request<ApplicationSettings>("/api/settings", {
      method: "PUT",
      headers: { "Content-Type": "application/json", "X-Admin-Token": token },
      body: JSON.stringify(body),
    }),
  job: (id: string) => request<Job>(`/api/jobs/${id}`, { cache: "no-store" }),
  translate: (id: string, target_language: string, provider_id?: string) =>
    request<Job>(`/api/documents/${id}/translate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ target_language, provider_id }),
    }),
  cancel: (id: string) => request<Job>(`/api/documents/${id}/cancel`, { method: "POST" }),
  updateElement: (id: string, translated_text: string) =>
    request(`/api/elements/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ translated_text }),
    }),
  reviewElement: (id: string) => request(`/api/elements/${id}/review`, { method: "POST" }),
  export: (id: string) => request<{ id: string }>(`/api/documents/${id}/export`, { method: "POST" }),
  downloadExport: (id: string) => download(`/api/exports/${id}/download`),
  saveProvider: (body: Record<string, unknown>, token: string, id?: string) =>
    request<Provider>(id ? `/api/providers/${id}` : "/api/providers", {
      method: id ? "PUT" : "POST",
      headers: { "Content-Type": "application/json", "X-Admin-Token": token },
      body: JSON.stringify(body),
    }),
  testProvider: (id: string, token: string) =>
    request<{ ok: boolean; sample: string }>("/api/providers/test", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Admin-Token": token },
      body: JSON.stringify({ provider_id: id }),
    }),
};
