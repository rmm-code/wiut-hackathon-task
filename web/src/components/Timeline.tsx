import { CardHead, Empty } from "./Card";
import { Icon } from "./Icon";
import { time } from "../lib/format";
import { classes } from "../data/classes";
import { labels } from "../types";
import type { TrafficEvent } from "../types";

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
        subtitle="One row for each of the 14 event classes. Click an event to jump the video to it."
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
        <div className="timeline-grid">
          <div className="timeline-ruler">
            <span>EVENT CLASS</span>
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
            {labels.map((label) => {
              const found = events.filter((e) => e.label === label);
              return (
                <div
                  className={`timeline-row ${found.length ? "" : "is-empty"}`}
                  key={label}
                >
                  <div className="timeline-label">
                    <span>{classes[label].name}</span>
                    <b>{found.length}</b>
                  </div>
                  <div className="timeline-tracks">
                    {lanes(found).map((lane, i) => (
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
                          />
                        ))}
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
            <div className="timeline-cursor-track">
              <span
                className="timeline-cursor"
                style={{ left: `${(position / duration) * 100}%` }}
              />
            </div>
          </div>
        </div>
      )}
      <div className="timeline-footer">
        <span className="timeline-legend">
          <span>
            <i className="dot bg-red" />
            Critical
          </span>
          <span>
            <i className="dot bg-amber" />
            Warning
          </span>
          <span>
            <i className="dot bg-green" />
            Notice
          </span>
        </span>
        <span>Video time · mm:ss</span>
      </div>
    </section>
  );
}
