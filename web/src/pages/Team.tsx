import { Icon } from "../components/Icon";
import type { IconName } from "../components/Icon";

const roles: [IconName, string, string, string][] = [
  [
    "target",
    "Computer vision",
    "Detection, tracking, and anticipation.",
    "slate",
  ],
  [
    "bars",
    "Data & evaluation",
    "Scene calibration, labels, and honest metrics.",
    "blue",
  ],
  [
    "grid",
    "Product & engineering",
    "The review experience and reliable delivery.",
    "green",
  ],
];

export function Team() {
  return (
    <>
      <section className="card team-intro">
        <span className="eyebrow">WIUT HACKATHON 2026</span>
        <h2>Team overview</h2>
        <p>
          A computer vision project connecting road-camera footage with an
          understandable, reviewable picture of traffic.
        </p>
        <a
          className="button"
          href="https://github.com/rmm-code/wiut-hackathon-task"
          target="_blank"
          rel="noreferrer"
        >
          <Icon name="github" size={18} />
          Project repository
          <Icon name="external" size={16} />
        </a>
      </section>
      <div className="section-heading">
        <div>
          <h2>Responsibilities</h2>
          <p>Proposed responsibilities for a three-person team.</p>
        </div>
      </div>
      <div className="team-grid">
        {roles.map(([icon, title, description, color]) => (
          <section className="card role-card" key={title}>
            <span className={`role-icon tone-${color}`}>
              <Icon name={icon} size={31} />
            </span>
            <h3>{title}</h3>
            <p>{description}</p>
            <span className="badge badge-neutral">Member to be confirmed</span>
          </section>
        ))}
      </div>
      <div className="team-note">
        <Icon name="team" size={24} />
        <div>
          <h3>Team details pending</h3>
          <p>
            Member names, contributions, and portfolio links will be added after
            the team confirms its details.
          </p>
        </div>
      </div>
    </>
  );
}
