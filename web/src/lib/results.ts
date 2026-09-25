import { labels } from "../types.ts";
import type { Analysis, Label, RiskPoint } from "../types";

const isNumber = (n: unknown): n is number =>
  typeof n === "number" && Number.isFinite(n);
const isObject = (v: unknown): v is Record<string, unknown> =>
  typeof v === "object" && v !== null && !Array.isArray(v);

export function parseResults(
  raw: unknown,
  filename: string,
  duration: number,
): Analysis {
  if (!isObject(raw) || !isObject(raw.videos))
    throw new Error(
      "Use the official predictions JSON with a “videos” object.",
    );
  const entry = raw.videos[filename];
  if (!isObject(entry))
    throw new Error(
      `No results found for ${filename}. The video filename must match exactly.`,
    );
  if (!Array.isArray(entry.events))
    throw new Error("The video must contain an events list.");
  const lastEnd = new Map<string, number>();
  const events = entry.events
    .map((row: unknown, i: number) => {
      if (!Array.isArray(row) || row.length !== 3)
        throw new Error(`Event ${i + 1} must contain start, end, and label.`);
      const [start, end, label] = row;
      if (
        !isNumber(start) ||
        !isNumber(end) ||
        start < 0 ||
        start >= end ||
        end > duration + 0.001
      ) {
        throw new Error(
          `Event ${i + 1} has invalid timestamps for this video.`,
        );
      }
      if (!labels.includes(label as Label))
        throw new Error(`Event ${i + 1} has an unknown class.`);
      return {
        id: `EV-${String(i + 1).padStart(3, "0")}`,
        label: label as Label,
        start,
        end,
        reviewed: false,
      };
    })
    .sort((a, b) => a.start - b.start);
  for (const event of events) {
    if (event.start < (lastEnd.get(event.label) ?? -1))
      throw new Error(`Overlapping ${event.label} events are not allowed.`);
    lastEnd.set(event.label, event.end);
  }
  const risk: RiskPoint[] = [];
  if (entry.risk !== undefined && !Array.isArray(entry.risk))
    throw new Error("Risk must be a list of timestamp/score pairs.");
  for (const row of (entry.risk ?? []) as unknown[]) {
    if (
      !Array.isArray(row) ||
      row.length !== 2 ||
      !isNumber(row[0]) ||
      !isNumber(row[1]) ||
      row[0] < 0 ||
      row[0] > duration ||
      row[1] < 0 ||
      row[1] > 1 ||
      row[0] < (risk.at(-1)?.[0] ?? -1)
    ) {
      throw new Error(
        "Risk timestamps must be ordered and within the video. Scores must be between 0 and 1.",
      );
    }
    risk.push([row[0], row[1]]);
  }
  return { origin: "imported", events, risk };
}
