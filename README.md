# Crossing

Traffic-event detection and accident anticipation for one fixed CCTV camera, built for the WIUT
Hackathon CV Track.

- **Website and live demo:** https://wiut.mardonjon.me
- **Release (weights, sample results):** [v1.0.0](https://github.com/rmm-code/wiut-hackathon-task/releases/tag/v1.0.0)
- **Technical report:** [docs/report.md](docs/report.md) (also on the website's Report page)
- **Sample predictions:** [predictions_samples.json](predictions_samples.json)

## Run the submission

Python 3.10–3.13 (tested on 3.10 and 3.12), ffmpeg/ffprobe and the OpenCV system libraries (`libgl1`,
`libglib2.0-0`). On Linux, pip installs the CUDA 12.6 build of PyTorch, which runs on any NVIDIA driver
from 525 up, T4 included. Download the weights once, with internet, before the offline run:

```sh
pip install -r requirements.txt
sh weights/download.sh          # downloads and SHA-256-verifies the three checkpoints (139.1 MB)
python run_submission.py --videos /data/test --out predictions.json
python evaluate.py --pred predictions.json --validate-only
```

`run_submission.py` and `evaluate.py` are the organizer files, unchanged; a test checks their hashes.
Inference never downloads anything: Ultralytics auto-install, online checks and settings sync are
disabled, and a missing checkpoint raises an error. The weights are also attached to the release as
`weights.tar`. Extract it in the repository root instead of running the download script.

Docker: `docker build -t crossing .`, then
`docker run --rm --network none -v /data/test:/data/test:ro -v "$PWD/output:/results" crossing python run_submission.py --videos /data/test --out /results/predictions.json`.
Run the weight download before building. The image installs the same CUDA 12.6 PyTorch build.

`CROSSING_DEVICE` selects `auto` (CUDA, then MPS, then CPU), `cuda:0`, `mps` or `cpu`. `CROSSING_FPS`
sets the analysis sampling rate (default 8 frames/s).

## How it works

```text
video ─► YOLO11s (COCO road users) ─► ByteTrack ─► camera alignment ─► scene rules ─► segments ─► events
                                     │                (SIFT homography)   per class      merge,
          accident / fire specialists ┘                                                  min length
frames one by one ─► own YOLO11s + ByteTrack ─► closest-approach conflict score ─► risk (Part B)
```

1. **Detection and tracking (learned).** Pretrained YOLO11s finds cars, buses, trucks, motorcycles,
   bicycles, people and animals in every fourth frame (about 7.5 frames/s at 29.97 fps). ByteTrack
   links the detections into tracks.
2. **Camera alignment (rule-based).** The first frame is matched to the organizer reference view with
   SIFT and RANSAC. If the match fails, the video is treated as a different camera and every scene rule
   is switched off.
3. **Scene rules (rule-based).** The geometry is mapped once on an empty-road background of the samples
   ([calibration](docs/calibration.md)). Each class has a small rule over tracks and that geometry
   ([classes](docs/classes.md)).
4. **Specialists (learned).** Two open-weights YOLO checkpoints propose accident and fire/smoke boxes
   about once a second. Temporal confirmation and road gating decide which become events.
5. **Segments.** Per-class minimum durations drop blips, and same-class events are merged, following
   the organizers' convention that simultaneous events form one segment.
6. **Part B.** `RiskEstimator` creates its own detector and tracker, sees only the frames it is given,
   and scores closest-approach conflicts (time to collision, predicted miss distance, detector
   confidence). The score is calibrated so the 0.5 alarm threshold is crossed about 0.9 times a minute
   on normal traffic. It never reads Part A output.

**Classes.** 13 of the 14 official classes are active on this camera. `near_miss` is implemented and
tested but switched off: our review of the samples found no near miss, and every detection was a
false alarm. A class that is predicted but absent from the test set scores zero in the macro average.

Details of each class, the legal basis of the two turn classes (Uzbekistan traffic rules, clauses 56
and 62), and the evidence for every camera fact are in [docs/classes.md](docs/classes.md).

## Accuracy on our sample labels

We labelled the four organizer samples ourselves; the method is in [devset/README.md](devset/README.md).
The labels are in the official ground-truth format:

```sh
python evaluate.py --pred predictions_samples.json --gt devset/labels.json --per-video
```

| Class | Labelled | Predicted | Precision | Recall | F1 @ tIoU 0.3 / 0.5 / 0.7 |
| --- | ---: | ---: | ---: | ---: | --- |
| stop_line | 10 | 10 | 1.00 | 1.00 | 1.00 / 1.00 / 1.00 |
| red_light | 3 | 3 | 1.00 | 1.00 | 1.00 / 1.00 / 1.00 |
| illegal_turn | 5 | 4 | 1.00 | 0.80 | 0.89 / 0.89 / 0.67 |
| solid_line_crossing | 2 | 3 | 0.67 | 1.00 | 0.80 / 0.80 / 0.40 |
| failure_to_yield | 22 | 33 | 0.52 | 0.77 | 0.62 / 0.62 / 0.58 |
| jaywalking | 36 | 36 | 0.61 | 0.61 | 0.72 / 0.61 / 0.39 |

Precision and recall are at tIoU 0.5. **Score A on these labels is 0.777**; no other class is
labelled or predicted. The predictions this work replaced (353 events in 10 classes) scored **0.085**
on the same labels. Most of the gap comes from false events in classes the samples do not contain:
125 of them, in near_miss, congestion, wrong_way and stopped_vehicle.

The rules were tuned on these same four videos, so the scores are optimistic. Six classes never occur
in the samples, so their accuracy is unmeasured.

## Reproducibility

- Seeds: Python, NumPy and Torch use 42, and the OpenCV alignment resets its RNG to 42. cuDNN
  benchmarking is off and deterministic cuDNN is requested.
- `predictions_samples.json` was produced by the unchanged harness from the tagged commit.
  A second harness run on C3905 produced identical events and an identical risk curve, and the web pipeline's events equal the harness's.
- CPU, MPS and CUDA can differ in floating point, so exact equality across platforms is not guaranteed.
- Dev tooling:
  - `python -m scripts.devset cache` stores detector and tracker output for every sample once.
  - `python -m scripts.devset score` re-runs all rules on that cache in about 10 seconds and scores
    them against `devset/labels.json`.
  - `python -m scripts.sheets` renders the contact sheets used for review.
- Tests: `python -m pytest -q tests` covers the rules, causality, the API, scene matching, segments,
  the organizer file hashes and the submission contract.

## Runtime

The harness gives each video 3 × its duration for Part A and Part B together, and scores a video that
runs over as empty. Official harness on an Apple M5 with MPS:

| Video | Duration | Harness time | Share of the 3 × budget |
| --- | ---: | ---: | ---: |
| C3896 | 340.3 s | 295.6 s | 29% |
| C3897 | 317.8 s | 262.7 s | 28% |
| C3902 | 317.8 s | 270.2 s | 28% |
| C3905 | 127.6 s | 96.7 s | 25% |

On an NVIDIA RTX 4060 with an Intel Core i5-12400 (Windows 11), C3905 took 134.9 s, 35% of its
budget. Pinned to two of the CPU's cores (four threads), a harsher stand-in for the organizers' 8-vCPU
machine, it took 235.2 s (61%). The T4 itself has not been measured.

Decoding the 4K video costs more than the models: the GPU was only about a quarter busy. The harness
decodes every video twice, once in Part A and once in its own Part B loop, and runs the detector
in both, at about 7.5 frames/s. Two measures protect the budget:

- Part A decodes on a background thread while the main thread analyses. It skips the colour
  conversion for the three frames in four it does not analyse. The output is unchanged.
- If a slow machine would push a video over its budget, Part B stops early
  ([vision/budget.py](vision/budget.py)). The harness then keeps that video's events and drops only
  its risk curve.

The public website analyses uploads on four CPU cores: a 20-second 1080p clip took 84 s.

## Website

https://wiut.mardonjon.me runs the same Python engine behind a FastAPI job queue. Visitors can upload a
clip (MP4, up to 2 minutes and 95 MB) and get annotated playback, an event timeline, a risk curve and a
JSON export. The site also has:

- every sample video annotated in full, with event timelines, EDA maps and the accuracy table;
- the report, the team and downloads.

Its deployment (systemd unit and nginx vhost) is in [`deploy/`](deploy/). See
[architecture](docs/architecture.md) for details.

Run it locally with Python 3.12, Node 22.18+ and ffmpeg:

```sh
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
PYTHON=.venv/bin/python sh weights/download.sh
npm --prefix web ci && npm run dev          # http://127.0.0.1:5173
```

## Repository layout

```text
solution.py, run_submission.py, evaluate.py   competition interface and unchanged organizer files
vision/            detection, tracking, camera alignment, rules, segments, risk, rendering, EDA
  rules/           road, crossing, direction, signal, turn and conflict rules
config/camera.json scene geometry and camera facts, each with its evidence
devset/            our sample labels, review notes and the dev-set report
api/               FastAPI endpoints, SQLite job store, bounded analysis worker
web/src/           React website
scripts/           weight setup, dev-set cache/replay/score, contact sheets, archive, packaging
deploy/            public-site systemd unit and nginx vhost
tests/             Python tests
docs/              report, classes, calibration, architecture, API, model research, task text
```

## Models, datasets and licences

No model was trained or fine-tuned by this team. The learned parts detect appearance. Tracking
association, camera alignment, signal reading, every event rule, segment merging and the risk score
are hand-written.

| Component and author | Upstream data | Dataset terms | Checkpoint terms |
| --- | --- | --- | --- |
| YOLO11s — Ultralytics | COCO 2017 | [COCO Consortium](https://cocodataset.org/#termsofuse): annotations CC BY 4.0; images retain individual Flickr rights/terms | Ultralytics AGPL-3.0 open-source terms |
| Fire/smoke YOLO26n — seawsurf | [FASDD CV](https://huggingface.co/datasets/seawsurf/fire_smoke_dataset_fasdd_cv), as identified in the source model card | Publisher declares CC BY 4.0 | Publisher declares CC BY 4.0; Ultralytics base/runtime terms also apply |
| Accident YOLO11x — Uppada Enos | [Traffic Accident Detection, hilmantm](https://universe.roboflow.com/hilmantm/traffic-accident-detection), as identified in the source model card | Publisher declares CC BY 4.0 | Publisher declares MIT; Ultralytics base/runtime terms also apply |
| WIUT organizer footage | C3896, C3897, C3902, C3905 | Provided for this competition | Used for camera geometry, our dev labels and regression fixtures, not for training |

Model cards: [fire/smoke](https://huggingface.co/seawsurf/fire_smoke_detection_box),
[accident](https://huggingface.co/Enos-123/traffic-accident-detection-yolo11x). Revisions and SHA-256
hashes are pinned in `weights/manifest.json`. ByteTrack runs through Ultralytics
([paper](https://arxiv.org/abs/2110.06864)). The website uses the Inter font (SIL OFL), Phosphor icons
(MIT), React, Vite and Recharts.

No other footage from this camera was collected, no hosted or closed model is called at any stage,
and no hidden test data was accessed.

## Team

| Member | Role | Links |
| --- | --- | --- |
| Mardonjon Rasulov | Captain | [Portfolio](https://mardonjon.me), [GitHub](https://github.com/rmmcode) |
| Saidxon Xaydarov | Team member | [Portfolio](https://xaydarov.uz), [GitHub](https://github.com/khdrvss), [LinkedIn](https://www.linkedin.com/in/saidxon-xaydarov) |
| Miraziz Mirvaliyev | Team member | [GitHub](https://github.com/MMiraziz013), [LinkedIn](https://www.linkedin.com/in/miraziz-mirvaliyev-75a685236/) |

`config/team.json` feeds the website's Team page.
