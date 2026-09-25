import { useEffect, useRef, useState } from "react";
import { api } from "../lib/api";
import { download } from "../lib/format";
import { classes } from "../data/classes";
import { labels, type EventTuple, type Label, type Review } from "../types";
import { Icon } from "./Icon";

const empty: Review = { events: [], reviewer: "", notes: "", complete: false, reviewed_entire_video: false };

export function Labels({ jobId, fps, duration }: { jobId: string; fps: number; duration: number }) {
  const player = useRef<HTMLVideoElement>(null);
  const [review, setReview] = useState<Review>(empty);
  const [ready, setReady] = useState(false);
  const [busy, setBusy] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [message, setMessage] = useState("");
  const [start, setStart] = useState(0);
  const [end, setEnd] = useState(0);
  const [label, setLabel] = useState<Label>("stopped_vehicle");
  useEffect(() => {
    const controller = new AbortController();
    api.labels(jobId, controller.signal).then(value => { setReview(value); setReady(true); }).catch(error => {
      if (!controller.signal.aborted) setMessage(error.message);
    });
    return () => controller.abort();
  }, [jobId]);
  useEffect(() => {
    if (!dirty) return;
    const guard = (event: BeforeUnloadEvent) => event.preventDefault();
    window.addEventListener("beforeunload", guard);
    return () => window.removeEventListener("beforeunload", guard);
  }, [dirty]);
  function change(update: Partial<Review>) {
    setReview(value => ({ ...value, ...update, complete: false }));
    setDirty(true);
    setMessage("");
  }
  function add() {
    if (!(Number.isFinite(start) && Number.isFinite(end) && start >= 0 && start < end && end <= duration)) {
      setMessage("Choose a start before the end, within the video.");
      return;
    }
    if (review.events.some(([a, b, kind]) => kind === label && start < b && end > a)) {
      setMessage("Intervals of the same type overlap. Remove the old interval and add their combined range.");
      return;
    }
    change({ events: [...review.events, [start, end, label] as EventTuple].sort((a, b) => a[0] - b[0]) });
  }
  async function save(complete: boolean) {
    setBusy(true);
    try {
      const result = await api.saveLabels(jobId, { ...review, complete });
      setReview(result); setDirty(false);
      setMessage(complete ? "Review finalized. You can export the labels for evaluation." : "Draft saved.");
    } catch (error) { setMessage(error instanceof Error ? error.message : "Could not save labels."); }
    finally { setBusy(false); }
  }
  async function exportLabels() {
    try { download("ground_truth.json", await api.exportLabels(jobId)); }
    catch (error) { setMessage(error instanceof Error ? error.message : "Export failed."); }
  }
  function step(direction: number) {
    if (!player.current) return;
    player.current.pause();
    player.current.currentTime = Math.max(0, Math.min(duration, player.current.currentTime + direction / fps));
  }
  return (
    <details className="analysis-info labels-panel">
      <summary><Icon name="book" size={17} /><span>Label this video</span><span>{dirty ? "Unsaved changes" : review.complete ? "Review complete" : "Independent review"}</span><Icon name="down" size={15} /></summary>
      <div className="analysis-body">
        <p>Review the clean video and mark every visible event. Model predictions are not copied into your labels. Review flags in the event table are separate from these evaluation labels.</p>
        <video ref={player} controls preload="metadata" src={`/api/jobs/${jobId}/source`} onError={() => setMessage("A clean video is unavailable for this older run. Analyze the video again to create one.")} />
        <div className="label-tools">
          <button className="button" onClick={() => step(-1)}>Previous frame</button>
          <button className="button" onClick={() => step(1)}>Next frame</button>
        </div>
        <fieldset disabled={!ready || busy}>
          <div className="label-tools">
            <label>Event<select value={label} onChange={e => setLabel(e.target.value as Label)}>{labels.map(value => <option key={value} value={value}>{classes[value].name}</option>)}</select></label>
            <label>Start (seconds)<input type="number" min={0} max={duration} step="0.001" value={start} onChange={e => setStart(Number(e.target.value))} /></label>
            <button className="button" onClick={() => setStart(Number((player.current?.currentTime ?? 0).toFixed(3)))}>Use current start</button>
            <label>End (seconds)<input type="number" min={0} max={duration} step="0.001" value={end} onChange={e => setEnd(Number(e.target.value))} /></label>
            <button className="button" onClick={() => setEnd(Number((player.current?.currentTime ?? 0).toFixed(3)))}>Use current end</button>
            <button className="button primary" onClick={add}>Add event</button>
          </div>
          <p>{classes[label].description}</p>
          <ul className="label-events">{review.events.map(([a, b, kind], index) => <li key={`${a}-${b}-${kind}`}><span>{classes[kind].name}</span><button onClick={() => { if (player.current) player.current.currentTime = a; }}>{a.toFixed(3)}–{b.toFixed(3)}s</button><button className="button" aria-label={`Remove ${classes[kind].name} at ${a} seconds`} onClick={() => change({ events: review.events.filter((_, i) => i !== index) })}>Remove</button></li>)}</ul>
          {!review.events.length && <p>No events labeled yet. A complete review can contain zero events.</p>}
          <div className="label-tools">
            <label>Reviewer name<input maxLength={120} value={review.reviewer} onChange={e => change({ reviewer: e.target.value })} /></label>
            <label className="review-notes">Notes<input maxLength={4000} value={review.notes} onChange={e => change({ notes: e.target.value })} placeholder="Ambiguous events, visibility, and limitations" /></label>
          </div>
          <label className="review-confirm"><input type="checkbox" checked={review.reviewed_entire_video} onChange={e => change({ reviewed_entire_video: e.target.checked })} />I reviewed the entire video for all 14 event types.</label>
          <div className="label-tools">
            <button className="button" onClick={() => void save(false)}>Save draft</button>
            <button className="button primary" disabled={!review.reviewer.trim() || !review.reviewed_entire_video} onClick={() => void save(true)}>Finalize review</button>
            <button className="button" disabled={!review.complete || dirty} onClick={() => void exportLabels()}>Export labels</button>
          </div>
        </fieldset>
        {message && <p role="status">{message}</p>}
        <p>Saved reviews follow the same 24-hour retention as uploads. Export completed labels to keep them.</p>
      </div>
    </details>
  );
}
