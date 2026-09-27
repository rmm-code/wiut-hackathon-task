import type { Label } from "../types";

// One verified detection per class the submission produces on the samples: each matches
// a devset/labels.json segment at temporal IoU >= 0.9, except stop_line (0.97 for the phase).
export const examples: {
  label: Label;
  sample: string;
  start: number;
  end: number;
  text: string;
}[] = [
  {
    label: "red_light",
    sample: "C3896.MP4",
    start: 78.9,
    end: 82.3,
    text: "The median lamp (inset) has been red for 13 s. Car #952 crosses the stop line and drives through while the other lanes wait.",
  },
  {
    label: "stop_line",
    sample: "C3896.MP4",
    start: 63.1,
    end: 102.5,
    text: "Car #567 stops on zebra A, well past the red stop line, for the whole red phase. The event ends at the green onset.",
  },
  {
    label: "illegal_turn",
    sample: "C3896.MP4",
    start: 106.6,
    end: 111.0,
    text: "Car #922 turns right into the slip lane from lane 2, cutting across the kerb-lane queue. Clause 56 requires turning from the kerb lane.",
  },
  {
    label: "solid_line_crossing",
    sample: "C3896.MP4",
    start: 123.6,
    end: 126.8,
    text: "SUV #1595 changes lane after the gantry, across one of the four solid lane lines before the stop line.",
  },
  {
    label: "failure_to_yield",
    sample: "C3897.MP4",
    start: 157.0,
    end: 158.3,
    text: "Car #2454 drives across zebra B while pedestrian #2436 is walking on it.",
  },
  {
    label: "jaywalking",
    sample: "C3902.MP4",
    start: 219.4,
    end: 224.5,
    text: "Pedestrian #4203 crosses the side road diagonally, away from zebra C.",
  },
];
