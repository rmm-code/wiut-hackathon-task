# Event implementation and evidence

All 14 official output labels have implementation paths. This table distinguishes implemented logic from evidence that makes it usable on this camera. Controlled tests are software verification, not traffic-accuracy measurements.

| Label | Implementation | Current camera limitation |
| --- | --- | --- |
| accident | Local appearance specialist, repeated-frame confirmation, participant stopping/end suppression | Contact itself is not established by a box; onset/end precision needs full-video review |
| near_miss | Approaching trajectories + braking/heading change + no observed overlap + separation | Image geometry cannot conclusively establish physical clearance |
| red_light | Governing lamp state, finite stop-line crossing, intersection traversal | Only the visible northwest-bound signal/approach is mapped; front position is approximate |
| wrong_way | Sustained motion opposing a mapped lane, held until lane exit | Direction evidence and lane geometry cover the visible approaches only |
| illegal_u_turn | Heading reversal inside a verified prohibited zone | **Inactive: no authoritative no-U-turn zone established** |
| stopped_vehicle | Ten seconds stationary outside mapped queues | Bus stops and occlusion/ID changes need review |
| jaywalking | Pedestrian ground point outside crossings/islands; rider exclusion | Footpoint and crossing-boundary errors remain possible |
| failure_to_yield | Pedestrian crossing occupancy + vehicle entry/clearance interval | Image-space front/rear footprints are approximate |
| illegal_turn | Entry region, heading change and prohibited exit completion | **Inactive: prohibited lane-to-exit movements not established** |
| solid_line_crossing | Straddling then clearing a finite verified line segment | One visible separator; ground footprint is a wheel-position proxy |
| stop_line | Stops past governing red line; holds until green | One signal mapping; occlusions and unknown light color need review |
| congestion | Slow queues in each separately mapped lane of a complete visible group | Visible segment only; no city-wide or hidden-lane inference |
| road_obstacle | Supported animal/obstacle classes on road | Current base weights cover selected animals; arbitrary debris is not solved |
| fire_smoke | Local fire/smoke specialist with temporal confirmation and road gating | Brief/distant smoke can be missed; no accuracy claim |

Before adding the final two real-camera configurations, obtain the governing sign/marking or organizer clarification, locate it in the supplied view, and map the prohibited manoeuvre. Do not infer a prohibition from infrequent turns. The controlled tests exercise both legal/disabled negatives and prohibited positives without pretending the artificial geometry is the real road.
