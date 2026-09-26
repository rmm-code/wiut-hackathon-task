# Development labels

`labels.json` holds our own event labels for the four organizer sample videos, in the
official `ground_truth.json` format, so that

```sh
python evaluate.py --pred predictions_samples.json --gt devset/labels.json --per-video
python -m scripts.devset score          # same metric on a fast rule replay
```

measure the submitted pipeline. `notes.json` records the evidence for every label
(time-stamped observation, involved track identities, uncertainty).

## How the labels were made

Labels are **model-assisted reviews, not independent human annotation**:

1. Candidate intervals came from two sources: the rules at deliberately loose settings
   (for example every pedestrian ground point on the carriageway, every vehicle
   stationary for eight seconds, every stop-line crossing in either lamp state), and a
   full-frame scan of each video at fixed intervals for visually obvious events.
2. Every candidate was reviewed on contact sheets rendered from the original 4K frames
   (`python -m scripts.sheets`), with the involved tracks highlighted, scene zones
   overlaid and the governing lamp visible.
3. Accepted events were given boundaries from the reviewed frames by the class conventions
   below. Anything that could not be decided from the frames is listed in `notes.json` as
   `uncertain` and left out of `labels.json`.

The reviewer was an AI assistant (Claude) working from extracted frames, directed by the
team. Treat these labels as a development set, not ground truth: they share blind spots
with the detector that proposed most candidates, and a human pass would improve them.

## Class conventions used on this camera

Definitions follow the task statement; the notes below make them concrete for this view.

| Label | Accepted when | Start → end |
| --- | --- | --- |
| jaywalking | A pedestrian's feet are on the carriageway outside the painted crossings (between queued cars, beside a crossing, across the side road). Standing on islands, kerbs or the crossing itself is excluded. | First frame on the carriageway → back on a kerb, island or crossing |
| failure_to_yield | A vehicle drives across a crossing while a pedestrian is on that crossing's carriageway section, or stepping onto it, near the vehicle's path | Vehicle front enters the crossing → vehicle rear leaves it |
| stopped_vehicle | A vehicle is stationary 10 s or longer on the carriageway and is not queueing at the signal (drop-offs, breakdowns, waiting on the carriageway) | Vehicle stops → vehicle moves again (video end if never) |
| red_light | A vehicle's front crosses a stop line while its governing signal is red and it continues into the intersection | Front crosses the stop line → leaves the intersection or frame |
| stop_line | A vehicle stops beyond the stop line during red without entering the intersection | Vehicle stops → governing signal turns green |
| wrong_way | A vehicle travels against its lane's direction | Enters the opposing lane → returns or leaves the frame |
| congestion | Every lane of a direction at a standstill or crawling beyond a normal signal queue (the queue does not clear on green) | Queue stops → queue clears |
| near_miss | Visible sharp braking or swerving between two road users to avoid contact | Evasive action begins → users clear of each other |
| solid_line_crossing | A vehicle changes lane across a solid marking | Wheel crosses the line → vehicle fully in the new lane |
| illegal_turn / illegal_u_turn | See `docs/classes.md` for the camera facts used | Vehicle starts turning → turn completed |
| accident, road_obstacle, fire_smoke | Only when clearly visible | Class definitions |

A normal red-phase queue at the stop line is neither `congestion` nor `stopped_vehicle`.
Two simultaneous same-class events are one segment, as in the organizer annotations.
