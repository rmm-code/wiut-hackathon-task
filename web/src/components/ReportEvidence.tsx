import { CardHead } from "./Card";
import { classes } from "../data/classes";
import { time } from "../lib/format";
import type { DevsetReport, ProjectInfo } from "../types";

const failures = [
  {
    image: "alignment",
    title: "Camera match rejected the right scene",
    source: "C3902 · 00:00",
    text: "The first run rejected this camera and disabled scene rules. A second matching scale fixed the rejection without lowering the geometric checks. The video was then rerun in full.",
  },
  {
    image: "signal",
    title: "A red light can look dark",
    source: "C3896 · 00:10",
    text: "The original brightness threshold returned unknown for this visibly red lamp. A tightly mapped signal region and measured brightness threshold recover red/green phases. Hidden signal heads remain unmapped.",
  },
  {
    image: "collision",
    title: "An appearance box does not prove a crash",
    source: "C3902 · 00:02",
    text: "The accident specialist proposed a collision at 1.07–3.20 seconds. Review showed two cars overlapping in perspective and driving on. Accident candidates now also require the vehicles to come to rest, which removes this false alarm.",
  },
];

function Devset({ report }: { report: DevsetReport }) {
  return (
    <section className="card">
      <CardHead
        icon="check"
        title="Accuracy on our sample labels"
        subtitle={`Official metric · ${report.labelled_events} labelled events in ${report.videos.length} sample videos`}
      />
      <div className="report-table">
        <table>
          <thead>
            <tr>
              <th>Class</th>
              <th>Labelled</th>
              <th>Predicted</th>
              <th>Precision</th>
              <th>Recall</th>
              <th>F1 @0.3</th>
              <th>F1 @0.5</th>
              <th>F1 @0.7</th>
            </tr>
          </thead>
          <tbody>
            {report.classes.map((row) => (
              <tr key={row.label}>
                <td>{classes[row.label].name}</td>
                <td>{row.labelled}</td>
                <td>{row.predicted}</td>
                <td>{row.precision.toFixed(2)}</td>
                <td>{row.recall.toFixed(2)}</td>
                <td>{row["f1_0.3"].toFixed(2)}</td>
                <td>{row["f1_0.5"].toFixed(2)}</td>
                <td>{row["f1_0.7"].toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="analysis-body">
        <p>
          Score A on these labels: <strong>{report.score_a.toFixed(3)}</strong>.
          Precision and recall are at temporal IoU 0.5. The labels are our own
          model-assisted review of the organizer samples, not the hidden test
          set, and the same samples were used to tune the rules, so treat these
          numbers as an upper bound.
        </p>
      </div>
    </section>
  );
}

export function ReportEvidence({ data }: { data: ProjectInfo }) {
  return (
    <>
      {data.devset && <Devset report={data.devset} />}
      <section className="card">
        <CardHead
          icon="chart"
          title="Measured sample results"
          subtitle="Permanent results · model candidates, not reviewed labels"
        />
        <div className="report-table">
          <table>
            <thead>
              <tr>
                <th>Video</th>
                <th>Duration</th>
                <th>Frames</th>
                <th>Events</th>
                <th>Tracked IDs</th>
                <th>Analysis time</th>
              </tr>
            </thead>
            <tbody>
              {data.samples.map((sample) => (
                <tr key={sample.id}>
                  <td>{sample.name}</td>
                  <td>{time(sample.duration)}</td>
                  <td>{sample.frames.toLocaleString()}</td>
                  <td>{sample.events}</td>
                  <td>{sample.road_users.toLocaleString()}</td>
                  <td>{sample.runtime.toFixed(1)}s</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="analysis-body">
          <p>
            All source videos are 3840 × 2160 at about 29.97 fps. Tracked IDs
            can split during occlusion, so they are not ground-truth counts.
            These are web-pipeline runtimes on Apple M5; the judging machine and
            independent two-pass harness need separate measurement.
          </p>
        </div>
      </section>
      <section className="card">
        <CardHead
          icon="eye"
          title="What failed, and what changed"
          subtitle="Concrete evidence from organizer footage"
        />
        <div className="failure-grid">
          {failures.map((item) => (
            <article key={item.image}>
              <img
                src={`/evidence/${item.image}.jpg`}
                alt={item.title}
                loading="lazy"
              />
              <small>{item.source}</small>
              <h3>{item.title}</h3>
              <p>{item.text}</p>
            </article>
          ))}
        </div>
      </section>
      <section className="card">
        <CardHead
          icon="shield"
          title="Class coverage"
          subtitle="Implementation is separate from camera evidence and measured accuracy"
        />
        <div className="coverage-report">
          {data.coverage.map((item) => (
            <div key={item.label}>
              <strong>{classes[item.label].name}</strong>
              <span
                className={`badge ${item.enabled ? "badge-green" : "badge-amber"}`}
              >
                {item.enabled
                  ? "Candidate detection active"
                  : "Needs camera facts"}
              </span>
              <p>{item.reason}</p>
            </div>
          ))}
        </div>
        <div className="analysis-body">
          <p>
            All 14 labels have implementation paths. A rule is applied only when
            its required observations and scene facts are available, and a class
            stays off when review found no reliable detections.
          </p>
        </div>
      </section>
      <section className="card">
        <CardHead
          icon="cpu"
          title="Models, data and licences"
          subtitle="Pretrained open weights · no training or fine-tuning performed by this team"
        />
        <div className="coverage-report">
          {data.models.map((model) => (
            <div key={model.name}>
              <h3>{model.name}</h3>
              <p>
                {model.purpose}. {model.method}.
              </p>
              <p>
                <a href={model.dataset_url} target="_blank" rel="noreferrer">
                  {model.dataset}
                </a>{" "}
                — {model.dataset_license}
              </p>
              <p>{model.model_license}</p>
              <a href={model.source} target="_blank" rel="noreferrer">
                Source model and attribution
              </a>
            </div>
          ))}
        </div>
        <div className="analysis-body">
          <p>
            Event geometry, temporal merging, signal interpretation and
            closest-approach risk are hand-written rules. Source-model benchmark
            scores do not measure performance on this camera.
          </p>
        </div>
      </section>
      <section className="card">
        <CardHead
          icon="download"
          title="Downloads & reproducibility"
          subtitle="Public sample endpoints do not require an upload session"
        />
        <div className="analysis-body">
          <div className="study-tabs">
            <a
              className="button"
              href={data.repository}
              target="_blank"
              rel="noreferrer"
            >
              Repository
            </a>
            <a className="button" href={data.predictions} download>
              All sample predictions
            </a>
            <a className="button" href={data.manifest} download>
              Weight checksums
            </a>
          </div>
          <div className="study-tabs">
            {data.models.map((model) => (
              <a
                className="button small"
                key={model.name}
                href={model.download}
              >
                {model.name} weights
              </a>
            ))}
          </div>
          <p>
            Python, NumPy, Torch and OpenCV seeds are fixed at 42. CPU, MPS and
            CUDA can differ numerically. The sample archive has no automatic
            expiry; private uploads are removed after 24 hours. Downloads on
            this server become internet-accessible when the backend is publicly
            deployed.
          </p>
        </div>
      </section>
    </>
  );
}
