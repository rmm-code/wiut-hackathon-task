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
  const reviewed = events.filter((e) => e.reviewed).length;
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
          icon="circleCheck"
          title="Manual review"
          subtitle="Your review of detected events"
        />
        <div className="stat-body">
          <div className="stat-value-row">
            <span>Events checked by you</span>
            <strong>
              {available ? (
                <>
                  {reviewed}
                  <small> / {total}</small>
                </>
              ) : (
                "—"
              )}
            </strong>
          </div>
          <div
            className="segment-meter"
            aria-label={`${reviewed} of ${total} events reviewed`}
          >
            {Array.from({ length: 36 }, (_, i) => (
              <i
                key={i}
                className={total && i / 36 < reviewed / total ? "bg-green" : ""}
              />
            ))}
          </div>
          <div className="meter-label">
            <span>
              {available
                ? `${total - reviewed} awaiting review`
                : "Awaiting results"}
            </span>
            <span>{total ? Math.round((reviewed / total) * 100) : 0}%</span>
          </div>
          <div className="stat-context">
            <Icon name="eye" size={15} />
            <span>Select an event to inspect its details</span>
          </div>
        </div>
        <div className="card-footer tinted-green">
          <Icon name="check" size={15} />
          <span>Review changes are saved for this session</span>
        </div>
      </section>
    </div>
  );
}
