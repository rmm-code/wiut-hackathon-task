import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { samples } from "../data/samples";
import { examples } from "../data/examples";
import { classes } from "../data/classes";
import { time } from "../lib/format";
import { Icon } from "../components/Icon";
import { CardHead } from "../components/Card";
import { TrafficChart } from "../components/Charts";
import { useProject } from "../hooks/useProject";
import type { EngineReport, Video } from "../types";

const kinds = ["car", "person", "bus", "truck", "bicycle", "motorcycle"];
const maps = [
  ["occupancy", "Where road users spend time"],
  ["motion", "Where the image moves"],
  ["trajectories", "Tracked paths"],
] as const;

export function Samples({
  onSample,
  report,
  filename,
}: {
  onSample: (video: Video) => void;
  report?: EngineReport;
  filename?: string;
}) {
  const { data: project } = useProject();
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
      {project?.samples.length ? (
        <section className="card">
          <CardHead
            icon="chart"
            title="The samples, measured"
            subtitle="From our analysis of every frame · brightness is the mean grey level (0–255)"
          />
          <div className="report-table">
            <table>
              <thead>
                <tr>
                  <th>Video</th>
                  <th>Resolution</th>
                  <th>fps</th>
                  <th>Duration</th>
                  <th>Brightness</th>
                  {kinds.map((kind) => (
                    <th key={kind}>{kind[0].toUpperCase() + kind.slice(1)}s</th>
                  ))}
                  <th>Events</th>
                </tr>
              </thead>
              <tbody>
                {project.samples.map((sample) => (
                  <tr key={sample.id}>
                    <td>{sample.name.replace(".MP4", "")}</td>
                    <td>
                      {sample.width} × {sample.height}
                    </td>
                    <td>{sample.fps.toFixed(2)}</td>
                    <td>{time(sample.duration)}</td>
                    <td>{sample.brightness.toFixed(0)}</td>
                    {kinds.map((kind) => (
                      <td key={kind}>{sample.by_class[kind] ?? 0}</td>
                    ))}
                    <td>{sample.events}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="analysis-body">
            <p>
              Counts are unique tracker identities, so an occluded road user can
              be counted twice. Every sample shares one fixed view, so a single
              camera map serves all four.
            </p>
          </div>
        </section>
      ) : null}
      <section className="card">
        <CardHead
          icon="road"
          title="Lanes and traffic directions"
          subtitle="Mapped on an empty-road background: the median of 45 frames of C3896"
        />
        <div className="lanes-map">
          <img
            src="/images/lanes.jpg"
            alt="The intersection with each carriageway's direction of travel, the stop line, solid lane lines and crossings"
            loading="lazy"
          />
          <ul>
            <li>
              <strong>South-east approach (orange).</strong> Five lanes run to the
              stop line (red); 479 of 480 tracked stop-line crossings in the four
              samples move this way. White lines are the solid lane markings.
            </li>
            <li>
              <strong>North-west carriageway (green).</strong> Above the raised
              median; every through track moves north-west.
            </li>
            <li>
              <strong>North-west approach (blue).</strong> Enters from the right
              and crosses crossing B. U-turns legitimately swing through this
              junction mouth, so it is left out of wrong-way checks.
            </li>
          </ul>
        </div>
      </section>
      {project?.samples.length ? (
        <section className="card">
          <CardHead
            icon="eye"
            title="Occupancy, motion and trajectories for every sample"
            subtitle="Measured maps · click a map to open it full size"
          />
          <div className="eda-grid">
            {project.samples.map((sample) =>
              maps.map(([kind, caption]) => (
                <figure key={`${sample.id}-${kind}`}>
                  <a
                    href={`/api/samples/${sample.id}/eda/${kind}`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    <img
                      src={`/api/samples/${sample.id}/eda/${kind}`}
                      alt={`${caption} in ${sample.name}`}
                      loading="lazy"
                    />
                  </a>
                  <figcaption>
                    {sample.name.replace(".MP4", "")} · {caption}
                  </figcaption>
                </figure>
              )),
            )}
          </div>
        </section>
      ) : null}
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
    </>
  );
}
