# Submission checklist

Every requirement in the task PDF, [research/WIUT Hackathon _ CV Track Elimination Task.pdf](../research/WIUT%20Hackathon%20_%20CV%20Track%20Elimination%20Task.pdf)
(text in [task.md](task.md)), checked on 27 September 2026. Status: **done**, **partial** or **not done**.

## Submission package (PDF page 7)

| Requirement | Status | Where |
| --- | --- | --- |
| One public repository link (tag) and one website link | Done | https://github.com/rmm-code/wiut-hackathon-task/tree/v1.0.0 and https://wiut.mardonjon.me |
| `solution.py` at the root with `CLASSES`, `detect_events`, `RiskEstimator` | Done | `tests/test_contract.py` |
| `run_submission.py` and `evaluate.py` unchanged | Done | Hash-checked against the starter kit in `tests/` |
| `requirements.txt` or a Dockerfile | Done, both | The Docker build downloads the weights; run it with `--gpus all` ([README](../README.md)) |
| Weights ≤ 5 GB, or `download.sh` | Done | 139.1 MB; `weights/download.sh` checks SHA-256; also `weights.tar` in the release |
| `predictions_samples.json` | Done | The harness on the tagged code reproduces its events and risk curves exactly on all four samples |
| Both commands work on a clean machine | Done | Clean Linux Python 3.10 container (CPU); Windows with an RTX 4060 (GPU) |
| README: install and run, including the weights | Done | [README](../README.md) "Run the submission" |
| README: architecture, models, datasets and licences, learned vs rule-based | Done | README "How it works" and "Models, datasets and licences" |
| README: fixed seeds and anything non-deterministic | Done | README "Reproducibility", including the budget guard's wall-clock dependence |
| README: team members and who did what | Done | README "Team" |

## Hardware and limits (page 7)

| Limit | Status | Evidence |
| --- | --- | --- |
| T4-class GPU, 8 CPU cores, 32 GB | Partial | Not run on a T4. C3905 used 35% of its time budget on an RTX 4060, and 61% with the process pinned to two CPU cores |
| No internet during evaluation | Done | Nothing is downloaded at inference; a missing checkpoint raises an error |
| At most 3 × the video duration | Done | 25–29% of the budget on an Apple M5; Part B stops early rather than let a video run over |
| Python 3.10 or newer | Done | Installs on 3.10–3.13 |

## Interface and rules (pages 5, 9–10)

| Rule | Status | Evidence |
| --- | --- | --- |
| The 14 official class ids, none added | Done | `vision/types.py` |
| Part B is causal and never opens the video or reuses Part A output | Done | `tests/test_causality.py`; the budget guard shares only Part A's start time |
| Two runs give the same predictions | Done | Repeated harness runs are identical; near the budget the guard can stop Part B in one run and not another (README) |
| Open weights only, no hosted models or paid APIs | Done | Three pinned open checkpoints |
| Every dataset and licence listed | Done | README table; no training data of our own |
| Open-source reuse attributed | Done | README |
| Website shows only material we have rights to | Done | Our own renders of the organizer samples; our own team photo |

## Model (pages 1–6)

| Item | Status | Evidence |
| --- | --- | --- |
| Part A: events as `[start, end, label]` | Done | 13 of 14 classes active; `near_miss` is off because every sample detection was a false alarm |
| Accuracy on our own dev labels | Done | Score A 0.777 on 78 labelled events in six classes ([devset/](../devset/README.md)); tuned on the same videos |
| Part B: a risk score for every frame | Done | Calibrated so 0.5 is the alarm level; unmeasured, because the samples contain no accident |
| Annotators' start and end conventions | Done | [classes.md](classes.md) |

## Website: required sections (pages 8–9)

| Section | Status | Where on https://wiut.mardonjon.me |
| --- | --- | --- |
| 1. Team: roles, who did what, GitHub, LinkedIn, portfolios, previous projects | Partial | "Our team": photos, roles, contributions, links and previous projects. Missing: a portfolio for Miraziz |
| 2. Problem and approach: pipeline diagram, models and data, learned vs rule-based | Done | "Approach & report": the problem, a nine-step pipeline with each step marked learned or rule-based, and the models, data and licences |
| 3. EDA: resolution, fps, duration, lighting; counts by class; heatmaps; trajectories; lane directions; density over time | Done | "Samples & insights": a measured table (resolution, fps, duration, brightness, road users by class), a lanes-and-directions map, occupancy, motion and trajectory maps for every sample, and findings that shaped the rules. Counts over time are charted for the open video |
| 4. Results: every sample annotated, timelines, risk curves, class examples, failure cases | Done | Dashboard (each sample), class examples on "Samples & insights", failures on "Approach & report" |
| 5. Live demo: upload, events, timeline, annotated playback, risk curve, stated limits, progress | Done | "Upload video": MP4 up to 2 minutes and 2.5 GB (sent in pieces), upload and analysis progress |
| 6. Report: what worked, what did not, what next | Done | "Approach & report", and the one-page [report.md](report.md) |
| 7. Links: repository, weights, `predictions_samples.json` | Done | "Downloads & reproducibility" on "Approach & report" |

## Website: extra credit (page 9)

| Idea | Status | Where |
| --- | --- | --- |
| Interactive charts; click an event to jump the video to it | Done | Dashboard timeline and event log |
| Ablations with numbers | Done | "Ablations" on "Approach & report"; `python -m scripts.ablation` |
| Error analysis on our own dev labels | Done | Per-class precision, recall and F1; "Where the errors go" sorts every prediction into correct, another class or false alarm (no class was confused with another); failure cases |
| Operator dashboard: events per class, location, time | Done | "Operator summary" on the Dashboard |
| Live stream or webcam | Not done | |

## Rubrics (pages 8–9)

- **Live demo (30%).** A 20-second clip uploaded to the public site came back complete in 87 s,
  with events, the annotated video and the risk curve. The piece-by-piece path for large files was
  tested end to end on a local server.
- **Sample-video visualizations (20%).** All four samples are annotated in full, with timelines and
  risk curves.
- **EDA (15%), approach and report (15%), team (10%), design (10%).** See the tables above. The layout
  works at phone width.
- **Runs as submitted (40%).** Checked on a clean Linux container and on Windows with an NVIDIA GPU.
- **Reproducibility (25%).** Pinned weights with checksums and fixed seeds; no training. The samples
  reproduce `predictions_samples.json` exactly.
- **Structure (20%).** The engine is in `vision/`, the site's API in `api/`, the site in `web/`, and tools
  in `scripts/`; 61 tests.
- **Engineering judgement (15%).** Frames sampled at 7.5 per second, decoding overlapped with
  analysis, a replay cache for tuning, and a time-budget guard.

## Known gaps

- **Runtime on a T4.** Not measured. The organizers' CPU sets the pace, because 4K decoding dominates.
- **Dev labels.** They are model-assisted AI reviews, not independent human annotation, and the rules
  were tuned on the same videos.
- **Unmeasured classes.** Accident, fire and smoke, road obstacle, congestion, wrong way and illegal
  U-turn never occur in the samples, so their behaviour on real events is unknown.
- **Team page.** Miraziz has no portfolio site to link.
- **Live stream or webcam demo.** Not built.
