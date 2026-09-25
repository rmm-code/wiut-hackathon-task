# WIUT traffic-event system: research and build plan

Research date: 24 September 2026. Status: requirements and approach reviewed; implementation and model benchmarking have not started.

**Recommendation:** use a pretrained YOLO road-user detector, ByteTrack, a calibrated map of the intersection, and separate event and anticipation logic. Deliver one simple dashboard backed by the same Python inference engine used in the submission. Start by annotating the supplied footage and measuring a baseline; add heavier models only when the measured errors justify them.

## 1. What was actually checked

- Read the entire 11-page task PDF and the pasted brief, including their differences.
- Extracted and read the starter interface, harness, evaluator, requirements, and example files. The extracted Python files match the ZIP byte for byte; checksums are in `starter-sha256.json`.
- Ran the official evaluator on the organizers' example predictions and labels: valid format, Score A 0.9074, Score B 0.7600, model score 0.8632. These are **example-fixture scores, not our model results**.
- Checked the supplied GitHub repository through authenticated GitHub access: it is private and empty. The local workspace was also empty before this research.
- Opened all four organizer-supplied Drive videos in the signed-in browser, inspected their previews and player durations, and checked short portions of playback. This is preliminary scene inspection, **not a complete event annotation or quantitative EDA**.
- Read the existing pothole model manifest, model documentation, detector, tracker, video-processing code, and rendering/reporting interfaces.
- Consulted primary model documentation, tracking research, dataset project pages, and OpenCV documentation. Links accompany the relevant decisions below.

The attachments specify the competition deliverables. The user's immediate request is to understand and recommend the work first. This document is the proposed build plan; no website has been published, repository visibility changed, or submission made.

## 2. The actual task and scoring

Part A is temporal event detection: `detect_events(video_path)` must return `[[start_sec, end_sec, label], ...]`. Detecting cars or drawing bounding boxes alone does not satisfy it. Part A may inspect the whole video, revisit frames, and refine boundaries.

Part B is accident anticipation: `RiskEstimator.reset(meta)` starts a fresh state and `step(frame, t_sec)` returns a score in [0, 1] for an accident starting within five seconds. Every score must depend only on the frames already received. The function receives BGR frames and must not open the video or reuse future-aware Part A results.

Required outputs are a runnable repository with weights, a public website with a working upload demo, and a short technical report. The PDF explicitly calls for a **public Git repository** at submission. Keep the current private repository private during research; arrange deliberate publication of the finished submission later.

| Component | Overall contribution when accidents occur in the test set | Practical implication |
| --- | ---: | --- |
| Event detection | 42% | Highest priority; class accuracy and precise temporal boundaries matter |
| Accident anticipation | 18% | Called a bonus, but skipping it gives up a substantial scoring component |
| Website | 25% | A working demo and real visualizations are essential |
| Code quality | 15% | Clean-machine execution and reproducibility directly earn points |

The evaluator has an explicit exception: when the ground truth contains no accidents, model score equals Score A, so event detection contributes the full 60% model allocation.

Part A averages per-class F1 at temporal IoU thresholds 0.3, 0.5, and 0.7. Rare and frequent evaluated classes have equal weight. A class absent from the truth but present in predictions adds a zero-scoring class. Omitting a class does not escape its penalty if it occurs in the hidden truth. We should pursue broad coverage with evidence, rather than fabricate rare-class predictions or deliberately limit the system to easy classes.

Temporal IoU measures overlap in **time**, not overlap between vehicle boxes. Example: the true accident lasts from 12 to 17 seconds. Predicting 11 to 18 gives 5/7 = 0.714; predicting 10 to 19 gives 5/9 = 0.556 and fails the strict 0.7 match.

Part B combines chance-normalized average precision, alarm F1, and mean warning lead time. Risk positivity uses a five-second horizon, while alarm matching allows starts within ten seconds before impact. These are distinct windows. Risk 0.5 starts an alarm; runs separated by less than two seconds merge. Evaluate false alarms during ordinary crossings and queues, not only successful warnings.

Runtime and packaging constraints:

