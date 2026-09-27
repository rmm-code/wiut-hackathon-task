# Camera calibration

All scene geometry lives in `config/camera.json`, in the coordinates of the organizer reference image
(`web/public/images/camera.webp`, 960 × 540 normalised to 0–1). Each video is aligned to that reference
once, on its first frame, so the same geometry applies to every clip from this camera.

## Alignment

The sample videos are 3840 × 2160 at 29.97 fps (the brief says typically 25 fps). Alignment downsamples
with area filtering, normalises contrast (CLAHE), matches SIFT features and estimates a RANSAC
homography. The match is accepted only with enough inliers, a high inlier fraction, broad spatial
coverage and a plausible projected area. If it fails at 960 × 540, it retries at the reference's
native 640 × 360 without relaxing those checks. That retry fixed C3902, whose first attempt fell just
below the inlier-fraction gate.

When alignment fails, the video is treated as a different camera. Detection and tracking still run,
but every scene rule and the risk score are switched off rather than applying this junction's
geometry to another road. `tests/test_scene.py` covers acceptance, rejection and the C3902 fallback.

## How the geometry was drawn

The first version was drawn on single frames and contained real errors:

- a stop line placed in the wrong spot;
- lane polygons that did not follow the lanes;
- zebra C drawn as a straight band although the paint bends;
- the raised median missing as an island.

The current geometry was placed on a **temporal-median background** of C3896: the per-pixel median of
45 frames spread over the clip. Moving and queued vehicles vanish from it, leaving the empty road and its
paint. Every region was then projected back into all four videos through their alignments and checked
by eye (`python -m scripts.sheets` draws the overlays).

| Element | How it was placed |
| --- | --- |
| Carriageway and islands | Kerbs, the three pedestrian islands, the median-nose refuge and the raised median traced on the median background |
| Crossings A, B, C | Painted zebra outlines; C follows the bend of the side-road crossing |
| South-east stop line | Painted line on the 4K median background, confirmed by where stop-line crossings cluster |
| Four solid lane lines | Painted-line detection (Hough) on the 4K median background of the approach; they land on the paint in all four videos |
| Lanes and carriageways | South-east approach (five lanes), north-west departure above the median, north-west approach from the right edge |
| Signal lamp | The median vehicle head; its region was checked on crops from all four videos |

## Signal

Only one vehicle signal head is visible, on the median. It governs the south-east approach: across the four
samples, 471 of 479 south-east-bound stop-line crossings (98%) happen while it is green, and the queue discharges
when it turns green. North-west-bound traffic crosses zebra B in both lamp states, so no visible head
governs that approach and no signal rule is applied to it.

The lamp reader classifies saturated red and green pixels in the lamp region (saturation above 100,
value above 50; the lamp is dim at dusk). A state change is accepted after three readings, or one
reading left uncontradicted for a second. Amber and unreadable frames keep the previous state.
`tests/fixtures/signal-*.png` are real lamp crops used as regression tests.

## Scene facts used by the rules

- Lane directions come from the carriageway layout and tracked motion.
- Turn restrictions come from Uzbekistan's traffic rules, clauses 56 and 62. See [classes](classes.md).
- The four solid lane lines are the painted continuous section between the gantry and the stop line.
  Upstream of the gantry the lines are dashed.
- `queue_zones` list where stationary vehicles are normal, so they are not reported as stopped vehicles.
  Each zone records its evidence from the reviewed samples:
  - the signal queue on the approach, which counts only while the lamp is red;
  - past the stop line;
  - the junction box, where vehicles wait to turn or U-turn;
  - the far-kerb parking strip and bus stop;
  - the north-east driveway corner.

Image-plane geometry is not metric. Speeds and gaps are measured in multiples of the object's box
height, so the rules scale with distance from the camera but make no physical-speed claims.
