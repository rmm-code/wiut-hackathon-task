import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { samples } from "../data/samples";
import { time } from "../lib/format";
import { Icon } from "../components/Icon";
import { CardHead } from "../components/Card";
import { TrafficChart } from "../components/Charts";
import type { EngineReport, Video } from "../types";

export function Samples({
  onSample,
  report,
  filename,
}: {
  onSample: (video: Video) => void;
  report?: EngineReport;
  filename?: string;
}) {
  const [states, setStates] = useState<Record<string, string | null>>({});
  const [available, setAvailable] = useState<string[]>([]);
  useEffect(() => {
    api
      .samples()
      .then((items) => {
        setAvailable(items.filter(item => item.available).map(item => item.id));
        setStates(Object.fromEntries(items.map(item => [item.id, item.state])));
      })
      .catch(() => {});
  }, []);
  return (
    <>
      <div className="sample-summary">
        <div>
          <Icon name="film" />
          <strong>04</strong>
          <span>Source videos</span>
        </div>
        <div>
          <Icon name="clock" />
          <strong>18:24</strong>
          <span>Approx. total duration</span>
        </div>
        <div>
          <Icon name="camera" />
          <strong>01</strong>
          <span>Fixed intersection</span>
        </div>
        <div>
          <Icon name="sun" />
          <strong>3</strong>
          <span>Lighting conditions</span>
        </div>
      </div>
      <div className="section-heading">
        <div>
          <h2>Source videos</h2>
          <p>Four organizer-provided samples from the same intersection.</p>
        </div>
        <span className="subtle-badge">Original footage</span>
      </div>
      <div className="sample-grid">
        {samples.map((sample, i) => (
          <article className="card sample-card" key={sample.id}>
            <div className="sample-image">
              <img
                src="/images/camera.webp"
                alt="Shared reference view of the supplied intersection"
              />
              <span className="sample-number">0{i + 1}</span>
              <span className="sample-length">{time(sample.duration)}</span>
              <span className="sample-image-label">
                Shared camera reference
              </span>
            </div>
            <div className="sample-card-body">
              <div>
                <h3>{sample.name}</h3>
                <span
                  className={`badge ${available.includes(sample.id) ? "badge-green" : "badge-neutral"}`}
                >
                  {available.includes(sample.id)
                    ? states[sample.id] === "complete" ? "Analysis complete" : states[sample.id] === "running" || states[sample.id] === "queued" ? "Analysis in progress" : "Ready to analyze"
                    : "Original link"}
                </span>
              </div>
              <p>
                <Icon
                  name={i === 3 ? "moon" : i === 2 ? "cloud" : "sun"}
                  size={16}
                />
                {sample.condition}
                <span>·</span>Fixed camera
              </p>
              <div className="sample-actions">
                <button className="button" onClick={() => onSample(sample)}>
                  {available.includes(sample.id)
                    ? "Open analysis"
                    : "Open workspace"}{" "}
                  <Icon name="arrow" size={15} />
                </button>
                <a
                  className="icon-button"
                  href={sample.link}
                  target="_blank"
                  rel="noreferrer"
                  aria-label={`Open original ${sample.name}`}
                >
                  <Icon name="open" size={18} />
                </a>
              </div>
            </div>
          </article>
        ))}
      </div>
      <div className="insights-grid">
        <TrafficChart activity={report?.summary.activity} source={filename} />
        <section className="card">
          <CardHead
            icon="eye"
            title="What the scene tells us"
            subtitle="Preliminary visual observations"
          />
          <div className="observation-list">
            {[
              [
                "person",
                "Crossings need context",
                "Marked crossings and pedestrian islands must be mapped separately.",
              ],
              [
                "car",
                "Queues are part of normal traffic",
                "A car waiting at a red light is not an abandoned vehicle.",
              ],
              [
                "cloud",
                "Lighting changes what we can see",
                "Strong shadows and darker footage need separate evaluation.",
              ],
              [
                "camera",
                "One view, many occlusions",
                "Buses and nearby vehicles can temporarily hide smaller road users.",
              ],
            ].map(([icon, title, text]) => (
              <div key={title}>
                <span className="observation-icon">
                  <Icon
                    name={icon as "person" | "car" | "cloud" | "camera"}
                    size={20}
                  />
                </span>
                <div>
                  <h3>{title}</h3>
                  <p>{text}</p>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
      <p className="page-note">
        <Icon name="info" size={16} />
        Durations are rounded from the source players.{" "}
        {report
          ? "The chart uses measured tracker counts from your latest analysis; identities can split during occlusion."
          : "The chart is an illustrative preview. Run an analysis to see measured counts."}
      </p>
    </>
  );
}
