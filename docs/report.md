# Technical report

## What we built

Crossing turns a fixed CCTV view of a Tashkent T-junction into timed traffic events and a causal
accident-risk curve.

- **Pipeline.** Pretrained YOLO11s finds road users and ByteTrack tracks them. A SIFT homography aligns
  each video to the reference view. Hand-written rules then read the tracks against scene geometry
  mapped once for this camera. Two open-weights specialist detectors propose accident and fire/smoke
  candidates.
- **Part B.** A separate estimator sees frames one at a time and scores closest-approach conflicts
  between tracked road users.
- **Training.** None. Everything learned is pretrained appearance detection. The camera knowledge
  lives in `config/camera.json`, where every fact carries its evidence.
- **Website.** https://wiut.mardonjon.me runs the same engine for uploads and shows every sample
  video annotated, with timelines, risk curves, EDA maps and the accuracy table below.

## How we measured it

There are no official labels, so we labelled the four sample videos ourselves; the method is in
[devset/README.md](../devset/README.md).

1. Loose versions of the rules proposed candidates; for jaywalking, every pedestrian foot point on
   the carriageway outside a crossing.
2. AI reviewers checked each candidate on contact sheets rendered from the original 4K frames, under a
   rubric that quotes the official class definitions.
3. Signal, turn and lane-line cases were re-checked at high zoom with measured geometry: front overshoot
   past the stop line, the lane at the stop line, and the lane coordinate between the painted lines.

This gave 77 labelled segments in six classes, 248 rejected candidates and 28 left uncertain.

| Class | Labelled | Predicted | Precision | Recall | F1 @ tIoU 0.3 / 0.5 / 0.7 |
| --- | ---: | ---: | ---: | ---: | --- |
| stop_line | 10 | 10 | 1.00 | 1.00 | 1.00 / 1.00 / 1.00 |
| red_light | 3 | 3 | 1.00 | 1.00 | 1.00 / 1.00 / 1.00 |
| illegal_turn | 4 | 4 | 1.00 | 1.00 | 1.00 / 1.00 / 1.00 |
| solid_line_crossing | 2 | 3 | 0.67 | 1.00 | 0.80 / 0.80 / 0.40 |
| failure_to_yield | 22 | 33 | 0.52 | 0.77 | 0.62 / 0.62 / 0.58 |
| jaywalking | 36 | 36 | 0.61 | 0.61 | 0.72 / 0.61 / 0.39 |

Precision and recall are at tIoU 0.5. **Score A on these labels is 0.808**; no other class is
labelled or predicted. The predictions this work replaced (353 events in 10 classes) scored **0.085**
on the same labels. Most of the gap comes from false events in classes the samples do not contain:
125 of them, in near_miss, congestion, wrong_way and stopped_vehicle.

The rules were tuned on the same four videos, so these numbers are optimistic. They are a development
measurement, not a test-set estimate.

## What worked

- **Mapping the camera from an empty-road background.** The first geometry was drawn on single frames
  and was wrong in ways that produced most false alarms: the stop line in the wrong place, lanes that
  did not follow the paint, zebra C drawn straight. A temporal median of 45 frames removes vehicles and
  exposes the paint. The stop line, the four solid lane lines and the crossings were placed on it and
  checked in all four videos.
- **Reading the one visible signal properly.** Crossings of the stop line cluster in green phases of
  the median signal head, which identifies it as the south-east approach's signal. A debounced lamp
  (amber keeps the last state) plus two tests removed every false red-light run that review found:
  the lamp must have been red for a second, and must still be red 1.5 s after the crossing. That
  excludes amber clearance and starts in the last second of red.
- **Reasoning from the traffic rules, not from rarity.** Clause 56 (turn from the extreme lane)
  identified five right turns from the wrong lane; the rule finds all of them. Clause 56 also shows
  that the eleven U-turns around the median nose, all from the median lane, are legal, so the U-turn
  rule flags only U-turns started from other lanes.
- **Negative evidence.** Review found no near miss, wrong-way drive, congestion episode, accident,
  fire or obstacle in the samples. Near-miss detection was switched off because every detection was a
  false alarm. The wrong-way rule was rewritten after 38 of 38 candidates proved to be U-turns through
  the junction mouth or tracker jitter. It now needs sustained travel against the direction inside one
  carriageway.

## What did not work

- **Stopped vehicles.** Every candidate was normal traffic: vehicles queued at the signal, waiting in
  the junction box to U-turn, parked at the far kerb or dwelling at a bus stop. Mapped zones and a
  "no stationary neighbour" test now suppress all of them. The rule can still find a lone vehicle
  stopped on green in a traffic lane, but it has no positive example to be measured against.
- **Pedestrians near crossings.** Foot points of people walking on or beside zebra paint, or hidden
  behind cars, flicker across the crossing edge. Margins, an occlusion check and a minimum duration
  help, but jaywalking remains the least precise active class.
- **Failure to yield.** Deciding whether a pedestrian is close enough to a vehicle's path from
  image boxes is fragile. Pedestrians waiting at a kerb, or on the other half of the split A/B
  crossing, still produce false events.
- **Accident specialist.** Its only confirmed detection in the samples was two cars overlapping in
  perspective. Requiring the participants to come to rest removed it, but the model's recall on a
  real crash here is unknown.
- **Part B cannot be measured on accident-free samples.** Its score was only calibrated for false-alarm
  rate, a monotonic change that leaves ranking and AP untouched.

## Runtime

Official harness, Part A and Part B together, on an Apple M5 with MPS:

| Video | Duration | Harness time | Share of the 3 × budget |
| --- | ---: | ---: | ---: |
| C3896 | 340.3 s | 315.7 s | 31% |
| C3897 | 317.8 s | 290.1 s | 30% |
| C3902 | 317.8 s | 293.3 s | 31% |
| C3905 | 127.6 s | 110.1 s | 29% |

The harness runs the detector twice, once for Part A and once in Part B, both at about 7.5 frames/s.
The judging GPU has not been measured. The public website analyses uploads on four CPU cores: a
20-second 1080p clip took 84 s.

## Next steps

- Have people check the model-assisted labels and label boundaries frame by frame.
- Label held-out footage.
- Collect positive examples of the unobserved classes (near miss, accident, obstacle, fire).
- Validate Part B on public crash datasets (DAD, CCD, DoTA) before relying on its alarms.
- Measure runtime on the judging GPU.
