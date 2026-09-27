import { useRef, useState } from "react";
import { CardHead } from "../components/Card";
import { Icon } from "../components/Icon";
import { MAX_UPLOAD_LABEL } from "../lib/media";
import { Dashboard } from "./Dashboard";
import type { Workspace } from "../hooks/useWorkspace";

const steps: [string, string][] = [
  [
    "Upload",
    `An MP4 of up to 2 minutes and ${MAX_UPLOAD_LABEL}. Large files are sent in pieces, with a progress bar.`,
  ],
  [
    "Analysis",
    "Our server runs the same engine as the submission, on CPU: about 9 minutes for a 2-minute 1080p clip, 15–20 for 4K.",
  ],
  [
    "Results",
    "The events with their times, a timeline, the annotated video and the accident-risk curve, on this page. Export them as JSON.",
  ],
];

function DropZone({ onFile }: { onFile: (file: File) => Promise<void> }) {
  const input = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function select(file?: File) {
    if (!file || busy) return;
    setError("");
    setBusy(true);
    try {
      await onFile(file);
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "This file could not be opened.",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="card demo-upload">
      <button
        className={`dropzone ${dragging ? "dragging" : ""}`}
        onClick={() => input.current?.click()}
        disabled={busy}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          void select(e.dataTransfer.files[0]);
        }}
      >
        <Icon name="film" size={35} />
        <strong>
          {busy ? "Preparing your video…" : "Drop an MP4 here, or click to choose one"}
        </strong>
        <span>MP4 · up to 2 minutes · {MAX_UPLOAD_LABEL} maximum</span>
      </button>
      <input
        ref={input}
        type="file"
        accept=".mp4,video/mp4"
        className="sr-only"
        onChange={(e) => {
          void select(e.target.files?.[0]);
          e.target.value = "";
        }}
        aria-label="Choose an MP4 file"
      />
      {error && (
        <div className="error-message" role="alert">
          <Icon name="warning" size={18} />
          <span>{error}</span>
        </div>
      )}
    </section>
  );
}

export function LiveDemo({
  workspace: w,
  onUpload,
}: {
  workspace: Workspace;
  onUpload: () => void;
}) {
  if (w.video.source === "local")
    return (
      <>
        <section className="card approach-intro">
          <div>
            <span className="eyebrow">LIVE DEMO</span>
            <h2>{w.video.name}</h2>
            <p>
              Your video. Progress and results appear below. The original is
              deleted when the analysis ends, and the results after 24 hours.
            </p>
          </div>
          <button className="button" onClick={onUpload}>
            <Icon name="upload" size={16} />
            Upload another video
          </button>
        </section>
        <Dashboard workspace={w} onUpload={onUpload} />
      </>
    );
  return (
    <>
      <section className="card approach-intro">
        <div>
          <span className="eyebrow">LIVE DEMO</span>
          <h2>Analyse your own video</h2>
          <p>
            Upload a clip from this camera. Our server runs the same detection,
            tracking and rules as the submission and shows what it found. No
            hosted AI service is used.
          </p>
        </div>
      </section>
      <DropZone onFile={w.upload} />
      <section className="card">
        <CardHead icon="stack" title="What happens" subtitle="From upload to results" />
        <ol className="demo-steps">
          {steps.map(([title, text], i) => (
            <li key={title}>
              <span className="demo-step-number">{i + 1}</span>
              <div>
                <h3>{title}</h3>
                <p>{text}</p>
              </div>
            </li>
          ))}
        </ol>
      </section>
    </>
  );
}
