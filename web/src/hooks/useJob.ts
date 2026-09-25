import { useEffect, useRef, useState } from "react";
import { api } from "../lib/api";
import type { Job, JobResult } from "../types";

export function useJob(onResult: (result: JobResult) => void) {
  const [job, setJob] = useState<Job | null>(null);
  const callback = useRef(onResult);
  callback.current = onResult;
  const current = useRef<{
    version: number;
    id?: string;
    controller?: AbortController;
  }>({ version: 0 });

  function remember(id?: string) {
    try {
      if (id) sessionStorage.setItem("crossing.job", id);
      else sessionStorage.removeItem("crossing.job");
    } catch {
      /* Persistence is optional. */
    }
  }

  function reset() {
    remember();
    current.current.controller?.abort();
    current.current = { version: current.current.version + 1 };
    setJob(null);
  }

  useEffect(() => {
    let id: string | null = null;
    try {
      id = sessionStorage.getItem("crossing.job");
    } catch {
      /* Optional persistence. */
    }
    if (id && /^(?:[a-f0-9]{32}|sample-c(?:3896|3897|3902|3905))$/.test(id)) {
      const controller = new AbortController();
      current.current.controller = controller;
      current.current.id = id;
      setJob({
        id,
        state: "loading",
        stage: "Opening saved analysis",
        progress: 0,
      });
      void monitor(id, current.current.version, controller);
    }
    if (!id) {
      const controller = new AbortController();
      const version = current.current.version;
      current.current.controller = controller;
      void api.samples(controller.signal).then(items => {
        if (controller.signal.aborted || current.current.version !== version) return;
        const saved = items.find(item => item.archived);
        if (!saved) return;
        const identity = `sample-${saved.id}`;
        current.current.id = identity;
        remember(identity);
        setJob({ id: identity, state: "loading", stage: "Opening saved sample", progress: 0 });
        void monitor(identity, version, controller);
      }).catch(() => {});
    }
    return () => {
      current.current.controller?.abort();
      current.current.version++;
    };
  }, []);

  async function monitor(
    id: string,
    version: number,
    controller: AbortController,
  ) {
    try {
      while (current.current.version === version) {
        const next = await api.status(id, controller.signal);
        if (current.current.version !== version) return;
        if (next.state === "complete") {
          const result = await api.result(id, controller.signal);
          if (current.current.version === version) {
            callback.current(result);
            setJob({ ...next, progress: 1 });
          }
          return;
        }
        setJob(next);
        if (next.state === "failed" || next.state === "cancelled") return;
        await new Promise((resolve) => setTimeout(resolve, 1200));
      }
    } catch (error) {
      if (current.current.version === version && !controller.signal.aborted) {
        setJob((value) =>
          value
            ? {
                ...value,
                state: "failed",
                error:
                  error instanceof Error ? error.message : "Analysis failed.",
              }
            : null,
        );
      }
    }
  }

  async function start(fileOrSample: File | string, force = false) {
    reset();
    const version = current.current.version;
    const controller = new AbortController();
    current.current.controller = controller;
    const sample = typeof fileOrSample === "string";
    setJob({
      id: "",
      state: sample ? "loading" : "uploading",
      progress: 0,
      stage: sample
        ? "Opening sample analysis"
        : "Sending video to the local server",
    });
    try {
      const result = sample
        ? await api.sample(fileOrSample, controller.signal, force)
        : await api.submit(fileOrSample, controller.signal);
      if (current.current.version !== version) return;
      current.current.id = result.id;
      remember(result.id);
      setJob({
        id: result.id,
        state: "loading",
        progress: 0,
        stage: "Opening analysis",
      });
      void monitor(result.id, version, controller);
    } catch (error) {
      if (current.current.version !== version) return;
      setJob({
        id: "",
        state: "failed",
        progress: 0,
        stage: "Could not start",
        error: error instanceof Error ? error.message : "Upload failed.",
      });
      throw error;
    }
  }

  async function cancel() {
    const id = current.current.id;
    reset();
    if (id) await api.cancel(id);
  }

  return { job, start, reset, cancel };
}
