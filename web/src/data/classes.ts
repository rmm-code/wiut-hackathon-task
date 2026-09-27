import type { Label, Level } from "../types";

export const classes: Record<
  Label,
  { name: string; level: Level; color: string; description: string }
> = {
  accident: {
    name: "Collision",
    level: "critical",
    color: "red",
    description:
      "Contact between two or more road users, or a road user and a fixed object.",
  },
  near_miss: {
    name: "Near miss",
    level: "warning",
    color: "amber",
    description: "Sharp braking or swerving to avoid a collision; no contact.",
  },
  red_light: {
    name: "Red-light running",
    level: "critical",
    color: "red",
    description: "A vehicle crosses the stop line while its signal is red.",
  },
  wrong_way: {
    name: "Wrong-way driving",
    level: "critical",
    color: "red",
    description:
      "A vehicle moves against the traffic direction of its lane, including driving in the oncoming lane.",
  },
  illegal_u_turn: {
    name: "Illegal U-turn",
    level: "warning",
    color: "amber",
    description: "A U-turn where the road markings or signs prohibit it.",
  },
  stopped_vehicle: {
    name: "Stopped vehicle",
    level: "notice",
    color: "green",
    description:
      "A vehicle stationary on the carriageway for 10 s or more, not in a queue at a signal.",
  },
  jaywalking: {
    name: "Pedestrian on roadway",
    level: "warning",
    color: "amber",
    description: "A pedestrian on the carriageway outside a crossing.",
  },
  failure_to_yield: {
    name: "Not yielding to a pedestrian",
    level: "warning",
    color: "amber",
    description:
      "A vehicle drives through a crossing while a pedestrian is on it or stepping onto it.",
  },
  illegal_turn: {
    name: "Illegal turn",
    level: "warning",
    color: "amber",
    description: "A turn from the wrong lane or in a prohibited direction.",
  },
  solid_line_crossing: {
    name: "Solid line crossing",
    level: "warning",
    color: "amber",
    description: "A lane change or manoeuvre across a solid marking.",
  },
  stop_line: {
    name: "Stop-line violation",
    level: "notice",
    color: "green",
    description:
      "A vehicle stops past the stop line on red without entering the intersection.",
  },
  congestion: {
    name: "Congestion",
    level: "notice",
    color: "green",
    description:
      "Traffic at a standstill or crawling across all lanes of a direction.",
  },
  road_obstacle: {
    name: "Obstacle on road",
    level: "warning",
    color: "amber",
    description: "Debris, animal, or fallen object on the carriageway.",
  },
  fire_smoke: {
    name: "Fire or smoke",
    level: "critical",
    color: "red",
    description: "Visible fire or smoke from a vehicle or on the road.",
  },
};
