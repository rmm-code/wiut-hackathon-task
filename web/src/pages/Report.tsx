import { useProject } from "../hooks/useProject";
import { ReportEvidence } from "../components/ReportEvidence";
import { CardHead } from "../components/Card";
import { Icon } from "../components/Icon";
import type { IconName } from "../components/Icon";
import { classes } from "../data/classes";
import { labels } from "../types";

type Kind = "Learned" | "Rule-based";

const pipeline: [IconName, string, string, Kind][] = [
  ["film", "Sample frames", "Decode the video on a background thread and analyse every 4th frame, about 7.5 per second.", "Rule-based"],
  ["target", "Detect", "Pretrained YOLO11s (COCO) finds cars, buses, trucks, motorcycles, bicycles and people.", "Learned"],
  ["road", "Track", "ByteTrack links detections into tracks. Without tracking, Score A falls to 0.", "Rule-based"],
  ["camera", "Align the camera", "SIFT and RANSAC match the view to the reference; later frames are tried if the first fails.", "Rule-based"],
  ["signal", "Read the signal", "The one visible signal head is read from its lamp colours, debounced over time.", "Rule-based"],
  ["shield", "Scene rules", "One small rule per class reads tracks against the lanes, crossings and stop line.", "Rule-based"],
  ["eye", "Specialists", "Accident YOLO11x and fire/smoke YOLO26n run once a second; tracks must confirm them.", "Learned"],
  ["stack", "Segments", "Fragments are merged and blips dropped; the result is the Part A event list.", "Rule-based"],
  ["chart", "Risk (Part B)", "A causal closest-approach score between tracks, calibrated so 0.5 is the alarm level.", "Rule-based"],
];

const worked = [
  "Score A 0.777 on our labels of the four samples; the predictions it replaced scored 0.085.",
  "Stop line and red light: F1 1.00. Illegal turn 0.82, solid-line crossing 0.67.",
  "Mapping the camera on an empty-road background (a median of 45 frames) removed most false alarms.",
  "A debounced signal reading with two timing tests removed every false red-light run.",
  "Traffic rule clause 56 found five wrong-lane right turns and showed that U-turns at the median are legal.",
  "It fits the time budget: 35% of it on an RTX 4060, 61% on two CPU cores.",
];

const failed = [
  "Jaywalking (F1 0.57): foot points beside zebra paint, or behind cars, flicker across the crossing edge.",
  "Failure to yield over-reports (33 found, 22 labelled): people waiting at a kerb still trigger it.",
  "Stopped vehicles: every candidate was normal traffic, so the rule has no positive example.",
  "Near miss is off: every detection in the samples was a false alarm.",
  "The accident specialist's only confirmed detection was two cars overlapping in perspective.",
  "Part B cannot be measured: the samples contain no accident.",
];

export function Report() {
  const { data, error } = useProject();
  return (
    <>
      <section className="card approach-intro">
        <div>
          <span className="eyebrow">THE PROBLEM</span>
          <h2>System overview</h2>
          <p>
            One fixed road camera. Part A reports every traffic event as a time
            segment in one of 14 official classes, scored by macro F1 over
            temporal IoU 0.3, 0.5 and 0.7 (70% of the model score). Part B gives,
            at every frame and from past frames only, the probability that an
            accident starts within 5 seconds (30%). Our approach: pretrained YOLO
            detects road users, and tracking plus camera-specific rules turn
            their movement into events and risk. The rules were tuned on our own
            labels of the four samples; the tables below report the official
            metric on those labels.
          </p>
        </div>
      </section>
      <section className="card">
        <CardHead
          icon="stack"
          title="Analysis pipeline"
          subtitle="Steps 1–8 give the Part A events; step 9 is Part B · open weights, no hosted AI"
        />
        <div className="pipeline">
          {pipeline.map(([icon, title, text, kind], i) => (
            <div className="pipeline-step" key={title}>
              <span
                className={`pipeline-icon tone-${kind === "Learned" ? "blue" : "slate"}`}
              >
                <Icon name={icon} size={25} />
              </span>
              <small>
                0{i + 1} ·{" "}
                <span className={`badge ${kind === "Learned" ? "badge-blue" : "badge-neutral"}`}>
                  {kind}
                </span>
              </small>
              <h3>{title}</h3>
              <p>{text}</p>
              {i < pipeline.length - 1 && (
                <Icon className="pipeline-arrow" name="right" size={16} />
              )}
            </div>
          ))}
        </div>
      </section>
      <div className="report-grid">
        <section className="card report-copy">
          <CardHead icon="check" title="What worked" subtitle="Measured on our sample labels" />
          <ul>
            {worked.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
          <span className="badge badge-green">13 of 14 classes active</span>
        </section>
        <section className="card report-copy">
          <CardHead icon="warning" title="What did not work" subtitle="Still open" />
          <ul>
            {failed.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
          <span className="badge badge-amber">
            Tuned on the samples it is measured on
          </span>
        </section>
        <section className="card report-copy">
          <CardHead
            icon="cpu"
            title="What we would do next"
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
            <li>Measure runtime on a T4 with an 8-core host.</li>
          </ul>
          <a
            className="button small report-link"
            href="https://github.com/rmm-code/wiut-hackathon-task/blob/v1.0.0/docs/report.md"
            target="_blank"
            rel="noreferrer"
          >
            Full one-page report
            <Icon name="external" size={14} />
          </a>
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
