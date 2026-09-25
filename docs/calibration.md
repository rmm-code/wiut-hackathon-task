# Camera calibration and coverage

The baseline uses the organizer-provided intersection reference, not a generic road layout. `config/camera.json` stores normalized carriageway, crossing, island, lane, and queue geometry.

The geometry was drawn from the actual reference and checked against the downloaded C3905 footage. It remains **provisional**. A first broad road polygon incorrectly included sidewalk/island areas; the current map follows the curb and includes all three foreground pedestrian islands plus the central island. Pedestrians close to crossing/island boundaries are treated conservatively using a size-aware margin.

The original sample is 3840 × 2160 at approximately 29.97 fps, not the brief's typical 25 fps. Camera matching downsamples with area filtering, normalizes contrast, matches SIFT features, estimates a RANSAC homography, and checks inlier count, inlier fraction, spatial coverage, and plausible projected area. Linear downsampling of the original 4K frame created aliasing that rejected the same scene while accepting its 720p copy; area filtering corrected that cause. A camera mismatch disables scene-dependent events and risk instead of applying this map to arbitrary roads.

Current default rule coverage:

| Class | State | Limitation |
| --- | --- | --- |
| Pedestrian on road | Active, provisional | Footpoint and crossing/island geometry can be imperfect; riders can be confused with walking pedestrians |
| Stopped vehicle | Active, provisional | Ten-second check and queue exclusion implemented; queue/bus-stop conventions need label review |
| Failure to yield | Active, provisional | Shared crossing occupancy; occlusions and approximate vehicle footprint can create false positives |
| Road obstacle | Partial, provisional | Only supported animal classes; no arbitrary-debris model |
| Wrong way, congestion | Disabled | Lane directions/complete lane groups have not been confirmed |
| Red light, stop line | Disabled | Governing signal regions and stop-line mappings are not confirmed |
| Illegal turn/U-turn, solid-line crossing | Disabled | Prohibitions and solid markings have not been verified |
| Accident | Active specialist, provisional | Appearance and temporal confirmation; contact onset accuracy is unvalidated |
| Near miss | Disabled | Evasive-action detection is not validated |
| Fire/smoke | Active specialist, provisional | Two-frame confirmation and road gating; tiny or brief incidents may be missed |

Do not set verification flags to true merely to increase class count. Signal/turn modules are experimental scaffolding until their configuration, boundaries, and behavior are validated. They are not advertised as working competition coverage. Image-plane trajectory geometry does not establish physical speed or calibrated collision probability.

The risk estimator produces a causal closest-approach conflict score with decay, on matching camera views. It uses no future frames and has independent tracking state. This is not a calibrated probability, and its anticipation quality cannot be claimed without accident labels.

Next validation work: annotate all supplied clips using the official event conventions, audit false positives, verify camera facts with organizers, evaluate held-out intervals, and add suitable open-weights accident/near-miss and smoke/fire recognition. No F1, precision, recall, or anticipation accuracy has been measured yet.

C3902 initially failed the single-scale matcher: 21 inliers represented 39.6% of descriptor matches, just below the existing 40% gate. Matching against the reference at its native 640 × 360 resolution produced 19 inliers with 42.2% agreement and broad spatial coverage. The matcher now retries that resolution after a failed 960 × 540 pass, retaining all existing inlier, area and coverage checks. Homographies are converted back to the common coordinate system. A regression fixture verifies recognition and that later unrelated frames clear the previous alignment. C3897 and C3905 still pass the original first matching pass.

## Expanded camera evidence (25 September)

The current revision maps three lanes separately in each visible carriageway, using the raised median, lane divisions and repeated observed motion in C3896 as direction evidence. Congestion requires occupancy of every mapped lane and an explicit complete-visibility flag. Wrong-way intervals persist while a vehicle stops in the opposing lane.

The visible median vehicle head faces the northwest-bound approach. Its region is `[0.601, 0.325, 0.615, 0.390]` in reference coordinates. Inspected C3896 frames show red at 0/10/20 s, green at 30/40/50/60 s, and red at 70/80/90 s. HSV brightness 120 missed the dim lamp; measured region thresholds are saturation 100 / value 50. This does not map the opposite hidden signal head or establish every lane's turning-phase permissions. One visible continuous white lane separator approaching the near stop line is mapped as a finite segment, not an infinite line.

Near-miss candidates require an approaching conflict, a measured braking/heading change, no observed box-overlap evidence and subsequent separation. Bounding boxes cannot establish absence of physical contact conclusively, so accuracy remains provisional.

Two prerequisites remain unresolved: an authoritative no-U-turn zone and prohibited lane-to-exit movements. The supplied signs/footage inspected here do not establish those prohibitions. `TurnRules` supports both with positive/negative controlled tests, but their real-camera configurations remain empty. To activate them honestly, supply the relevant sign/marking or organizer rule, its visible region, and prohibited entry/exit mapping. No legal rule is inferred from a rare manoeuvre or low traffic frequency alone.
