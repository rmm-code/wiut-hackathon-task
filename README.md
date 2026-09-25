# Crossing

A traffic-video review system for the WIUT Hackathon CV Track.

**Phase 2 baseline is connected:** uploads run through local YOLO11s + ByteTrack, provisional scene rules, and causal risk scoring. The website displays real job progress, annotated playback, tracked-road-user counts, event intervals, and JSON export. This is **not yet a validated competition model**: see the class-coverage limitations below.

## Start locally

Use Python 3.12, Node 22.18+, npm, and ffmpeg/ffprobe. Tested on an Apple M5 Mac with 16 GB unified memory; CUDA and CPU selection are supported by the code but not yet benchmarked here.

```sh
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.txt
PYTHON=.venv/bin/python sh weights/download.sh
npm --prefix web ci
npm run dev
```

Open http://127.0.0.1:5173. The combined command starts the Python API on port 8000 and the web app on 5173. For separate terminals, use `npm run dev:api` and `npm run dev:web`.

The API is local-only by default. Videos are sent to the local Python server, not to a hosted AI provider. Uploads accept MP4, up to two minutes and 250 MB. Jobs have a bounded queue, cookie-based ownership, cancellation, restart recovery, and cleanup after 24 hours. Cookies/results are not a substitute for a full public-deployment security review.

The default dashboard remains a clearly labeled illustrative preview. Upload a real clip or select a downloaded sample to run the actual engine. Results are labeled **Model results · baseline**, and Analysis details exposes active/disabled rules and calibration limitations. Uploaded video becomes annotated playback on completion. The current job is restored after page refresh; saved labels and outputs follow the server’s 24-hour retention. Export labels to keep them.

## Tests and build

```sh
npm run check
npm test
npm run build
```

`check` verifies strict TypeScript and the 700-line ceiling. `test` runs frontend result validation and Python rules, causality, API ownership, scene matching, and submission-contract tests. No actual traffic-event accuracy is implied by these engineering tests.

## Official offline interface

The root organizer files are byte-identical to the supplied ZIP. The root `solution.py` exposes `CLASSES`, `detect_events`, and `RiskEstimator`.

```sh
.venv/bin/python run_submission.py --videos samples --out predictions_samples.json --team crossing
.venv/bin/python evaluate.py --pred predictions_samples.json --validate-only
# After independently reviewing labels:
.venv/bin/python evaluate.py --pred predictions_samples.json --gt my_labels.json --per-video
```

For the judging environment, install ffmpeg/ffprobe and the system libraries required by OpenCV (the Dockerfile includes them), then install dependencies and download weights once while online:

```sh
pip install -r requirements.txt
sh weights/download.sh
```

After setup, run offline:

```sh
python run_submission.py --videos /data/test --out predictions.json
python evaluate.py --pred predictions.json --validate-only
```

The root Dockerfile supplies the Python environment. Run the weight downloader before building, then use `docker run --rm --network none -v /data/test:/data/test:ro -v "$PWD/output:/results" team python run_submission.py --videos /data/test --out /results/predictions.json` after `docker build -t team .`. Create `output/` first. This container is the Python service/submission environment; it does not publish the web frontend.

Weights must be downloaded before offline execution. `scripts/setup.py` verifies the checkpoint SHA-256 in `weights/manifest.json`. Inference disables Ultralytics automatic installation, online checks, and synchronization. The three installed checkpoints total 139.1 MB; no model training has been performed.

Part B creates a fresh detector/tracker/history and only processes frames supplied by the harness. It does not open the video or reuse Part A results. It returns a bounded, uncalibrated image-space conflict score.

## Sample videos

Only organizer-supplied links are used. Original samples are large: C3905 alone is approximately 2.35 GB, 3840 × 2160, 127.6275 seconds, and 29.97 fps.

```sh
.venv/bin/python -m scripts.samples C3905.MP4
# Omit the name to download all four supplied originals.
.venv/bin/python -m scripts.samples
```

C3905 is downloaded and processed. C3897 and C3902 were moved from Downloads into `samples/`, checked for metadata and first/last-frame decoding, and registered with SHA-256 ready markers. Both have now been fully analyzed on the Mac GPU, with saved results in the app and `output/C3897` / `output/C3902`. C3896 was subsequently imported and fully analyzed too. All four organizer samples now have saved results. Source links remain available in the website. Ready markers store metadata, source URL, and checksum; incomplete downloads are not offered to the sample-analysis endpoint. Trusted server-side originals can exceed the public upload duration/byte limit.

Generate local visual artifacts with:

```sh
.venv/bin/python -m vision.cli samples/C3905.MP4 --output output/C3905
```