- Both passes together must finish within three times video duration on the organizer machine: one T4-class NVIDIA GPU with 16 GB VRAM, eight CPU cores, 32 GB RAM, subject to organizer updates.
- Total shipped model weights: at most 5 GB. No inference-time internet or hosted model calls.
- Python 3.10 or newer; pinned, tested dependencies and local model paths.
- Preserve `run_submission.py` and `evaluate.py` unchanged. Keep `solution.py` as a small adapter to modular code.
- Every input filename must appear in predictions, even with no events. Times must stay inside video duration.
- Same-class overlapping events must be combined into their temporal union before the harness runs. Different labels may overlap. Blindly allowing the harness to drop duplicates loses coverage.
- Fixed seeds, stable ordering, reset tracking state between videos, and repeated-run verification are required.

## 3. Supplied footage and missing scene information

Player-displayed durations, rounded to whole seconds:

| Organizer link | Filename | Displayed duration | Preliminary visible condition |
| --- | --- | --- | --- |
| [Sample 1](https://drive.google.com/file/d/1kR9jODA2Wotw4gwkvpRKdqFADNJNc1nS/view) | C3896.MP4 | 5:40 | Bright daylight and strong shadows |
| [Sample 2](https://drive.google.com/file/d/1hp8DYeqtYHSwfM6qAo9FPSRHlpMFrIN_/view) | C3897.MP4 | 5:18 | Daylight, queued vehicles, pedestrians near the central island |
| [Sample 3](https://drive.google.com/file/d/10cHEReCWzO3u-Vk1CnNgHAx6egGy5MwJ/view) | C3902.MP4 | 5:18 | More shaded roadway, large bus visible |
| [Sample 4](https://drive.google.com/file/d/1aJ-QsAZVYJtLKHiRvKKeBq1D3GWNobRd/view) | C3905.MP4 | 2:08 | Darker conditions and smaller road users visible |

Together these are approximately **18 minutes 24 seconds**. Source resolution, exact frame rate, frame count, compression, camera stability, and event counts still need measurement from the original files. Browser playback versions are not reliable substitutes for original-file metadata.

All previews show the same intersection, including multiple marked crossings, pedestrian islands, traffic lights, traffic lanes, and sidewalk activity. We must map each crossing separately; a pedestrian standing on an island is different from a pedestrian on the carriageway. Signal heads are visible, but which head governs which lane and whether every required signal is readable remain to be verified.

The pasted brief says `samples/camera.md` is supplied; the PDF's supplied-data list does not include it, and it is absent from the ZIP. Obtain the organizer's road-layout description if available. Otherwise document visible geometry ourselves and ask for clarification about legal lane directions and prohibited manoeuvres. The system must not infer that every U-turn is illegal.

Confirm the original clips use one stable image coordinate system. If small framing differences exist, estimate alignment from static landmarks. Normalizing coordinates alone handles resizing but does not correct camera rotation, translation, or cropping. No additional footage from this camera may be collected.

## 4. What can be reused from the pothole project

The actual local model is a roughly 50 MB YOLOv8m checkpoint. The local manifest lists seven classes: Heavy-Vehicle, Light-Vehicle, Pedestrian, Crack, Crack-Severe, Pothole, and Speed-Bump. The existing detector deliberately keeps only the pothole class. Thus the model is worth benchmarking for traffic detection, but the current application logic cannot be reused unchanged. The upstream project documents the same seven-class road-anomaly approach. [Upstream project](https://github.com/collabdoor/road-anomaly-detection).

| Existing piece | Decision |
| --- | --- |
| Local YOLO checkpoint | Include as an initial comparison; enable its road-user classes in a separate adapter |
| Detector loading and model manifest patterns | Reuse the ideas and suitable utilities with attribution |
| Frame sampling, video rendering, evidence crop utilities | Adapt where they remain general-purpose |
| Existing tracker | Replace for this task: it models potholes approached by a moving dashcam, rather than independently moving road users |
| Pothole severity, GPS deduplication, trigger band | Exclude; these solve a different problem |
| Synthetic fallback | Exclude from actual inference; missing weights must produce a clear error |
| Existing complete web/backend architecture | Reuse only individual useful components; importing the entire product creates unnecessary complexity |

Useful local evidence: [model notes](/Users/mardonjon/Desktop/pothole/docs/ai.md), [detector](/Users/mardonjon/Desktop/pothole/ai/inference/detector.py), [tracker](/Users/mardonjon/Desktop/pothole/ai/inference/tracking.py), and [model manifest](/Users/mardonjon/Desktop/pothole/apps/web/public/models/model.json). These source files remain unchanged.

Potholes are not one of the 14 official classes, and should not automatically be relabeled as `road_obstacle`.

## 5. Proposed model and processing pipeline

**Video frames → YOLO road-user detections → ByteTrack identities and trajectories → mapped lanes/crossings/signals → event state machines → refined time segments.**

Use pretrained weights first. Compare the existing YOLOv8m road model with a small general YOLO model, starting with YOLO11s and optionally YOLO26s if the available implementation and device support are straightforward. Official documentation provides these model variants; published benchmark numbers do not establish performance on this intersection. Make the choice using small-pedestrian recall, vehicle recall, tracking stability, runtime, and final event F1. [YOLO11](https://docs.ultralytics.com/models/yolo11), [YOLO26](https://docs.ultralytics.com/models/yolo26).

ByteTrack is a suitable initial tracker because it associates detections over time, including lower-confidence candidates that can help retain partially obscured road users. Ultralytics provides both ByteTrack and BoT-SORT integrations. Start with ByteTrack; compare BoT-SORT only if identity switches remain a measured problem. Tune track lifetime in elapsed seconds and keep the tracker time base consistent with sampled frames. [ByteTrack paper](https://arxiv.org/abs/2110.06864), [tracking documentation](https://docs.ultralytics.com/modes/track).

Manually map roadway regions, crossings, islands, stop lines, solid markings, legal lane directions, permitted turn connections, and relevant signal crops. This is justified by the competition's single-camera setting. Track ground-contact estimates for road position, while retaining vehicle fronts/footprints for stop-line and crossing decisions. A generic box centre cannot accurately implement every boundary rule.

Where adequate reference geometry is available, rectify the road plane to reduce perspective distortion. This assumes an approximately planar road. Without trustworthy calibration, use conservative local motion/conflict measures and do not claim accurate metres, km/h, or physical TTC. [OpenCV homography documentation](https://docs.opencv.org/4.0.0/d9/dab/tutorial_homography.html).

Each event module should maintain candidate, confirmed, active, and ended states with class-specific timing. Track uncertainty and brief occlusion explicitly. A lost detection should not immediately end an event, but a tracker prediction must not extend it indefinitely.

Part A can use an economical initial pass and revisit short candidate windows at a higher frame rate to refine onset/end. Proposed comparison rates are 5, 8–10, and 12.5 analyzed frames/second when compatible with the actual source rate; these are experiments, not established settings. Use higher-resolution road-user or signal crops only when their measured benefit justifies the cost.

## 6. All 14 event classes: evidence and boundary rules

| Official label | Proposed evidence | Required start → end | Main error to prevent |
| --- | --- | --- | --- |
| `accident` | Visible contact plus consistent trajectory/appearance changes; optional temporal verifier | First visible contact → all involved users stop moving or leave frame | Overlapping boxes or ordinary stopping treated as a crash |
| `near_miss` | Close conflict plus sharp evasive braking/swerving and no contact | Evasive action begins → users clear each other | Every close pass treated as a near miss |
| `red_light` | Correct governing signal is red when vehicle front crosses mapped stop line | Front crosses line → vehicle leaves intersection/frame | Reading a pedestrian signal or the wrong lane's signal |
| `wrong_way` | Sustained motion opposite the legal direction of the occupied lane | Enters opposing lane → returns to legal lane or exits | Legitimate turning motion or tracker jitter |
| `illegal_u_turn` | Trajectory reversal plus confirmed prohibition | Starts turning → completes turn | Assuming U-turn geometry establishes illegality |
| `stopped_vehicle` | At least 10 seconds stationary on carriageway, excluding signal queues | Original stop time → moves again or is removed | Starting the event only after the ten-second confirmation; red queues |
| `jaywalking` | Pedestrian on roadway outside mapped crossing | Steps onto road → leaves road | People on sidewalks, islands, or legitimate crossings |
| `failure_to_yield` | Vehicle crosses a pedestrian crossing while a pedestrian occupies/enters it | Vehicle enters crossing → leaves crossing | Combining separate crossing regions or inventing broader legal criteria |
| `illegal_turn` | Completed manoeuvre and lane/turn permission map | Starts turning → completes turn | Legal turn mistaken for prohibited turn |
| `solid_line_crossing` | Vehicle footprint/wheel evidence crosses mapped solid marking | Wheel crosses line → fully in new lane | Box-edge overlap with paint; crossing a broken marking |
| `stop_line` | Vehicle stops beyond stop line on red without entering intersection | Vehicle stops → governing signal turns green | Confusing it with red-light running; ending at vehicle movement instead of green |
| `congestion` | Direction-level occupancy and near-zero/crawling flow across all lanes | Queue stops moving → queue clears | One stopped lane treated as whole-direction congestion |
| `road_obstacle` | Persistent non-road-user object/change on carriageway, with appearance verification | Appears → removed | Shadows, road paint, or potholes treated as new debris |
| `fire_smoke` | Specialized visual evidence sustained over time | First visible smoke → clears or video ends | Tree shadows, haze, dust, or glare |

Do not apply one universal minimum-duration filter or merge gap to every class. Genuine short manoeuvres can be valid events. Merge truly overlapping same-class segments, and only join separated fragments when evidence supports one continuous event.

Standard road-user YOLO detections do not solve arbitrary debris or smoke recognition. Persistent foreground/background differences can propose obstacle candidates, but illumination changes and stationary-object absorption require explicit handling and a semantic check. [OpenCV background subtraction](https://docs.opencv.org/4.x/d1/dc5/tutorial_background_subtraction.html).

Implementation order: road geometry and tracking first; stopped-vehicle, wrong-way, pedestrian/crossing, and direction-level queue logic next; signal and turn rules once their scene facts are verified; accident/near-miss verification and specialist obstacle/smoke recognition next. Keep every class represented in the design and report actual validated coverage honestly.

Ask organizers how normal signal queues should be treated under `congestion`: its definition does not explicitly exclude them, unlike `stopped_vehicle`. Also clarify bicycle/scooter riders versus pedestrians where this changes crossing labels.

## 7. Accident anticipation without looking ahead

Build a separate streaming state with its own tracker and history. Sharing immutable model weights is acceptable; sharing completed-video trajectories or event predictions from Part A is not. Reset all per-video state, and add a prefix-invariance check: identical received frame prefixes must yield identical risk scores regardless of the unseen continuation.

Candidate signals include predicted path intersection, closing motion, minimum separation, braking, wrong-way motion, and vehicle–pedestrian conflicts. Where calibration supports it, compute closest-approach time from relative position and velocity, then require a small predicted separation and a physically compatible path. Close approach time alone is insufficient: vehicles in adjacent lanes can pass safely.

Use only past frames for smoothing and derivatives. Part B cannot use centred windows, bidirectional tracking, or Part A's refined contact time. Sample inference internally if necessary and return the last valid score for other calls. Include those skipped-frame outputs in the normal harness execution.

Map the features to a bounded risk score and tune on held-out labels. If the samples contain no accidents, state that camera-specific probability calibration and anticipation accuracy cannot be established from those samples. External accident data may support training, but perspective differences must be acknowledged. A bounded heuristic is not automatically a calibrated probability.

## 8. External data and model research decisions

| Candidate | Relevance | Decision before implementation |
| --- | --- | --- |
| Organizer samples plus our annotations | Exact target camera and scoring definitions | Highest priority; annotate first and retain held-out footage |
| CADP | Fixed CCTV accident detection/forecasting; 1,416 video segments, 205 with full spatiotemporal annotations | Relevant potential accident-training source; author page limits use to noncommercial/research purposes |
| DoTA | Traffic anomalies with temporal/spatial/category annotations; driving-video viewpoint | Secondary transfer source; do not assume dashcam performance transfers to elevated CCTV |
| ACCIDENT | Recent fixed-surveillance accident benchmark, real and synthetic clips | Promising research lead; verify downloadable split, exact licence, provenance, and compatibility before use |

Primary sources: [CADP](https://ankitshah009.github.io/accident_forecasting_traffic_camera), [DoTA](https://github.com/MoonBlvd/Detection-of-Traffic-Anomaly), [ACCIDENT](https://accidentbench.github.io/), [ACCIDENT repository](https://github.com/accidentbench/ACCIDENT).

DoTA's project documents a roughly 55 GB frame archive, so downloading it wholesale should not precede a useful baseline. A repository's code licence is not automatically a complete licence for every underlying video. Record dataset and checkpoint terms separately, along with versions, hashes, and attribution. Exclude any accidentally discovered footage from the target camera, including within public datasets.

Use a small temporal classifier for ambiguous accident/near-miss candidate clips only if we have suitable labels and time to validate it. Large video-language models add memory, packaging, and latency costs; they are a later measured experiment, not the first dependency. Closed-model inference is prohibited, including in the live demo's event-analysis path.

Ultralytics describes its open-source option under AGPL-3.0. Plan the public submission and notices accordingly, and verify terms for the exact weights/runtime selected. The previous road-model repository labels its code Apache-2.0; that label alone does not settle every dependency's terms. [Ultralytics licensing](https://www.ultralytics.com/license). Official [RT-DETR](https://github.com/lyuwenyu/RT-DETR) is an alternative benchmark candidate if needed, not a reason to delay a working YOLO baseline.

## 9. Data annotation and evaluation plan

1. Obtain original copies of the four provided videos only; preserve their names and record hashes, metadata, and decoding integrity.
2. Measure resolution, FPS, duration, brightness distribution, blur, object size versus image location, and stability of static landmarks.
3. Map the road geometry and signal-to-lane relationships once, then verify them across all clips.
4. Watch all clips and annotate event intervals using the official definitions. Review uncertain contact/near-miss frames closely. Keep confirmed labels separate from uncertain notes.
5. Explicitly annotate normal traffic periods as useful negative evidence. Review signal queues, safe close passes, bus stops, legal turns, and people standing on islands.
6. Split by video or separated time blocks, not random adjacent frames. With only four clips, use leave-one-video-out checks where feasible and disclose their limited statistical strength.
7. Compare detectors on a small manually checked set covering each lighting condition and small road users. Fine-tune only if recall misses justify annotation/training effort.
8. Run the unchanged evaluator and examine per-class F1 at all three thresholds, boundary errors, false events per minute, anticipation AP/alarm F1/lead time, runtime, and peak memory.
9. Change one substantive factor at a time: detector choice, tracker, sampling rate, geometry correction, event confirmation, temporal verification.
10. Publish genuine results, including unvalidated classes and failure examples. Do not report sample-tuned performance as hidden-test accuracy.

Quantitative website EDA should include object counts over time, unique tracks versus raw detections, trajectory maps, occupancy/density per direction, motion heatmaps, signal visibility, and a short explanation of how these findings changed the algorithm. Counts must distinguish detections per frame from unique road users.

## 10. Simple dashboard based on the supplied references

Adopt the reference's light grey background, white rounded cards, fine borders, compact left sidebar, restrained blue/green/amber accents, and generous spacing. Use red mainly for confirmed critical events. Translate its project-management layout into a traffic-analysis workflow.

The main screen should contain:

- Header: selected sample or uploaded video, analysis status, and one prominent Upload video button.
- Three compact summary cards: detected events, road users/traffic activity, and risk summary with its time context clearly stated.
- Large video player with boxes, trajectories, and road zones available through direct on/off controls.
- Beside it, a readable event list with label, start/end, duration, and an explanation/evidence frame.
- Below, a colored event timeline synchronized with playback; clicking any interval seeks the video.
- A synchronized anticipation curve, including the 0.5 alarm threshold and a clear explanation of the five-second horizon.
- A filterable event table and downloadable official JSON.

Use four sidebar destinations: **Dashboard**, **Samples & Insights**, **Approach & Report**, **Team**. Samples & Insights covers every supplied video and EDA. Approach & Report separates learned components from rules and includes failure cases and ablations. Team includes three members, contributions, and real portfolio links. Repository, weights, and sample predictions remain easy to find.

The upload flow stays on the dashboard: choose MP4 → validate → show queued/analyzing/visualizing progress → display results. Start with a clearly stated two-minute limit and a measured file-size limit. Show useful handling for invalid files, videos with no events, unsupported camera viewpoints, and analysis failure. Avoid accounts, workspace switching, multi-camera administration, and a separate job-management interface in the first version.

This is a single-camera challenge. Accepting an arbitrary MP4 does not make the rule system calibrated for any intersection. Explain that limitation in the demo and detect obvious scene mismatch when possible.

A small React/TypeScript frontend with a Python FastAPI backend is a suitable proposed structure. Use one inference worker with a bounded queue; persistent job metadata and local result storage are enough initially. Serve the built frontend and API together where practical. The same core Python engine should power evaluation and the website, with richer UI metadata kept separate from the official event tuples. No duplicate browser-only inference engine is necessary.

Deployment must provide an actual Python inference process. A static website alone cannot satisfy the upload-and-run requirement. Select hosting after CPU throughput, available GPU resources, and judging-period uptime needs are known; no hosting purchase is assumed.

## 11. Build milestones and acceptance checks

| Stage | Concrete output | Completion evidence |
| --- | --- | --- |
| Scene and labels | Source manifest, camera map, reviewed event labels, EDA summary | Every sample inspected; uncertain scene facts listed |
| Runnable baseline | Thin `solution.py`, local detector, tracker, initial event rules | Official harness runs and evaluator validates output |
| Coverage and timing | Class modules and candidate-window refinement | Per-class scores and boundary-error review on held-out footage |
| Causal risk | Streaming estimator and risk curve | Prefix invariance, clean reset, alarm analysis |
| Website | Reference-inspired dashboard and actual upload processing | MP4 upload → model → synchronized results works on desktop/mobile |
| Submission | Weights, pinned environment, report, sample outputs, public release | Clean-machine offline run, repeated predictions, runtime margin |

Keep responsibilities separate: video I/O; detection; tracking; scene geometry; signals; event modules; causal risk; segment merging; evaluation/EDA tools; API/job processing; frontend. Review executable files at 500 lines and keep them below 700 unless cohesion explicitly justifies otherwise. Preserve the third-party organizer files intact.

Measure **Part A plus Part B** together under the normal harness flags. Both passes decode the video; do not budget only detector speed. A sensible engineering target is at most twice video duration, leaving margin under the official three-times limit. This target is proposed, not yet measured. Account for model initialization, decoding, tracking, and dense risk output, and avoid keeping all decoded frames in memory.

For a three-person team, suggested responsibilities are: model/tracking/risk; scene annotation/rules/evaluation; dashboard/API/deployment/report. Labels and failure cases should be reviewed across roles. Actual people and contributions must be supplied rather than invented.

Before final submission verify: all weights local and under 5 GB; no inference network requests; unchanged organizer files; valid finite event/risk outputs; no same-class overlaps; end-of-file event handling; per-video state reset; deterministic reruns; runtime within budget; live upload failure handling; every sample visualized; README provenance and licences; release commit and public website available to judges.

## 12. Decisions still requiring facts

- Exact deadline and remaining working time.
- The user's PC graphics card model and VRAM; a PC alone does not establish CUDA availability. CPU development can start, but GPU training/runtime claims require measurement.
- Whether the organizers have `camera.md` or equivalent road-rule clarification.
- Original video metadata and full annotations, including whether any accidents occur in the samples.
- Team names, roles, and portfolio links.
- Hosting resources and how long the site must remain online.

**First build action:** acquire and inspect the original samples, prepare the scene map and a small reviewed label set, then benchmark the existing road YOLO model against a general YOLO model. This gives the evidence needed to choose the detector and implement the dashboard around real outputs.
