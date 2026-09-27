import type { Job } from "../types";
import { Icon } from "./Icon";

// Shown while a video is uploading or being analysed, and when a run failed or was
// cancelled. Finished results speak for themselves.
export function JobStatus({ job, onCancel }: {
  job: Job | null;
  onCancel: () => void;
}) {
  if (!job || job.state === "complete") return null;
  const failed = job.state === "failed";
  const cancelled = job.state === "cancelled";
  const uploading = job.state === "uploading" && job.progress > 0;
  const preparing = !uploading && (job.state === "loading" || job.state === "uploading" ||
    job.state === "queued" || (job.state === "running" && !job.processed_frames));
  const progress = Math.max(0, Math.min(1, job.progress));
  const frames = job.processed_frames !== undefined
    ? `${job.processed_frames.toLocaleString()} / ${job.total_frames?.toLocaleString()} frames processed`
    : null;
  const description = failed ? job.error
    : cancelled ? "This run was cancelled. Open the sample to restore its saved results."
    : job.state === "loading" ? "Checking saved results. This does not start a new analysis."
    : uploading ? `${job.detail}. Analysis starts when the upload finishes; a 2-minute 4K video then takes about 15–20 minutes on our CPU server.`
    : job.stage === "Preparing model" ? "Loading local models before processing begins."
    : frames ?? "Waiting for the local analysis server.";
  return (
    <section className={`job-status ${failed ? "job-error" : ""}`} role="status" aria-live="polite">
      <Icon name={failed ? "warning" : "cpu"} size={20} />
      <div>
        <strong>{failed ? "Analysis could not finish" : cancelled ? "Analysis cancelled" : job.stage}</strong>
        <p>{description}</p>
        {!failed && !cancelled && <progress value={preparing ? undefined : progress} max={1} aria-label="Analysis progress" />}
      </div>
      {!failed && !cancelled && !preparing && <span className="job-percent">{Math.round(progress * 100)}%</span>}
      <button className="button small" onClick={onCancel}>{failed || cancelled ? "Dismiss" : job.state === "loading" ? "Close" : "Cancel"}</button>
    </section>
  );
}
