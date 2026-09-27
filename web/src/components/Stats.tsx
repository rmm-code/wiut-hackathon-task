import { TrafficSummary } from "./TrafficSummary";
import { CardHead } from "./Card";
import { Icon } from "./Icon";
import { classes } from "../data/classes";
import type { Analysis } from "../types";

export function Stats({
  analysis,
  onEvents,
  onInsights,
}: {
  analysis: Analysis;
  onEvents: () => void;
  onInsights: () => void;
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
          subtitle="Events in the selected video"
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
        onOpen={onInsights}
        activity={analysis.report?.summary.activity}
        roadUsers={analysis.report?.summary.road_users}
      />
    </div>
  );
}