This creates `annotated.mp4`, clean `source.mp4`, three traffic-map JPEGs, `analysis.json`, `predictions.json`, and measured progress. Local generated videos, uploads, caches, weights, and environments are excluded from Git. Package verified weights separately for competition submission.

## Coverage and limits

Default provisional rules: pedestrian on road, stopped vehicle, failure to yield, and limited animal-on-road obstacle detection. The camera is matched against the supplied reference before applying those rules. Unknown camera views still get object detection and tracking, but scene-specific events/risk are disabled.

Wrong-way, congestion, signal violations, illegal turns, and solid-line crossings require verified camera facts. Accident and fire/smoke specialist checkpoints are enabled with temporal confirmation but unvalidated accuracy. Near-miss heuristics remain disabled; generic debris is unsupported. The website reports these limits for every analysis. Do not enable unsupported classes merely to advertise full coverage.

There are no independent dev labels yet, so precision, recall, temporal F1, and anticipation accuracy are **not established**. A long predicted interval may be a false positive or a union of concurrent same-class events; review footage before treating it as correct. Mac runtime is not proof of runtime on the organizers' Linux/NVIDIA machine.

## Structure

```text
solution.py        competition adapter
run_submission.py  unchanged organizer harness
evaluate.py        unchanged organizer evaluator
vision/            inference, tracking, scene geometry, events, risk, rendering
  rules/           road, signal, turn, and experimental conflict rules
api/               FastAPI endpoints, SQLite jobs, bounded process worker
config/            provisional camera geometry and explicit verification flags
weights/           model manifest and pre-run download instructions
web/src/           approved React interface, API client, job state, review panels
scripts/           setup, sample download, dev startup, source-size check
tests/             Python engineering checks
samples/           local organizer footage and verified metadata
storage/           private, expiring job artifacts; ignored
output/            local analysis/evaluation artifacts; ignored
docs/              architecture, calibration, evidence, API, provenance
```

The inference package is shared by the web worker and offline adapter. API jobs run in isolated subprocesses; no second browser model or future-aware tracking cache is used. The optional web starter Worker only serves static frontend assets and cannot run the Python model.

## Configuration

Environment variables are listed in `.env.example`; export them before starting. `CROSSING_DEVICE` accepts `auto`, `mps`, `cpu`, or `cuda:0`. `auto` selects CUDA, then MPS, then CPU. `CROSSING_FPS` sets the desired sampling rate. Model and scene paths can be overridden explicitly. Review `config/camera.json` and [calibration notes](docs/calibration.md) before enabling any verification flags.

The Dockerfile has been built for Linux x86_64. All three models run with networking disabled and all 30 Python tests pass in that environment. Public deployment and the target NVIDIA benchmark are still pending; the installed CUDA 13 build needs a compatible NVIDIA driver.

## Documentation and attribution

- [Architecture](docs/architecture.md), [API](docs/api.md), [calibration and rule coverage](docs/calibration.md), [technical report](docs/report.md).
- Official YOLO11s weights and Ultralytics runtime: AGPL-3.0 open-source terms; source and hash in `weights/manifest.json`.
- ByteTrack implementation through Ultralytics; paper: https://arxiv.org/abs/2110.06864.
- User-supplied design references in `design/`; organizer camera still provenance in [assets](docs/assets.md).
- Inter font (SIL OFL), Phosphor icons (MIT), React/Vite, Recharts, and the installed Product Design starter.

No additional footage from the target camera was collected, no closed-model inference API is used, and no hidden test data was accessed. Team member details and public publication remain to be completed.

## Submission audit

Read [the readiness checklist](docs/submission.md), [current measured report](docs/report.md), and [model research and licences](docs/research.md). Run `python -m scripts.check` to identify missing release inputs. All three pinned model weights are verified by `python -m scripts.setup`. The current candidate is not yet a complete public submission.

The supplied specifications are saved as [full task](docs/task.md) and [submission package](docs/package.md).

## Reproducibility

Python `random`, NumPy and Torch use seed 42; OpenCV alignment resets its RNG to 42. cuDNN benchmarking is disabled and deterministic cuDNN behavior is requested. Exact cross-platform numerical equality is not guaranteed between MPS, CPU and CUDA. Independent web/harness output equality has been checked on C3905; final all-sample repeated harness runs and target NVIDIA timing remain unverified. Predictions are model candidates, not human labels.

## Public website

Pushing this repository does not deploy the application. A public installation needs the frontend plus the Python API/worker, ffmpeg, local model weights, and writable storage. Serve the frontend and `/api` under the same HTTPS origin through a reverse proxy, configure `CROSSING_ORIGINS`, and provision persistent sample artifacts. GitHub Pages or another static-only host cannot run the Python inference service. The local two-minute / 250 MB upload limit also applies to the demo unless deliberately changed.
