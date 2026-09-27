import { Icon } from "../components/Icon";
import { useProject } from "../hooks/useProject";

export function Team() {
  const { data, error } = useProject();
  return (
    <>
      <section className="card team-intro">
        <span className="eyebrow">WIUT HACKATHON 2026</span>
        <h2>Our team</h2>
        <p>
          Three people building a reviewable picture of traffic from one fixed
          camera.
        </p>
      </section>
      {error && <p role="alert">{error}</p>}
      {!data && !error && <p role="status">Loading team details…</p>}
      <div className="team-grid">
        {data?.team.map((member) => (
          <section className="card role-card" key={member.name}>
            {member.photo ? (
              <img
                className="member-photo"
                src={member.photo}
                alt={member.name}
                width={88}
                height={88}
                loading="lazy"
              />
            ) : (
              <span className="role-icon tone-slate">
                <Icon name="person" size={28} />
              </span>
            )}
            <h3>{member.name}</h3>
            <span className="badge badge-neutral">{member.role}</span>
            {member.contribution && <p>{member.contribution}</p>}
            <div className="study-tabs">
              {Object.entries(member.links).map(([label, url]) => (
                <a
                  className="button small"
                  href={url}
                  target="_blank"
                  rel="noreferrer"
                  key={label}
                >
                  {label}
                  <Icon name="external" size={14} />
                </a>
              ))}
            </div>
          </section>
        ))}
      </div>
      <section className="card report-copy">
        <div className="analysis-body">
          <p>
            Names, roles and profile links were supplied by the team members.
          </p>
          <a
            className="button"
            href={
              data?.repository ??
              "https://github.com/rmm-code/wiut-hackathon-task"
            }
            target="_blank"
            rel="noreferrer"
          >
            <Icon name="github" size={17} />
            Project repository
          </a>
        </div>
      </section>
    </>
  );
}
