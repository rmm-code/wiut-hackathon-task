import type { EngineReport } from "../types";
import { classes } from "../data/classes";
import { Icon } from "./Icon";

export function AnalysisInfo({ report }: { report?: EngineReport }) {
  if (!report) return null;
  const active = report.coverage.filter((item) => item.enabled).length;
  return (
    <details className="analysis-info">
      <summary>
        <Icon name="info" size={17} />
        <span>Analysis details</span>
        <span>
          {report.summary.road_users} tracked road users ·{" "}
          {report.summary.runtime_sec}s
        </span>
        <Icon name="down" size={15} />
      </summary>
      <div className="analysis-body">
        <p>
          <strong>{report.engine.model}</strong> · {report.engine.tracker} ·{" "}
          {report.engine.device.toUpperCase()} ·{" "}
          {report.meta.sample_fps.toFixed(1)} analyzed frames/s
        </p>
        <p>
          {report.scene.matched
            ? `Camera matched. Calibration is ${report.scene.calibration}.`
            : "This video does not match the configured intersection. Scene-specific event rules are disabled."}{" "}
          {active} of 14 event rules active.
        </p>
        <div className="coverage-list">
          {report.coverage.map((item) => (
            <span
              key={item.label}
              className={`badge ${item.enabled ? "badge-green" : "badge-neutral"}`}
              title={item.reason}
            >
              {classes[item.label].name} ·{" "}
              {item.enabled ? "provisional" : "off"}
            </span>
          ))}
        </div>
        <ul>
          {report.limitations.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </div>
    </details>
  );
}
