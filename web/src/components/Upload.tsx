import { useEffect, useRef, useState } from "react";
import { Icon } from "./Icon";
import { MAX_UPLOAD_LABEL } from "../lib/media";

export function Upload({
  kind,
  filename,
  onClose,
  onFile,
}: {
  kind: "video" | "results";
  filename: string;
  onClose: () => void;
  onFile: (file: File) => Promise<void>;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const input = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const isVideo = kind === "video";
  useEffect(() => {
    const element = dialog.current;
    element?.showModal();
    return () => element?.close();
  }, []);

  async function select(file?: File) {
    if (!file || busy) return;
    setError("");
    setBusy(true);
    try {
      await onFile(file);
      onClose();
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "This file could not be opened.",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <dialog
      ref={dialog}
      className="upload-dialog"
      onCancel={(event) => {
        if (busy) event.preventDefault();
        else onClose();
      }}
      aria-labelledby="upload-title"
    >
      <div className="dialog-top">
        <span className="dialog-icon">
          <Icon name={isVideo ? "upload" : "json"} size={24} />
        </span>
        <button
          className="icon-button"
          onClick={onClose}
          disabled={busy}
          aria-label="Close dialog"
        >
          <Icon name="close" />
        </button>
      </div>
      <h2 id="upload-title">
        {isVideo ? "Analyze a video" : "Import analysis results"}
      </h2>
      <p>
        {isVideo ? (
          "Upload a road-camera clip for local YOLO detection, tracking, and event analysis."
        ) : (
          <>
            Import predictions for <strong>{filename}</strong> using the
            official JSON format.
          </>
        )}
      </p>
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
        <Icon name={isVideo ? "film" : "json"} size={35} />
        <strong>
          {busy
            ? "Preparing your video…"
            : "Drop a file here, or click to browse"}
        </strong>
        <span>
          {isVideo
            ? `MP4 · up to 2 minutes · ${MAX_UPLOAD_LABEL} maximum`
            : "predictions.json · 20 MB maximum"}
        </span>
      </button>
      <input
        ref={input}
        type="file"
        accept={isVideo ? ".mp4,video/mp4" : ".json,application/json"}
        className="sr-only"
        onChange={(e) => {
          void select(e.target.files?.[0]);
          e.target.value = "";
        }}
        aria-label={isVideo ? "Choose MP4 file" : "Choose predictions JSON"}
      />
      {error && (
        <div className="error-message" role="alert">
          <Icon name="warning" size={18} />
          <span>{error}</span>
        </div>
      )}
      <div className="upload-note">
        <Icon name="shield" size={19} />
        <p>
          {isVideo
            ? "Your video is analysed on our server by the same engine as the submission, on CPU: a two-minute 1080p clip takes about 9 minutes, a two-minute 4K clip about 15–20. You get events, a risk curve and an annotated video. No hosted AI service is used; the original is deleted when its analysis ends, and results after 24 hours."
            : "Results must match the selected filename. We check classes, timestamps, same-class overlaps, and risk scores before importing."}
        </p>
      </div>
      <div className="dialog-footer">
        <span>Open-weights models only · uploads deleted after 24 hours</span>
        <button className="button" onClick={onClose} disabled={busy}>
          Cancel
        </button>
      </div>
    </dialog>
  );
}
