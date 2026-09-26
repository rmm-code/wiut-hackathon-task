# Development labels

`labels.json` holds our own event labels for the four organizer sample videos, in the official
`ground_truth.json` format. `notes.json` records the evidence for every accepted label and every
rejected or uncertain candidate: time, track identities and a short reason. `report.json` is the
official Part A metric of the submitted `predictions_samples.json` against these labels, and the
website renders it.

```sh
python evaluate.py --pred predictions_samples.json --gt devset/labels.json --per-video
python -m scripts.devset cache            # detector + tracker output of every sample, once (~5 min on M5)
python -m scripts.devset score            # same metric on a fast rule replay (~10 s)
python -m scripts.devset score --pred predictions_samples.json --json devset/report.json
python -m scripts.sheets C3896.MP4 40 70 --ids 503 --out sheet.jpg   # review contact sheet
```

## How the labels were made

These labels are **model-assisted reviews, not independent human annotation**.

1. **Candidates.** Deliberately loose versions of the rules proposed candidates from the cached tracks.
   For example: every pedestrian ground point on the carriageway outside a crossing, every vehicle in
   a crossing while any pedestrian track was on it, every vehicle stationary for 8 s, every stop-line
   crossing whatever the lamp state, every close approach with braking, every motion against a
   carriageway, and every lane change in the solid-line section. Overlapping candidates were grouped
   into 437 review episodes.
2. **Review.** Each episode was rendered as a contact sheet from the original 4K frames with the
   involved tracks highlighted, zones overlaid and, for signal classes, the lamp enlarged in every
   tile. Reviewers (AI assistants, Claude, working under a written rubric that quotes the official
   class definitions) returned yes / no / uncertain with a reason and boundaries. Only `yes` enters
   `labels.json`.
3. **Zoom checks.** Small tiles misled early verdicts on stop-line and turn cases. The first pass
   called several cars "at the line" that were in fact a car length past it. Every signal, turn and
   U-turn candidate was therefore re-checked at high zoom, together with the geometry measurements
   used for the decision: front overshoot past the stop line in box heights, lane at the stop-line
   crossing, and debounced lamp state.

Same-class events that overlap in time are merged into one segment, as the organizers' annotations do.

## Conventions on this camera

Definitions follow the task statement. Where the view needed a decision, we used the following.

| Label | Accepted when | Start → end |
| --- | --- | --- |
| jaywalking | Feet clearly on the asphalt outside a zebra: the slip-lane shortcut between zebras A and C, walking or standing beside zebra B, crossing the junction box. Excluded: zebra paint and its edge, islands, the median refuge, kerbs | Steps onto the asphalt → back on a kerb, island or zebra |
| failure_to_yield | Vehicle moves across a zebra while a pedestrian walks on the same zebra near its path. Excluded: pedestrians waiting at a kerb, pedestrians on the other half of the split A/B crossing | Vehicle front enters → rear leaves |
| stopped_vehicle | Stationary 10 s or more on the carriageway for a non-traffic reason | Stops → moves again or video end |
| red_light | Front crosses the stop line after the lamp has been red for about a second and the vehicle continues through the junction while the lamp stays red. Amber clearance and starts in the last second of red are not labelled | Crossing → leaves the junction |
| stop_line | Front clearly past the stop line (typically half a car length or more) while stationary on red | First such stop in the phase → green |
| illegal_turn | Right turn into the side road from lanes 2–5 (clause 56: turns start from the extreme lane) | Stop-line crossing → turn completed |
| illegal_u_turn | None found: all 11 observed U-turns start from the median lane, and no sign or marking prohibits them | — |
| solid_line_crossing | Lane change across one of the four solid lane lines before the stop line | Wheel on the line → fully in the new lane |
| near_miss, wrong_way, congestion, accident, fire_smoke, road_obstacle | None occurred in the samples | — |

## Limits

- The reviewers were AI assistants. They share blind spots with the detector that proposed most
  candidates. An event no loose rule proposed can only enter through a reviewer's `extra` note.
- The rules were tuned on these same four videos, so the measured scores are optimistic. They are a
  development measurement, not an estimate of the hidden test score.
- Six classes have no positive examples here. Their precision on real events is unmeasured.
