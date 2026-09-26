import { useProject } from "../hooks/useProject";
import { ReportEvidence } from "../components/ReportEvidence";
import { CardHead } from "../components/Card";
import { Icon } from "../components/Icon";
import type { IconName } from "../components/Icon";
import { classes } from "../data/classes";
import { labels } from "../types";

const pipeline: [IconName, string, string][] = [
  ["film", "Observe", "Read frames from the fixed road camera."],
  ["target", "Detect", "YOLO locates vehicles and pedestrians."],
  ["road", "Track", "ByteTrack follows movement over time."],
  ["shield", "Understand", "Scene rules identify events and risk."],
  ["chart", "Review", "Explore precise intervals and evidence."],
];

export function Report() {
  const { data, error } = useProject();
  return (
    <>
      <section className="card approach-intro">
        <div>
          <span className="eyebrow">MEASURED ON SAMPLE LABELS</span>
          <h2>System overview</h2>
          <p>
            YOLO detects road users. Tracking and camera-specific scene rules
            turn their movement into events and risk estimates. The rules were
            reviewed and tuned against our own labels of the four sample videos,
            and the accuracy table below reports the official metric on those
            labels.
          </p>
        </div>
      </section>
      <section className="card">
        <CardHead
          icon="stack"
          title="Analysis pipeline"
          subtitle="Local YOLO inference · no hosted AI calls"
        />
        <div className="pipeline">
          {pipeline.map(([icon, title, text], i) => (
            <div className="pipeline-step" key={title}>
              <span
                className={`pipeline-icon tone-${["blue", "slate", "green", "amber", "blue"][i]}`}
              >
                <Icon name={icon} size={25} />
              </span>
              <small>0{i + 1}</small>
              <h3>{title}</h3>
              <p>{text}</p>
              {i < 4 && (
                <Icon className="pipeline-arrow" name="right" size={16} />
              )}
            </div>
          ))}
        </div>
      </section>
      <div className="report-grid">
        <section className="card report-copy">
          <CardHead
            icon="check"
            title="What works today"
            subtitle="Phase 2 · connected local analysis"
          />
          <ul>
            <li>Explore an explicitly labeled event preview.</li>
            <li>Upload an MP4 to the local YOLO analysis server.</li>
            <li>
              Get tracked road users, event intervals, and an annotated video.
            </li>
            <li>Navigate the timeline, filter, review, and export results.</li>
            <li>Inspect measured occupancy, movement, and trajectory maps.</li>
            <li>
              Label a clean video and export reviewed evaluation intervals.
            </li>
          </ul>
          <span className="badge badge-green">Local pipeline implemented</span>
        </section>
        <section className="card report-copy">
          <CardHead
            icon="cpu"
            title="What comes next"
            subtitle="Validation and class coverage"
          />
          <ul>
            <li>
              Have a person re-check our model-assisted sample labels, and label
              held-out footage.
            </li>
            <li>Calibrate the anticipation score on real collision clips.</li>
            <li>
              Find positive examples for near misses, accidents, fire and
              obstacles, none of which occur in the samples.
            </li>
            <li>Measure runtime on the judging GPU.</li>
          </ul>
          <span className="badge badge-amber">
            Tuned on the samples it is measured on
          </span>
        </section>
      </div>
      <section className="card">
        <CardHead
          icon="book"
          title="The event vocabulary"
          subtitle="14 official classes · active coverage is reported with each analysis"
        />
        <div className="class-grid">
          {labels.map((label) => (
            <details key={label}>
              <summary>
                <i className={`dot bg-${classes[label].color}`} />
                <span>{classes[label].name}</span>
                <Icon name="down" size={15} />
              </summary>
              <p>{classes[label].description}</p>
              <code>{label}</code>
            </details>
          ))}
        </div>
      </section>
      {error && <p role="alert">{error}</p>}
      {data && <ReportEvidence data={data} />}
      <section className="card limitations">
        <CardHead icon="info" title="Built around honest evidence" />
        <div>
          <p>
            <strong>A single-camera system.</strong> Road rules depend on this
            intersection’s geometry. Other camera views need their own
            calibration.
          </p>
          <p>
            <strong>Prediction is not certainty.</strong> Occlusion, poor
            lighting, and ambiguous movement can affect results. The current
            preview does not assess real safety.
          </p>
          <p>
            <strong>Reproducible by design.</strong> The offline submission uses
            local weights, offline inference, and the unchanged competition
            evaluator.
          </p>
        </div>
        <a
          className="button"
          href="https://github.com/rmm-code/wiut-hackathon-task"
          target="_blank"
          rel="noreferrer"
        >
          <Icon name="github" size={17} />
          Explore the repository
          <Icon name="external" size={15} />
        </a>
      </section>
    </>
  );
}
