import { useEffect, useRef, useState } from "react";
import { Study } from "../components/Study";
import { Stats } from "../components/Stats";
import { Camera } from "../components/Camera";
import { RiskChart } from "../components/Charts";
import { Timeline } from "../components/Timeline";
import { Events } from "../components/Events";
import { OperatorSummary } from "../components/OperatorSummary";
import { JobStatus } from "../components/JobStatus";
import { AnalysisInfo } from "../components/AnalysisInfo";
import { Icon } from "../components/Icon";
import type { Workspace } from "../hooks/useWorkspace";
import type { TrafficEvent } from "../types";

export function Dashboard({ workspace: w }: { workspace: Workspace }) {
  const review = useRef<HTMLDetailsElement>(null);
  const [showReview, setShowReview] = useState(true);
  useEffect(() => {
    if (
      review.current &&
      (w.selected ||
        w.video.source === "local" ||
        w.analysis.origin === "model")
    ) {
      review.current.open = true;
    }
  }, [w.selected, w.video.id, w.analysis.origin]);

  function jump(event: TrafficEvent) {
    w.pick(event);
    // The video sits above the timeline and the log: bring it into view so the jump is visible.
    requestAnimationFrame(() =>
      review.current?.scrollIntoView({ behavior: "smooth", block: "nearest" }),
    );
  }

  return (
    <>
      <JobStatus job={w.job} onCancel={w.cancelJob} />
      <Stats
        analysis={w.analysis}
        onInsights={() => w.navigate("samples")}
        onEvents={() =>
          document
            .getElementById("timeline")
            ?.scrollIntoView({ behavior: "smooth", block: "center" })
        }
      />
      <details
        ref={review}
        open
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
            />
          </div>
        )}
      </details>
      <Timeline
        events={w.analysis.events}
        duration={w.video.duration}
        position={w.position}
        selected={w.selected}
        onSelect={jump}
        onSeek={w.seek}
      />
      <Events
        key={w.video.id}
        analysis={w.analysis}
        selected={w.selected}
        onSelect={jump}
        onExport={w.exportResults}
      />
      <OperatorSummary events={w.analysis.events} duration={w.video.duration} />
      <AnalysisInfo report={w.analysis.report} />
      {w.job?.state === "complete" && w.analysis.report?.eda && (
        <Study jobId={w.job.id} />
      )}
    </>
  );
}
