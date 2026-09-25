# Architecture

## Running system

The React frontend communicates with a same-origin `/api` proxy. FastAPI validates and stores uploads, persists job state in SQLite, and returns a job ID. A single background worker claims queued jobs and starts an isolated Python inference subprocess. It never blocks an HTTP request on model inference.

The subprocess loads local YOLO weights, decodes the video, detects objects, updates a per-video ByteTrack instance, checks camera correspondence, evaluates scene rules, and computes causal risk. It writes atomic progress JSON, an annotated H.264 MP4, analysis details, and official-format predictions. The worker marks a job complete only after successful process exit and result creation. FastAPI serves owner-scoped results and range-capable video; the UI polls real progress and displays model results separately from illustrative fixtures.

## Responsibilities

| Area | Responsibility |
| --- | --- |
| `web/src/pages`, `components` | Approved compact interface and review interactions |
| `web/src/hooks/useJob.ts` | Submit, poll, cancellation, stale-request protection |
| `web/src/hooks/useWorkspace.ts` | Selected video, playback, analysis, import/export, review state |
| `web/src/lib/api.ts` | Typed HTTP boundary |
| `api/main.py` | Validation, ownership, endpoints, trusted sample submission |
| `api/store.py` | SQLite state and recovery/retention records |
| `api/worker.py` | Bounded subprocess execution, cancellation, runtime limits, cleanup |
| `vision/detector.py` | Local YOLO and independent tracker IDs |
| `vision/scene.py` | Contrast-normalized SIFT matching, verified homography, scene queries |
| `vision/tracks.py` | Bounded observation history and time-based movement estimates |
| `vision/rules/` | Provisional or explicitly disabled event rules by responsibility |
| `vision/segments.py` | Confirmation, interval closure, same-class union |
| `vision/risk.py` | Causal streaming estimator and conflict score |
| `vision/pipeline.py`, `media.py` | Shared offline analysis, progress, metadata, annotation |
| `solution.py` | Exact thin competition interface |

## Invariants

- The default frontend preview is never represented as model output. Actual jobs set origin to `model` and include provenance/coverage.
- Official predictions contain filename keys, event tuples, and risk pairs. Extra scene/engine/review metadata remains outside the official video entries.
- Part A may inspect the video. Part B only accepts sequential frames and creates its own detector, tracker, scene state, and risk history; it never reads Part A output.
- No automatic weight download, package installation, or hosted model request occurs during inference. Setup/download scripts run explicitly before the offline stage.
- Histories are bounded; frames are streamed, not all retained in RAM. Annotated frames stream to ffmpeg.
- Active geometry and threshold settings are explicit. Unverified legal facts and unsupported models disable their affected classes.
- SIFT correspondence rejects unsupported camera views rather than applying arbitrary lane rules.
- UI job generations prevent an older result from overwriting a newly selected source. Cancelling a known job terminates its subprocess.
- Review state is browser-session-local and does not change model labels. Server job artifacts expire after 24 hours.

## Local operation and future deployment

`npm run dev` starts FastAPI on 127.0.0.1:8000 and Vite on 127.0.0.1:5173. The API currently binds to loopback. Cookie ownership, origin checks, filename isolation, size/duration checks, bounded concurrency, and retention are implemented. A production deployment still needs environment-specific TLS, origin/cookie settings, upload-body limits at the proxy, storage quotas, rate limiting, monitoring, and final deployment testing.

The static web build is in `web/dist/client`; the retained template Worker is only a static-serving option. Deploy the real model on a Python-capable host, with the frontend and API under one origin or a carefully configured proxy. No deployment has been performed.

Mac/MPS development and the local benchmark do not verify Linux/CUDA behavior. The organizer environment must be tested separately before submission. Model correctness also requires independent labels, specialist class coverage, and event-boundary validation; engineering checks do not establish accuracy.

## Maintainability

Authored source files remain below 700 lines. Review files at 500 lines, split by responsibility, and avoid compressing source to meet limits. Comments explain only non-obvious constraints. Long explanations belong in documentation. Keep the organizer harness/evaluator unchanged and verify their hashes in tests.

## Validation additions

`vision/specialists.py` handles Part A incident appearance evidence independently of `vision/risk.py`. The latter never imports incident results. `vision/eda.py` accumulates measured counts/maps/trajectories; `vision/media.py` writes annotated and clean review copies. `api/review.py` owns manual review validation and private artifacts; `api/limits.py` enforces body sizes before parsers consume chunked uploads. Frontend `Study` and `Labels` components are directly expandable sections, preserving the compact dashboard hierarchy.

A tab remembers its latest job ID and restores it after refresh. Authentication stays in the HttpOnly owner cookie; no owner secret is exposed to browser JavaScript. Labels are explicit, separate from predictions, draft until finalized, and retained only for the job's lifetime. Export is required for permanent storage.
