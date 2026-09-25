import { useEffect, useRef, useState } from "react";
import { Study } from "../components/Study";
import { Labels } from "../components/Labels";
import { Stats } from "../components/Stats";
import { Camera } from "../components/Camera";
import { RiskChart } from "../components/Charts";
import { Timeline } from "../components/Timeline";
import { Events } from "../components/Events";
import { JobStatus } from "../components/JobStatus";
import { AnalysisInfo } from "../components/AnalysisInfo";
import { Icon } from "../components/Icon";
import { demoVideo } from "../data/samples";
import type { Workspace } from "../hooks/useWorkspace";

export function Dashboard({ workspace: w }: { workspace: Workspace }) {
  const review = useRef<HTMLDetailsElement>(null);
  const [showReview, setShowReview] = useState(false);
  useEffect(() => {
    if (
      review.current &&
      (w.selected ||
        w.video.source === "local" ||
        w.analysis.origin === "imported" ||
        w.analysis.origin === "model")
    ) {
      review.current.open = true;
    }
  }, [w.selected, w.video.id, w.analysis.origin]);

  return (
    <>
      <JobStatus job={w.job} onCancel={w.cancelJob} onReanalyze={w.video.source === "sample" ? w.reanalyze : undefined} />
      {w.analysis.origin !== "preview" && !w.job && (
        <div className="notice-bar">
          <Icon name="info" size={16} />
          <span>
            {w.analysis.origin === "imported"
              ? "Imported results. Review events against the video."
              : "No analysis yet. Import existing results to review this video."}
          </span>
          <button onClick={() => w.choose(demoVideo)}>
            Explore preview
            <Icon name="arrow" size={14} />
          </button>
        </div>
      )}
      <Stats
        analysis={w.analysis}
        onInsights={() => w.navigate("samples")}
        onEvents={() =>
          document
            .getElementById("timeline")
            ?.scrollIntoView({ behavior: "smooth", block: "center" })
        }
      />
      <AnalysisInfo report={w.analysis.report} />
      {w.job?.state === "complete" && w.analysis.report?.eda && <Study jobId={w.job.id} />}
      <Timeline
        events={w.analysis.events}
        duration={w.video.duration}
        position={w.position}
        selected={w.selected}
        onSelect={w.pick}
        onSeek={w.seek}
      />
      <Events
        key={w.video.id}
        analysis={w.analysis}
        selected={w.selected}
        onSelect={w.pick}
        onReview={w.review}
        onExport={w.exportResults}
      />
      <details
        ref={review}
        className="review-panel"
        onToggle={(event) => {
          setShowReview(event.currentTarget.open);
          if (!event.currentTarget.open) w.setPlaying(false);
        }}
      >
        <summary>
          <span className="card-icon">
            <Icon name="camera" size={19} />
          </span>
          <div>
            <h2>Video & risk</h2>
            <p>{w.video.name} · playback and accident anticipation</p>
          </div>
          <Icon name="down" size={16} />
        </summary>
        {showReview && (
          <div className="monitor-grid">
            <Camera workspace={w} />
            <RiskChart
              risk={w.analysis.risk}
              position={w.position}
              preview={w.analysis.origin === "preview"}
            />
          </div>
        )}
      </details>
      {w.job?.state === "complete" && w.analysis.report?.eda && <Labels key={w.job.id} jobId={w.job.id} fps={w.analysis.report.meta.fps} duration={w.video.duration} />}
    </>
  );
}
