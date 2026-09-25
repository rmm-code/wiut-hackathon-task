# Technical report

Crossing analyzes fixed-camera road videos with YOLO11s, ByteTrack, camera alignment, temporal event rules, two specialist incident detectors, and an independent causal risk estimator. The website supports uploads, queued processing, cancellation, annotated playback, event timelines, risk curves, JSON export, measured traffic maps, and independent event labeling. No model training or hosted AI inference is claimed.

## Verified evidence — 24 September 2026

| Check | Result |
| --- | --- |
| Original sample available | C3905: 3840 × 2160, 29.97003 fps, 3,825 frames, 127.6275 seconds |
| Updated official harness, Part A + Part B | 140.0 seconds on Apple M5 / MPS; allowance 382.9 seconds |
| Official output | 17 candidate events, 3,825 risk samples; validator reports zero errors/warnings |
| Web run with annotated/clean video and maps | 79.46 seconds; event and risk arrays exactly equal to the separate official harness run |
| Model storage | Three pinned checkpoints, 139.1 MB total |
| Engineering tests | 30 Python and 6 frontend tests pass |
| Linux offline check | All three models load and predict without networking; all 30 Python tests pass |
| Frontend | Strict TypeScript, production build and 700-line source guard pass |

The Mac measurement does not establish NVIDIA timing. Predictions now cover all four organizer samples. Candidate counts and runtime vary with code revisions; older 22-event reports and 195.6-second runs describe the earlier baseline.

## Changes motivated by observed problems

Area-filtered downsampling and feature alignment fixed a false camera mismatch on the dark 4K sample. Crossing rules now exclude likely cyclists classified as pedestrians and maintain a yielding interval until the vehicle clears the crossing. Signal logic separates stop-line crossing from intersection entry and retains stopped-line events until green. Turn and solid-line events use observed boundaries instead of arbitrary short intervals. Signal/turn modules remain inactive without verified scene facts.

Two appearance specialists provide accident and fire/smoke candidates, with repeated-frame confirmation and a road-region constraint. Accident suppression reduces repeated events from an already stopped wreck. Source example images establish only functional loading and inference; they are not held-out evaluation data. Details and licences are in `docs/research.md`.

Measured EDA includes visible counts over time, ground-point occupancy, image-space motion and object trajectories. These are tracker-derived observations. Identity switches inflate totals; image-space movement is not physical speed. Maps on an unmatched camera use the actual input frame rather than the configured intersection background.

Part B receives only the current frame and timestamp, owns independent tracking state, and never calls the incident specialists or Part A. Prefix/reset tests verify this contract with controlled detections. Its closest-approach score remains uncalibrated; causal execution alone does not prove anticipation quality.

## Limitations and incomplete submission requirements

Six categories are enabled on matching scenes: stopped vehicle, pedestrian on road, failure to yield, limited animal obstacles, accident, and fire/smoke. Near-miss detection and legal signal/direction/turn/line rules remain disabled where evidence is insufficient. The specialist detectors sample around 1 Hz, so brief incidents and precise onset times can be missed. Congestion needs confirmed lane groups; arbitrary debris remains unsupported.

There is no completed independent ground truth, so no precision, recall, temporal F1, or anticipation accuracy is reported. The review panel helps produce labels but does not establish their correctness. Model event-table review flags are not ground truth.

All four organizer samples are now available and fully processed. A public working host, populated public repository/tag, public artifact links, and three real team profiles are still missing. NVIDIA runtime has not been measured. See `docs/submission.md` for the release checklist. This remains a tested local candidate, not a completed competition submission.


## Additional samples — 24 September 2026

| Sample | Decoded frames | Candidate events | Tracked identities | Web pipeline runtime |
| --- | --- | --- | --- | --- |
| C3897 | 9,525 / 9,525 | 44 | 1,087 | 183.29 s |
| C3902 | 9,525 / 9,525 | 34 | 1,192 | 210.98 s |

Both clips are 317.8175 seconds at 3840 × 2160 / 29.97003 fps. Each has 9,525 risk points, complete annotated and clean H.264 exports, and occupancy/motion/trajectory maps. The combined three-sample predictions pass the unchanged evaluator's format validation with 95 candidate events and no errors/warnings. These timings describe the web pipeline, not an independent Part A + Part B harness benchmark on those two clips.

The first C3902 run decoded successfully but failed camera recognition, disabling event rules. That zero-event output was superseded after a native-resolution matching fallback fixed alignment without relaxing the acceptance checks. The full corrected rerun matched the scene and produced 34 candidates. Independent labels and event-accuracy measurements remain outstanding.


## Final source sample — 25 September 2026

C3896 was found in Downloads, verified, moved into `samples/`, and fully processed on Apple M5 / MPS. All 10,200 frames decoded; the 340.34-second clip produced 56 candidate events, 10,200 risk points and 1,050 tracked identities in 225.51 seconds. Camera matching passed with 703 inliers. Both annotated and clean H.264 exports contain 10,200 frames and the full source duration. The combined four-video predictions contain 151 candidate events and pass official format validation with zero errors or warnings. These are unreviewed model candidates; completing all samples does not establish accuracy or satisfy the remaining public-release requirements.
