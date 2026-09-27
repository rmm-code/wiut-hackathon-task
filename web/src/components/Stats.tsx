import { TrafficSummary } from "./TrafficSummary";
import { CardHead } from "./Card";
import { Icon } from "./Icon";
import { classes } from "../data/classes";
import type { Analysis } from "../types";

export function Stats({
  analysis,
  onEvents,
  onInsights,
  onUpload,
}: {
  analysis: Analysis;
  onEvents: () => void;
  onInsights: () => void;
  onUpload: () => void;
}) {
  const { events, origin } = analysis;
  const available = origin !== "none";
  const total = events.length;
  const critical = events.filter(
    (e) => classes[e.label].level === "critical",
  ).length;
  const warning = events.filter(
    (e) => classes[e.label].level === "warning",
  ).length;
  const notice = total - critical - warning;
  return (
    <div className="stats-grid">
      <section className="card stat-card">
        <CardHead
          icon="bars"
          title="Event overview"
          subtitle={
            origin === "preview"
              ? "Illustrative events · not model results"
              : "Events in the selected video"
          }
        />
        <div className="stat-body">
          <div className="stat-value-row">
            <span>Total events</span>
            <strong>{available ? String(total).padStart(2, "0") : "—"}</strong>
          </div>
          <div
            className="split-meter"
            aria-label={`${critical} critical, ${warning} warnings, ${notice} notices`}
          >
            <i
              className={available ? "bg-red" : ""}
              style={{ flex: critical || 0.1 }}
            />
            <i
              className={available ? "bg-amber" : ""}
              style={{ flex: warning || 0.1 }}
            />
            <i
              className={available ? "bg-green" : ""}
              style={{ flex: notice || 0.1 }}
            />
          </div>
          {[
            ["Critical", critical, "red"],
            ["Warning", warning, "amber"],
            ["Notice", notice, "green"],
          ].map(([name, count, color]) => (
            <div className="stat-legend" key={name}>
              <span>
                <i className={`dot bg-${color}`} />
                {name}
              </span>
              <span>
                <b>{available ? count : "—"}</b> events
              </span>
            </div>
          ))}
        </div>
        <button className="card-footer" onClick={onEvents}>
          View event timeline <Icon name="arrow" size={16} />
        </button>
      </section>
      <TrafficSummary
        preview={origin === "preview"}
        onOpen={onInsights}
        activity={analysis.report?.summary.activity}
        roadUsers={analysis.report?.summary.road_users}
      />
      <section className="card stat-card">
        <CardHead
          icon="upload"
          title="Live demo"
          subtitle="Analyse your own video"
        />
        <div className="stat-body">
          <p className="stat-note">
            Upload an MP4 of up to 2 minutes and 2.5 GB. Our server runs the
            same engine as the submission and returns the events, a timeline,
            an annotated video and the risk curve.
          </p>
          <button className="button primary" onClick={onUpload}>
            <Icon name="upload" size={16} />
            Upload video
          </button>
        </div>
      </section>
    </div>
  );
}
