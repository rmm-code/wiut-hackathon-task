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
| South-east approach signal = median vehicle head | Across the four samples, 471 of 479 south-east-bound stop-line crossings (98%) happen while it is green, and the queue discharges exactly when it turns green |
| No visible head governs the north-west approach | North-west-bound traffic crosses zebra B in both lamp states, so no red-light rule is applied there |
| Five lanes, four solid lane lines before the stop line | Painted-line detection plus five clean clusters of stop-line crossing positions |
| Lane arrows and turn signs | None visible on the approach (the gantry carries only a priority-road sign and signal heads) |
| Legal basis for lane choice | Uzbekistan traffic rules, clause 56: take the extreme position before turning right, turning left or making a U-turn. Clause 62: no U-turns on pedestrian crossings ([uzpdd.uz, chapter 9](https://uzpdd.uz/pddtext.php?id=9)) |

## Turn classes

**illegal_turn: active.** A right turn into the side road must start from the kerb lane (clause 56). In
the four samples, 20 of 25 right turns into the side road cross the stop line in the kerb lane. The other
five (C3896 at 33.2 s, 106.6 s and 274.4 s, C3897 at 175.4 s, C3902 at 280.5 s) cross it in lanes 2–3.
The rule flags a vehicle first seen moving in lanes 2–5 over the solid-line section that then travels
into the side road. The event runs from the stop-line crossing to the completed turn.

The rule finds four of the five. It misses C3896 #139, which creeps through a congested junction for
20 s. It also flags C3897 #2011: that car moved into the kerb lane across solid lines before the stop
line, so its turn is legal, but the rule only checks where a vehicle was, not its lane at the line.
That detection merged with #2175's event into one segment.

**illegal_u_turn: active, narrow.** U-turns around the median nose are frequent: 11 were tracked end to end
in the samples: 10 start in the median lane and one on the line between lanes 4 and 5. No sign or marking prohibits them. The reversal happens in the
junction rather than on a zebra, so they are treated as legal. Clause 56 is broken by any U-turn not started from the median lane. The rule flags lanes 1–3
only, because vehicles on the line between lanes 4 and 5 are ambiguous. None occurred in the samples, so the rule is untested
here. An earlier draft treated every nose U-turn as a clause 62 violation. That was rejected
because it would label a routine, permitted movement.

If the organisers treat nose U-turns as illegal, add a rule with `from` = the median lane. The observed
examples are listed in the development notes.

## Other classes

| Label | Rule | State |
| --- | --- | --- |
| red_light | Front crosses the stop line after the lamp has been red for 1 s, enters the junction, and the lamp is still red 1.5 s later. This excludes amber clearance and starts on red+amber | Active; 3 of 3 sample events found, no false alarms |
| stop_line | Stationary with the front at least 0.35 box heights past the stop line during red; ends at the green onset. Several cars in one red phase form one segment | Active; 10 of 10 red phases found |
| illegal_turn | Clause 56 right turn from lanes 2–5 (above) | Active; 4 of 5 found, no false alarms |
| solid_line_crossing | The footprint straddles and then clears one of the four solid lane lines. Crossings less than 3 s apart form one event | Active; 2 of 2 found, 1 false alarm |
| failure_to_yield | Vehicle moving across a crossing within one vehicle height of a pedestrian walking on it, away from the crossing's kerb ends (12% of its length) | Active; tuned on the labels |
| jaywalking | Pedestrian foot point on the carriageway at least 0.06 pedestrian heights inside the kerb and 0.12 away from any crossing or island, for at least 3 s. Riders and pedestrians whose feet are hidden behind a vehicle are excluded | Active; tuned on the labels |
| stopped_vehicle | Stationary 10 s on the carriageway with no stationary vehicle next to it. Excluded: the signal queue (unless the vehicle stopped on green), past the stop line, the junction box where vehicles wait to turn, the far-kerb parking and bus-stop strip, the north-east driveway corner, and boxes cut by the frame edge | Active; every sample candidate was normal traffic, so there are no detections and no measured positives |
| wrong_way | Travels at least 1.5 box heights against the carriageway within 2 s while staying inside one carriageway. The junction mouth is excluded, because U-turners pass through it | Active; none in the samples |
| congestion | Four or more vehicles, 85% stationary, for 15 s, while the governing lamp is green (or on the unsignalled carriageway) | Active; none in the samples |
| near_miss | Collision course, hard braking or swerving, no box overlap, then separation | **Off**: the reviewed samples contained no near miss, and every detection was a false alarm |
| accident | Specialist detector confirmed across frames; the participants must come to rest | Active; the only sample candidate was two cars overlapping in perspective, now suppressed |
| road_obstacle | Supported animal classes on the carriageway | Active; arbitrary debris is not covered |
| fire_smoke | Specialist detector with temporal confirmation and road gating | Active; none in the samples |

Every predicted class enters the macro average. A class that fires on normal traffic but never
occurs in the test set costs a full class's worth of score, which is why near_miss stays off and why
the rules are tuned toward precision.
