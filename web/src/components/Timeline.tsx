import { CardHead, Empty } from "./Card";
import { Icon } from "./Icon";
import { time } from "../lib/format";
import { classes } from "../data/classes";
import type { Label, TrafficEvent } from "../types";
import type { IconName } from "./Icon";

const groups: { name: string; icon: IconName; labels: Label[] }[] = [
  {
    name: "Safety",
    icon: "shield",
    labels: ["accident", "near_miss", "fire_smoke"],
  },
  {
    name: "Violations",
    icon: "signal",
    labels: ["red_light", "wrong_way", "illegal_turn", "illegal_u_turn"],
  },
  {
    name: "Pedestrians",
    icon: "person",
    labels: ["jaywalking", "failure_to_yield"],
  },
  { name: "Stopped vehicles", icon: "car", labels: ["stopped_vehicle"] },
  {
    name: "Road activity",
    icon: "road",
    labels: ["congestion", "road_obstacle", "solid_line_crossing", "stop_line"],
  },
];

function lanes(events: TrafficEvent[]): TrafficEvent[][] {
  const result: TrafficEvent[][] = [];
  for (const event of [...events].sort((a, b) => a.start - b.start)) {
    const lane = result.find((row) => row.at(-1)!.end <= event.start);
    if (lane) lane.push(event);
    else result.push([event]);
  }
  return result.length ? result : [[]];
}

export function Timeline({
  events,
  duration,
  position,
  selected,
  onSelect,
  onSeek,
}: {
  events: TrafficEvent[];
  duration: number;
  position: number;
  selected: string | null;
  onSelect: (event: TrafficEvent) => void;
  onSeek: (position: number) => void;
}) {
  const ticks = Array.from({ length: 6 }, (_, i) => (duration * i) / 5);
  return (
    <section className="card timeline-card" id="timeline">
      <CardHead
        icon="clock"
        title="Event timeline"
        subtitle="Events by type and time. Click one to jump the video to it."
        action={
          <span className="subtle-badge">
            <Icon name="film" size={14} />
            {time(duration)}
          </span>
        }
      />
      {!events.length ? (
        <Empty
          title="A clear timeline starts here"
          text="Events will appear here when results are available for this video."
          icon="clock"
        />
      ) : (
        <div className="timeline-scroll">
          <div className="timeline-grid">
            <div className="timeline-ruler">
              <span>EVENT GROUP</span>
              <div>
                {ticks.map((tick, i) => (
                  <button
                    key={i}
                    style={{ left: `${i * 20}%` }}
                    onClick={() => onSeek(tick)}
                  >
                    {time(tick)}
                  </button>
                ))}
              </div>
            </div>
            <div className="timeline-rows">
              {groups.map((group) => (
                <div className="timeline-row" key={group.name}>
                  <div className="timeline-label">
                    <Icon name={group.icon} size={17} />
                    <span>{group.name}</span>
                  </div>
                  <div className="timeline-tracks">
                    {lanes(
                      events.filter((e) => group.labels.includes(e.label)),
                    ).map((lane, i) => (
                      <div className="timeline-lane" key={i}>
                        {lane.map((event) => (
                          <button
                            key={event.id}
                            className={`event-segment segment-${classes[event.label].color} ${selected === event.id ? "selected" : ""}`}
                            style={{
                              left: `${(event.start / duration) * 100}%`,
                              width: `${((event.end - event.start) / duration) * 100}%`,
                            }}
                            onClick={() => onSelect(event)}
                            title={`${classes[event.label].name} · ${time(event.start)}–${time(event.end)}`}
                            aria-label={`${classes[event.label].name}, ${time(event.start)} to ${time(event.end)}`}
                          >
                            <span>{classes[event.label].name}</span>
                          </button>
                        ))}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
              <div className="timeline-cursor-track">
                <span
                  className="timeline-cursor"
                  style={{ left: `${(position / duration) * 100}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      )}
      <div className="timeline-footer">
        <span>
          <Icon name="info" size={14} />
          Different event types can overlap.
        </span>
        <span>Video time · mm:ss</span>
      </div>
    </section>
  );
}
