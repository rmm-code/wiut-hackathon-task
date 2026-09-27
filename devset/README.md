# Development labels

- `labels.json`: our event labels for the four organizer sample videos, in the official
  `ground_truth.json` format. 78 segments in six classes.
- `notes.json`: one record per reviewed candidate, accepted, rejected or uncertain, with time, track
  identities, source and a short reason (127 accepted records, 248 rejected, 28 uncertain).
- `report.json`: the official Part A metric of `predictions_samples.json` against these labels, as shown
  on the website.
- `review/`: everything used to build the labels (rubric, candidates, verdicts, scripts).

```sh
python evaluate.py --pred predictions_samples.json --gt devset/labels.json --per-video
python -m scripts.devset cache      # detector and tracker output of every sample, once (~5 min on M5)
python -m scripts.devset score      # every rule re-run on that cache and scored (~10 s)
python devset/review/assemble.py    # rebuild labels.json and notes.json from the verdicts
```

## How the labels were made

These labels are **model-assisted reviews by AI assistants (Claude), not independent human
annotation**.

1. **Candidates.** Deliberately loose versions of the rules proposed candidates from the cached tracks.
   For example:
   - every pedestrian ground point on the carriageway outside a crossing;
   - every vehicle inside a crossing while any pedestrian track was on it;
   - every vehicle stationary for 8 s;
   - every stop-line crossing in any lamp state;
   - every close approach with braking;
   - every motion against a carriageway;
   - every lane change in the solid-line section.

   Overlapping candidates were grouped into 404 review episodes; 33 solid-line candidates were
   reviewed separately.
2. **Review.** Each candidate was checked on contact sheets rendered from the original 4K frames. The
   involved tracks are highlighted, scene zones overlaid, and for signal classes the lamp is enlarged in
   every tile. The rubric (`review/rubric.md`) quotes the official class definitions.
   - Reviewer agents covered all near-miss and wrong-way episodes, jaywalking in C3896, and part of
     C3897.
   - The remaining jaywalking and failure-to-yield review went through every detection of the final
     rules plus the extra detections of deliberately looser settings.
3. **Zoom and measurement.** Every signal, turn, lane-line and stopped-vehicle case was re-checked at
   high zoom, together with a measurement:
   - front overshoot past the stop line, in box heights;
   - the lane at the stop-line crossing;
   - a continuous lane coordinate between the painted lines;
   - the debounced lamp state.

   Small tiles had misled early verdicts: the first pass called several cars "at the line" that were a
   car length past it.

**Boundaries.**
- Jaywalking from the manual review uses the pedestrian's ground point with no margins: the segment
  runs from stepping onto the carriageway to leaving it. It does not use the tuned rule's boundaries.
- Failure-to-yield segments span the vehicle's traversal of the crossing.
- The rest were set from the zoomed frames.
- Same-class events that overlap in time are merged into one segment, as the organizers' annotations do.

## Conventions on this camera

| Label | Accepted when | Start → end |
| --- | --- | --- |
| jaywalking | Feet clearly on the asphalt outside a zebra: the slip-lane shortcut between zebras A and C, walking or standing beside zebra B, crossing the junction box. Excluded: zebra paint and its edge, islands, the median refuge, kerbs, cyclists and riders | Steps onto the carriageway → leaves it |
| failure_to_yield | Vehicle moves across a zebra while a pedestrian walks on the same zebra near its path. Excluded: pedestrians waiting at a kerb, pedestrians on the other half of the split A/B crossing | Vehicle front enters → rear leaves |
| red_light | Front crosses the stop line after the lamp has been red for about a second, and the vehicle continues through the junction while the lamp stays red. Amber clearance and starts in the last second of red are not labelled | Crossing → leaves the junction |
| stop_line | Front clearly past the stop line (typically half a car length or more) while stationary on red | First such stop in the phase → green onset |
| illegal_turn | Right turn into the side road from lanes 2–5 (clause 56: turns start from the extreme lane) | Stop-line crossing → turn completed |
| solid_line_crossing | Lane change across one of the four solid lane lines before the stop line | Wheel on the line → fully in the new lane |
| stopped_vehicle | None accepted. Every candidate was a signal queue, a vehicle waiting in the junction box to U-turn or turn, far-kerb parking or a bus stop, or a vehicle waiting at the north-east driveway | — |
| illegal_u_turn | None. 10 of 11 tracked U-turns start in the median lane and the eleventh on the line beside it; no sign or marking prohibits them | — |
| near_miss, wrong_way, congestion, accident, fire_smoke, road_obstacle | None occurred | — |

## Limits

- **Shared blind spots.** The reviewers were AI assistants, and they share blind spots with the
  detector that proposed the candidates. An event that no loose rule proposed can only enter through a
  reviewer's `extra` note.
- **Failure-to-yield recall.** It is measured against events found by the final rule or a looser one.
  The broad "any pedestrian on the crossing" episodes were only partly reviewed; in the part that was,
  2 of 34 verdicts were positive, and both were among the rule's detections.
- **Boundary circularity.** Failure-to-yield boundaries come from the same crossing geometry the rule
  uses, so its tIoU is optimistic.
- **Tuned on the same videos.** The scores are a development measurement, not an estimate of the
  hidden test score.
- **Classes without positives.** Six classes have none here, so their precision on real events is
  unmeasured.
