import type { Job, JobResult, Review, ProjectInfo } from "../types";

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

export const api = {
  about() {
    return request<ProjectInfo>("/about");
  },
  labels(id: string, signal?: AbortSignal) {
    return request<Review>(`/jobs/${id}/labels`, { signal });
  },
  saveLabels(id: string, body: Review) {
    return request<Review>(`/jobs/${id}/labels`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  },
  exportLabels(id: string) {
    return request<Record<string, unknown>>(`/jobs/${id}/labels/export`);
  },
  submit(file: File, signal?: AbortSignal) {
    const body = new FormData();
    body.append("file", file);
    return request<{ id: string }>("/jobs", { method: "POST", body, signal });
  },
  sample(id: string, signal?: AbortSignal, force = false) {
    return request<{ id: string }>(
      `/samples/${encodeURIComponent(id)}/jobs${force ? "?force=true" : ""}`,
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
