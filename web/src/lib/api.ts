import type { Job, JobResult, ProjectInfo } from "../types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`/api${path}`, {
      credentials: "same-origin",
      cache: "no-store",
      ...init,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError")
      throw error;
    throw new Error(
      "The analysis server is unavailable. Start the backend and try again.",
    );
  }
  const body = await response.json().catch(() => null);
  if (!response.ok)
    throw new Error(
      typeof body?.detail === "string"
        ? body.detail
        : "The analysis server could not complete this request.",
    );
  if (!body)
    throw new Error("The analysis server returned an invalid response.");
  return body as T;
}

// The server's single-request limit is 95 MB; larger videos are sent in pieces.
const SINGLE_UPLOAD_BYTES = 90 * 1024 * 1024;

export const api = {
  about() {
    return request<ProjectInfo>("/about");
  },
  submit(file: File, signal?: AbortSignal) {
    const body = new FormData();
    body.append("file", file);
    return request<{ id: string }>("/jobs", { method: "POST", body, signal });
  },
  async upload(
    file: File,
    signal?: AbortSignal,
    events: {
      onStart?: (id: string) => void;
      onProgress?: (sent: number) => void;
    } = {},
  ) {
    if (file.size <= SINGLE_UPLOAD_BYTES) return api.submit(file, signal);
    const { id, chunk_bytes } = await request<{ id: string; chunk_bytes: number }>(
      "/uploads",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename: file.name, size: file.size }),
        signal,
      },
    );
    events.onStart?.(id);
    let sent = 0;
    while (sent < file.size) {
      const piece = file.slice(sent, Math.min(sent + chunk_bytes, file.size));
      for (let attempt = 1; ; attempt++) {
        try {
          const result = await request<{ received: number }>(
            `/uploads/${id}?offset=${sent}`,
            {
              method: "POST",
              headers: { "Content-Type": "application/octet-stream" },
              body: piece,
              signal,
            },
          );
          sent = result.received;
          break;
        } catch (error) {
          // The server acknowledges a repeated piece, so retrying after a dropped
          // connection is safe.
          if (signal?.aborted || attempt >= 4) throw error;
          await new Promise((resolve) => setTimeout(resolve, 1500 * attempt));
        }
      }
      events.onProgress?.(sent);
    }
    return request<{ id: string }>(`/uploads/${id}/complete`, {
      method: "POST",
      signal,
    });
  },
  sample(id: string, signal?: AbortSignal) {
    return request<{ id: string }>(
      `/samples/${encodeURIComponent(id)}/jobs`,
      {
        method: "POST",
        signal,
      },
    );
  },
  status(id: string, signal?: AbortSignal) {
    return request<Job>(
      id.startsWith("sample-")
        ? `/samples/${id.slice(7)}/status`
        : `/jobs/${id}`,
      { signal },
    );
  },
  result(id: string, signal?: AbortSignal) {
    return request<JobResult>(
      id.startsWith("sample-")
        ? `/samples/${id.slice(7)}/results`
        : `/jobs/${id}/results`,
      { signal },
    );
  },
  cancel(id: string) {
    if (id.startsWith("sample-")) return Promise.resolve({ state: "complete" });
    return request(`/jobs/${id}`, { method: "DELETE" });
  },
  samples(signal?: AbortSignal) {
    return request<
      {
        id: string;
        name: string;
        available: boolean;
        archived?: boolean;
        state: Job["state"] | null;
      }[]
    >("/samples", { signal });
  },
};
