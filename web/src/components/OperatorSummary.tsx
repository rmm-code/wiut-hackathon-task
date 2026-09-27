import { CardHead } from "./Card";
import { classes } from "../data/classes";
import { time } from "../lib/format";
import type { Label, TrafficEvent } from "../types";

function Bars({ rows }: { rows: [string, number][] }) {
  const top = Math.max(1, ...rows.map(([, count]) => count));
  return (
    <ul className="operator-bars">
      {rows.map(([name, count]) => (
        <li key={name}>
          <span>{name}</span>
          <i style={{ width: `${(100 * count) / top}%` }} />
          <b>{count}</b>
        </li>
      ))}
    </ul>
  );
}

function tally(values: string[]): [string, number][] {
  const counts = new Map<string, number>();
  for (const value of values) counts.set(value, (counts.get(value) ?? 0) + 1);
  return [...counts].sort((a, b) => b[1] - a[1]);
}

// What an operator scans first: which violations, where, and when.
export function OperatorSummary({
  events,
  duration,
}: {
  events: TrafficEvent[];
  duration: number;
}) {
  if (!events.length) return null;
  const minutes = Math.max(1, Math.ceil(duration / 60));
  const perMinute: [string, number][] = Array.from({ length: minutes }, (_, i) => [
    `${time(i * 60)}–${time(Math.min(duration, (i + 1) * 60))}`,
    events.filter((event) => event.start >= i * 60 && event.start < (i + 1) * 60).length,
  ]);
  return (
    <section className="card">
      <CardHead
        icon="bars"
        title="Operator summary"
        subtitle="Events in this video by class, by location and by minute"
      />
      <div className="operator-grid">
        <div>
          <h3>By class</h3>
          <Bars rows={tally(events.map((event) => classes[event.label as Label].name))} />
        </div>
        <div>
          <h3>By location</h3>
          <Bars rows={tally(events.map((event) => event.lane ?? "Not localised"))} />
        </div>
        <div>
          <h3>By minute</h3>
          <Bars rows={perMinute} />
        </div>
      </div>
    </section>
  );
}
