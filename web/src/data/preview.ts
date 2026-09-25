import type { Analysis, Label, TrafficEvent } from "../types";

const rows: [Label, number, number, number, string][] = [
  ["stopped_vehicle", 18, 53, 0.96, "Lane 02"],
  ["near_miss", 62, 81, 0.87, "Crossing A"],
  ["jaywalking", 90, 116, 0.93, "Crossing B"],
  ["red_light", 126, 147, 0.98, "Lane 01"],
  ["congestion", 144, 201, 0.95, "Northbound"],
  ["failure_to_yield", 173, 189, 0.89, "Crossing A"],
  ["solid_line_crossing", 210, 227, 0.91, "Lane 03"],
  ["wrong_way", 229, 249, 0.94, "Lane 02"],
  ["near_miss", 252, 270, 0.83, "Crossing B"],
  ["stopped_vehicle", 276, 314, 0.97, "Lane 01"],
  ["stop_line", 301, 328, 0.92, "Lane 03"],
  ["red_light", 318, 335, 0.9, "Lane 02"],
];

export function makePreview(): Analysis {
  const events: TrafficEvent[] = rows.map(
    ([label, start, end, confidence, lane], i) => ({
      id: `EV-${String(i + 1).padStart(3, "0")}`,
      label,
      start,
      end,
      confidence,
      lane,
      reviewed: i % 3 === 0,
    }),
  );
  const values = [
    0.08, 0.1, 0.07, 0.11, 0.19, 0.46, 0.78, 0.31, 0.12, 0.11, 0.19, 0.25, 0.54,
    0.84, 0.42, 0.16, 0.1, 0.16, 0.28, 0.19, 0.11, 0.08, 0.17, 0.3, 0.64, 0.8,
    0.32, 0.17, 0.11, 0.14, 0.31, 0.5, 0.72, 0.2, 0.09,
  ];
  return {
    origin: "preview",
    events,
    risk: values.map((score, i) => [i * 10, score]),
  };
}

export const traffic = [
  { time: "00:00", cars: 38, buses: 13, people: 24 },
  { time: "01:00", cars: 62, buses: 18, people: 32 },
  { time: "02:00", cars: 50, buses: 14, people: 27 },
  { time: "03:00", cars: 74, buses: 21, people: 39 },
  { time: "04:00", cars: 57, buses: 17, people: 32 },
  { time: "05:00", cars: 44, buses: 12, people: 23 },
];
