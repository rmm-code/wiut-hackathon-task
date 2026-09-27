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
      "Visible contact between road users or a road user and a fixed object.",
  },
  near_miss: {
    name: "Near miss",
    level: "warning",
    color: "amber",
    description:
      "Sharp braking or swerving to avoid a collision, with no contact.",
  },
  red_light: {
    name: "Red-light running",
    level: "critical",
    color: "red",
    description:
      "A vehicle crosses its stop line on red and enters the intersection. The interval ends when it clears the intersection.",
  },
  wrong_way: {
    name: "Wrong-way driving",
    level: "critical",
    color: "red",
    description: "A vehicle moves against the permitted direction of its lane.",
  },
  illegal_u_turn: {
    name: "Illegal U-turn",
    level: "warning",
    color: "amber",
    description: "A U-turn where markings or signs prohibit the manoeuvre.",
  },
  stopped_vehicle: {
    name: "Stopped vehicle",
    level: "notice",
    color: "green",
    description:
      "Stationary on the carriageway for at least 10 seconds, outside a signal queue.",
  },
  jaywalking: {
    name: "Pedestrian on road",
    level: "warning",
    color: "amber",
    description:
      "A pedestrian enters the carriageway outside a marked crossing.",
  },
  failure_to_yield: {
    name: "Failure to yield",
    level: "warning",
    color: "amber",
    description:
      "A vehicle enters a crossing while a pedestrian is on or entering it.",
  },
  illegal_turn: {
    name: "Illegal turn",
    level: "warning",
    color: "amber",
    description: "A turn from the wrong lane or in a prohibited direction.",
  },
  solid_line_crossing: {
    name: "Solid-line crossing",
    level: "warning",
    color: "amber",
    description: "A vehicle manoeuvres across a solid road marking.",
  },
  stop_line: {
    name: "Stop-line violation",
    level: "notice",
    color: "green",
    description:
      "A vehicle stops beyond the stop line on red without entering the intersection.",
  },
  congestion: {
    name: "Congestion",
    level: "notice",
    color: "green",
    description:
      "Traffic is stationary or crawling across all lanes of one direction.",
  },
  road_obstacle: {
    name: "Road obstacle",
    level: "warning",
    color: "amber",
    description:
      "Debris, an animal, or a fallen object occupies the carriageway.",
  },
  fire_smoke: {
    name: "Fire or smoke",
    level: "critical",
    color: "red",
    description: "Visible fire or smoke from a vehicle or the road.",
  },
};
