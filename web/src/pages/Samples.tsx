import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { samples } from "../data/samples";
import { examples } from "../data/examples";
import { classes } from "../data/classes";
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
  const [archived, setArchived] = useState<string[]>([]);
  const [states, setStates] = useState<Record<string, string | null>>({});
  const [available, setAvailable] = useState<string[]>([]);
  useEffect(() => {
    api
      .samples()
      .then((items) => {
        setArchived(
          items.filter((item) => item.archived).map((item) => item.id),
        );
        setAvailable(
          items.filter((item) => item.available).map((item) => item.id),
        );
        setStates(
          Object.fromEntries(items.map((item) => [item.id, item.state])),
        );
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
                src={
                  archived.includes(sample.id)
                    ? `/api/samples/${sample.id}/eda/poster`
                    : "/images/camera.webp"
                }
                alt={
                  archived.includes(sample.id)
                    ? `Annotated first frame of ${sample.name}`
                    : "Shared reference view of the supplied intersection"
                }
              />
              <span className="sample-number">0{i + 1}</span>
              <span className="sample-length">{time(sample.duration)}</span>
              <span className="sample-image-label">
                {archived.includes(sample.id)
                  ? "Saved sample · no expiry"
                  : "Shared camera reference"}
              </span>
            </div>
            <div className="sample-card-body">
              <div>
                <h3>{sample.name}</h3>
                <span
                  className={`badge ${available.includes(sample.id) ? "badge-green" : "badge-neutral"}`}
                >
                  {available.includes(sample.id)
                    ? states[sample.id] === "complete"
                      ? "Analysis complete"
                      : states[sample.id] === "running" ||
                          states[sample.id] === "queued"
                        ? "Analysis in progress"
                        : "Ready to analyze"
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
            title="What the samples taught us"
            subtitle="Measured findings that shaped the rules"
          />
          <div className="observation-list">
            {[
              [
                "signal",
                "One lamp, one approach",
                "98% of the 479 south-east stop-line crossings happen on the median lamp's green. North-west traffic ignores it, so only one approach gets signal rules.",
              ],
              [
                "turn",
                "Lanes decide legality",
                "20 of 25 right turns start in the kerb lane and 10 of 11 U-turns in the median lane. Clause 56 turns that into the illegal-turn rule.",
              ],
              [
                "car",
                "Standing still is usually normal",
                "Every vehicle stationary for 10 s was queueing, waiting to turn in the junction box, or parked at the far kerb. Those zones are excluded.",
              ],
              [
                "person",
                "Jaywalking is a shortcut",
                "Pedestrians cut across the slip lane between zebras A and C and walk beside zebra B. Feet on zebra paint are not jaywalking.",
              ],
              [
                "moon",
                "Dusk dims the lamp",
                "C3905 is filmed at dusk, so the lamp reader uses lower thresholds (saturation 100, value 50) that also hold in daylight.",
              ],
            ].map(([icon, title, text]) => (
              <div key={title}>
                <span className="observation-icon">
                  <Icon
                    name={icon as "signal" | "turn" | "car" | "person" | "moon"}
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
      <section className="card">
        <CardHead
          icon="check"
          title="Examples of each detected class"
          subtitle="Verified detections from the sample videos · open a sample to play the full event"
        />
        <div className="example-list">
          {examples.map((item) => (
            <figure key={item.label}>
              <img
                src={`/examples/${item.label}.jpg`}
                alt={`${classes[item.label].name} in ${item.sample}`}
                loading="lazy"
              />
              <figcaption>
                <strong>{classes[item.label].name}</strong>
                <span>
                  {item.sample.replace(".MP4", "")} · {time(item.start)}–
                  {time(item.end)}
                </span>
                <p>{item.text}</p>
              </figcaption>
            </figure>
          ))}
        </div>
      </section>
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
