# Submission readiness audit

Audit date: 25 September 2026. Compared with both user-supplied specifications: [full task](task.md) and [submission package](package.md). `task.md` preserves the attached text byte-for-byte; `package.md` preserves the submission requirements with normalized Markdown whitespace. These are reference documents. This audit records the implementation's status; it does not change the organizer's requirements.

**Conclusion: a working local candidate, not a complete submission. Perfect operation or accurate traffic-event detection is not established.**

## Required deliverables

| Requirement | Evidence | Assessment |
| --- | --- | --- |
| Public Git repository with tag/commit | The supplied GitHub repository is private. Local Git history has now been initialized for the initial source push; a public release/tag is still outstanding. | Missing |
| Public team website through judging | Only localhost is configured; public release fields are empty. | Missing |
| Root interface | `solution.py` exposes the exact classes, detection function and risk estimator; contract tests pass. | Implemented |
| Unchanged organizer files | SHA-256 verification matches the supplied harness and evaluator. | Verified |
| Clean-machine two-command execution | Earlier Linux x86 Docker build and offline model smoke tests passed. There is no released package to clone and test; the exact final full run on the intended NVIDIA environment remains unverified. | Partial |
| Offline weights, at most 5 GB | Three local pinned/hash-verified checkpoints total 139.1 MB. Inference does not download weights or call hosted AI. | Implemented locally; release delivery missing |
| Expected weight setup | Working `weights/download.sh` delegates to the checksum-verifying Python downloader. Checkpoints stay outside Git and must be downloaded before the offline run. Public release verification remains outstanding. | Downloader implemented |
| Sample predictions | Four videos, 151 candidate events, full per-frame risk arrays; official format validation reports zero errors/warnings. Predictions equal saved per-video analysis artifacts. | Verified |
| Annotated versions of every sample | Full-length H.264 videos, clean review copies, timelines, risk curves and maps are saved for all four clips. | Complete locally |
| EDA | Source metadata, lighting, tracker counts, trajectories, occupancy and image-space motion are generated. Verified legal lane directions and the full requested class/density presentation remain incomplete. | Partial |
| Team and portfolio | Team page contains proposed roles and member placeholders. No three names, actual contributions, profiles or previous projects. | Missing |
| Approach and technical report on website | Basic pipeline/limitations appear in the app. Detailed research, benchmarks and failures live in Markdown; the web page does not yet present the full model/data/licence evidence or concrete class examples/failures. | Partial |
| Live upload demo | Local upload, queue, cancellation, results, playback and fullscreen have been exercised. Public deployment is absent; an in-app browser crash occurred during verification. | Working locally; not publicly verified |
| Public repository/weights/predictions links | GitHub link exists but targets an empty private repository. No complete public release artifact links. | Missing |

The suggested layout uses `src/`; this project instead separates `vision/`, `api/`, and `web/src/`. This is a layout difference, not evidence that the root import contract is broken. `notebooks/` is explicitly optional. Avoid renaming working modules solely to create an appearance of compliance; confirm literal layout expectations if organizers enforce them.

## README checklist

| Required README content | Current status |
| --- | --- |
| Installation, run and weights acquisition | Local, pre-download and offline commands are documented; final clean-release execution still needs verification. |
| Architecture and model descriptions | Basic approach present; specialist detail is mostly in linked research notes. Consolidate a complete learned-versus-rule-based explanation. |
| Every training/pretraining dataset and licence | No local training is claimed. Pretrained sources are partly documented, but the README does not contain the complete dataset/licence ledger requested by the brief. Checkpoint licence declarations do not themselves document dataset licences. |
| Fixed seeds and nondeterminism | Seeds are set in code (Python, NumPy and Torch: 42; OpenCV alignment: 42). README now states them and the platform/reproducibility limits. |
| Team and who did what | Missing. |

Packaging updates corrected the obsolete single-model weight notes and missing-samples research task. The actual manifest contains three models and all four samples are present.

## What “working” means here

Fresh checks during this audit:

- 34 Python tests plus 6 frontend tests passed: **40 engineering tests**.
- TypeScript checking, the production web build and the 700-line source guard passed.
- All organizer-script and weight hashes passed preflight.
- `evaluate.py --pred predictions_samples.json --validate-only`: **4 videos, 151 events, 0 errors, 0 warnings**.
- Saved event/risk arrays match `output/<sample>/analysis.json` for every sample.
- No finalized review-label files were found in the local job storage.

These checks establish interfaces, data format and tested software behavior. They do not measure event precision, recall, temporal F1 or anticipation quality. No honest accuracy percentage can currently be stated.

| Sample | Decoded frames | Candidate events | Web runtime on Mac |
| --- | --- | --- | --- |
| C3896 | 10,200 | 56 | 225.51 s |
| C3897 | 9,525 | 44 | 183.29 s |
| C3902 | 9,525 | 34 | 210.98 s |
| C3905 | 3,825 | 17 | 79.46 s |

The independent unchanged A+B harness benchmark is available only for C3905: 140.0 seconds against 382.9 allowed on the Mac. Other rows are web-pipeline timings, not two-pass harness measurements. All-four-video harness reproduction and the intended NVIDIA benchmark remain outstanding. The earlier Linux test was CPU inference with networking disabled, not a T4 performance test. The final code has evolved since that container check.

Six categories are enabled on a matching camera: accident, stopped_vehicle, jaywalking, failure_to_yield, limited road_obstacle, and fire_smoke. Eight remain off: near_miss, red_light, wrong_way, illegal_u_turn, illegal_turn, solid_line_crossing, stop_line, and congestion. Predicting a subset is permitted by the FAQ; it is not a claim to solve every traffic class and may cost substantial hidden-test recall. Do not invent legal directions or prohibited turns just to enable them.

Part B is optional. Our implementation is causal by design and covered by controlled prefix/reset tests, but its score is an uncalibrated image-space conflict heuristic, not an established probability of an accident within five seconds. Specialist example-image checks are not held-out accuracy evaluation.

Sample outputs copied under `output/` are preserved, but the current website serves owner-scoped job artifacts that expire after 24 hours. A durable public sample gallery still needs to serve the preserved outputs rather than depend on a visitor's temporary jobs. This matters for availability throughout judging.

## Remaining work, in order

1. Finish release packaging and README: weight acquisition/archive, source and dataset attribution, seeds/nondeterminism, team details, and consistent documentation.
2. Establish a reviewed development set and measure errors with the unchanged evaluator. Labels are encouraged rather than a mandatory submitted artifact, but they are needed to substantiate accuracy. Keep held-out video intervals for honest tuning.
3. Verify available scene facts, review active rule boundaries, and improve unsupported classes only with defensible evidence. Validate/calibrate anticipation if claiming the bonus.
4. Run the final harness on all samples from a clean package, compare repeated predictions, and measure the combined budget on compatible NVIDIA hardware.
5. Publish the repository/tag, public weights and sample predictions; deploy a working upload service and durable sample gallery; finish team/report/examples pages and verify public access, playback and uploads.

Do not equate “all four videos processed” or “format VALID” with “submission complete” or “accurate model.”
