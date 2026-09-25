import { useState } from "react";
import { Icon } from "./Icon";

const views = {
  occupancy: ["Occupancy", "Time spent by tracked road users in each area."],
  motion: [
    "Movement",
    "Movement in image coordinates; this is not vehicle speed.",
  ],
  trajectories: [
    "Trajectories",
    "Paths followed by tracked objects. Identity switches can split paths.",
  ],
} as const;

export function Study({ jobId }: { jobId: string }) {
  const base = jobId.startsWith("sample-")
    ? `/api/samples/${jobId.slice(7)}`
    : `/api/jobs/${jobId}`;
  const [view, setView] = useState<keyof typeof views>("occupancy");
  return (
    <details className="analysis-info study">
      <summary>
        <Icon name="chart" size={17} />
        <span>Traffic patterns</span>
        <Icon name="down" size={15} />
      </summary>
      <div className="analysis-body">
        <div className="study-tabs" role="group" aria-label="Traffic map">
          {Object.entries(views).map(([key, [label]]) => (
            <button
              key={key}
              className={`button ${view === key ? "primary" : ""}`}
              aria-pressed={view === key}
              onClick={() => setView(key as keyof typeof views)}
            >
              {label}
            </button>
          ))}
        </div>
        <img
          src={`${base}/eda/${view}`}
          alt={`${views[view][0]} for this video`}
        />
        <p>
          {views[view][1]} Brighter heatmap areas indicate more activity within
          this video; scales are relative.
        </p>
      </div>
    </details>
  );
}
