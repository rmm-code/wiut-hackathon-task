# Review rubric — traffic-event dev labels (fixed CCTV camera, Tashkent T-junction)

You are labeling candidate events on contact sheets. Each sheet is a grid of 6 or 9 frames cropped
from the original 4K video; the timestamp (seconds) is printed top-left of each tile. Tracked objects
have thin grey boxes; the candidate's tracks are drawn **thick green with a label like `pers#123` or
`car#45`**. Yellow outlines = painted zebra crossings (A, B, C); magenta = islands/raised median;
red line = the south-east (SE) stop line. See `zones.jpg` for the named zones.

Scene: a main road runs from the upper-left to the lower-right. SE-bound traffic (5 lanes) comes from
the upper-left, stops at the red stop line, crosses zebra A and continues to the lower-right; some turn
right into the side road at the bottom-left through the slip lane and across zebra C. NW-bound traffic
enters from the right edge, crosses zebra B and continues up-left above the raised median; some turn
left into the side road along the bottom of the frame, crossing zebra C. Zebras A and B are two halves of
one pedestrian crossing, split by the small island at the median nose.

Judge only what is visible. When a detail cannot be decided from the frames, answer `uncertain` rather
than guessing. Be strict: a verdict of `yes` means an annotator following the definitions below would
certainly label it.

## Definitions (official) and how to apply them here

**jaywalking** — "A pedestrian on the carriageway outside a crossing." YES when the person's feet are on
the asphalt clearly outside the painted zebra (more than about half a stripe width beyond the paint),
not on a kerb, island, raised median or sidewalk. This includes pedestrians cutting across the slip-lane
asphalt between zebra A and zebra C (tag `slip-lane`), walking between queued cars, crossing the main road
away from zebras, or walking in the junction box. NO for people on the zebra, at its painted edge, on
islands/median/sidewalks, waiting on a kerb, cyclists/scooter riders, or detector errors (poles, signs).
Start = first frame on the asphalt; end = back on kerb/island/sidewalk/zebra (or leaves the frame).

**failure_to_yield** — "A vehicle drives through a crossing while a pedestrian is on it or stepping onto
it." YES when a vehicle (the green car/bus/truck/motorcycle box) moves across a zebra while a
pedestrian is on the same zebra's carriageway section (zebra A, B or C) or stepping onto it, near enough
to the vehicle's path that the vehicle should have yielded (roughly within the same half of the
crossing). NO if the pedestrian is only waiting on the kerb/island, has already cleared the vehicle's
path well before it arrives, is on the other half of the split A/B crossing, or the vehicle is stationary.
Start = vehicle front enters the zebra; end = vehicle rear leaves the zebra.

**stopped_vehicle** — "A vehicle stationary on the carriageway for 10 s or more, not in a queue at a
signal." YES for a vehicle stopped in a traffic lane or at the kerb within the carriageway for >= 10 s for
reasons other than traffic (drop-off/pick-up, parked, broken down, waiting). NO for vehicles queued behind
a red light or behind other stationary traffic, vehicles in marked parking bays off the carriageway, or
vehicles that keep creeping forward. Start = stops; end = moves again (or video end).

**near_miss** — "Sharp braking or swerving to avoid a collision; no contact." YES only when a road
user visibly brakes hard or swerves because of another road user that was on a collision course, and they
do not touch. Normal slowing in traffic, queue stop-and-go, and ordinary turning conflicts are NO.
Start = onset of the evasive action; end = users clear of each other.

**red_light** — "A vehicle crosses the stop line while its signal is red." The SE approach signal is the
median head (red box in zones.jpg); the sheet note gives the lamp state from our lamp reader. YES when a
vehicle's front crosses the SE stop line while the lamp is red and it continues into the junction. Amber
is NO. Start = front crosses the stop line; end = leaves the junction or the frame.

**stop_line** — "A vehicle stops past the stop line on red without entering the intersection." YES when
a vehicle stops with its front beyond the SE stop line (typically on zebra A) while the SE lamp is red.
Start = vehicle stops; end = lamp turns green.

**wrong_way** — "A vehicle moves against the traffic direction of its lane." YES only for a vehicle
clearly driving against the direction of its carriageway (e.g. moving up-left in the SE-bound lanes).
Reversing a few metres, tracking jitter or boxes jumping between vehicles are NO.

## Output

Write one JSON object per episode to the output file you are given, as a JSON list:

```json
{"eid": "jayw-C3896-0012", "verdicts": [
   {"id": 123, "verdict": "yes", "start": 12.4, "end": 18.0, "tag": "slip-lane", "why": "walks across slip-lane asphalt from zebra A to island"},
   {"id": 130, "verdict": "no", "why": "stays on zebra C stripes"}],
 "extra": [{"label": "jaywalking", "start": 14.0, "end": 16.5, "why": "untracked woman crossing between queued cars at right of crop"}]}
```

- One verdict per highlighted id (`yes` / `no` / `uncertain`). For `yes`, give start/end in seconds
  from the tile timestamps (interpolate between tiles; if unsure, use the member interval printed in the
  episode list).
- `extra` is for clear events of the same class involving objects that are not highlighted. Leave it empty
  otherwise.
- For failure_to_yield, the `id` is the vehicle; mention the pedestrian ids in `why`.
- Keep `why` short and factual. Do not describe people beyond position and action.
