# Event classes on this camera

All 14 official labels have an implementation path. This page records the camera facts each rule relies
on, how they were established, and whether the class is switched on. Measured accuracy on our sample
labels is in [the technical report](report.md) and on the website's Report page.

## Scene facts (config/camera.json)

The camera watches a T-junction. The main road runs from the upper left, where five south-east-bound lanes
approach a stop line, to the right side of the frame. A raised median separates the north-west-bound
carriageway. A side road leaves at the bottom left through a channelised slip lane. Zebras A and B cross
the main road on either side of the median nose; zebra C crosses the side road.

Every region was placed on a temporal-median "empty road" background of C3896, so parked and queued
vehicles do not hide the paint. It was then checked on the other three samples through the per-video
camera alignment. The four solid lane lines of the south-east approach were found with painted-line
detection on that background and land on the paint in all four videos.

| Fact | Evidence |
| --- | --- |
| South-east approach signal = median vehicle head | Across C3896 and C3897, 97% of south-east-bound stop-line crossings happen while it is green, and the queue discharges exactly when it turns green |
| No visible head governs the north-west approach | North-west-bound traffic crosses zebra B in both lamp states, so no red-light rule is applied there |
| Five lanes, four solid lane lines before the stop line | Painted-line detection plus five clean clusters of stop-line crossing positions |
| Lane arrows and turn signs | None visible on the approach (the gantry carries only a priority-road sign and signal heads) |
| Legal basis for lane choice | Uzbekistan traffic rules, clause 56: take the extreme position before turning right, turning left or making a U-turn. Clause 62: no U-turns on pedestrian crossings ([uzpdd.uz, chapter 9](https://uzpdd.uz/pddtext.php?id=9)) |

## Turn classes

**illegal_turn: active.** A right turn into the side road must start from the kerb lane (clause 56). In
the samples, 12 of 17 right turns do so. The other five (C3896 at 106.6 s and 274.4 s, C3897 at 172.3 s and
175.4 s, C3902 at 280.5 s) cut across the kerb lane from lanes 2–3. The rule flags a vehicle first seen
moving in lanes 2–5 over the solid-line section that then travels into the side road. The event runs
from the stop-line crossing to the completed turn.

**illegal_u_turn: active, narrow.** U-turns around the median nose are frequent: 11 were tracked end to end
in the samples, all from the median lane. No sign or marking prohibits them. The reversal happens in the
junction rather than on a zebra, so they are treated as legal. Only a U-turn started from lanes 1–3
violates clause 56, and none occurred in the samples, so the rule is correct-by-construction here but
unmeasured. An earlier draft treated every nose U-turn as a clause 62 violation. That was rejected
because it would label a routine, permitted movement.

If the organisers treat nose U-turns as illegal, add a rule with `from` = the median lane. The observed
examples are listed in the development notes.

## Other classes

| Label | Rule | State |
| --- | --- | --- |
| red_light | Front crosses the stop line after the lamp has been red for 1 s, enters the junction, and the lamp is still red 1.5 s later (excludes amber clearance and starts on red+amber) | Active |
| stop_line | Stationary with the front at least 0.35 box heights past the stop line during red; ends on green. Several cars in one red phase merge into one segment | Active |
| solid_line_crossing | Footprint straddles and then clears one of the four solid lane lines | Active |
| wrong_way | Travels at least 1.5 box heights against the carriageway within 2 s, staying inside one carriageway | Active; no occurrences in the samples |
| congestion | Four or more vehicles, 85% stationary, for 15 s, on green (or on the unsignalled carriageway) | Active; no occurrences in the samples |
| failure_to_yield | Vehicle moving across a crossing within one vehicle size of a pedestrian walking on the crossing's carriageway part | Active |
| jaywalking | Pedestrian ground point on the carriageway outside crossings and islands; riders and pedestrians hidden behind vehicles excluded | Active |
| stopped_vehicle | Stationary 10 s on the carriageway outside the signal queue | Active |
| near_miss | Collision course, hard brake or swerve, no overlap, then separation | **Off**: the reviewed samples contained no near miss and every detection was a false alarm |
| accident | Specialist detector, confirmed across frames, participants must come to rest | Active; the only sample candidate was two cars overlapping in perspective and is now suppressed |
| road_obstacle | Supported animal classes on the carriageway | Active; arbitrary debris is not covered |
| fire_smoke | Specialist detector with temporal confirmation and road gating | Active; no occurrences in the samples |

Classes that are active but never occur in the samples have unmeasured precision. Every predicted class
enters the macro average, so a class that fires on normal traffic costs more than it earns. That is why
near_miss stays off.
