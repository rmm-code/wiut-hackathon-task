import type { Job } from "../types";
import { Icon } from "./Icon";

export function JobStatus({ job, onCancel, onReanalyze }: {
  job: Job | null;
  onCancel: () => void;
  onReanalyze?: () => void;
}) {
  if (!job) return null;
  const complete = job.state === "complete";
  const failed = job.state === "failed";
  const cancelled = job.state === "cancelled";
  const preparing = job.state === "loading" || job.state === "uploading" ||
    job.state === "queued" || (job.state === "running" && !job.processed_frames);
  const progress = complete ? 1 : Math.max(0, Math.min(1, job.progress));
  const frames = job.processed_frames !== undefined
    ? `${job.processed_frames.toLocaleString()} / ${job.total_frames?.toLocaleString()} frames processed`
    : null;
  const description = failed ? job.error
    : complete ? `${frames ?? "Video processed in full"}. Saved results are ready.`
    : cancelled ? "This run was cancelled. Open the sample to restore its saved results."
    : job.state === "loading" ? "Checking saved results. This does not start a new analysis."
    : job.stage === "Preparing model" ? "Loading local models before processing begins."
    : frames ?? "Waiting for the local analysis server.";
  return (
    <section className={`job-status ${failed ? "job-error" : ""}`} role="status" aria-live="polite">
      <Icon name={failed ? "warning" : complete ? "check" : "cpu"} size={20} />
      <div>
        <strong>{complete ? "Analysis complete" : failed ? "Analysis could not finish" : cancelled ? "Analysis cancelled" : job.stage}</strong>
        <p>{description}</p>
        {!failed && !cancelled && <progress value={preparing ? undefined : progress} max={1} aria-label="Analysis progress" />}
      </div>
      {!failed && !cancelled && !preparing && <span className="job-percent">{Math.round(progress * 100)}%</span>}
      {complete ? onReanalyze && <button className="button small" onClick={onReanalyze}>Reanalyze</button>
        : <button className="button small" onClick={onCancel}>{failed || cancelled ? "Dismiss" : job.state === "loading" ? "Close" : "Cancel"}</button>}
    </section>
  );
}
