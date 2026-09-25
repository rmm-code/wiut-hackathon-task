# Local API — implemented baseline

The frontend uses relative `/api` URLs. Vite proxies them to the local FastAPI service on port 8000.

| Method and path | Behavior |
| --- | --- |
| `GET /api/health` | Weight/encoder readiness and baseline status |
| `POST /api/jobs` | Multipart MP4 upload; returns `202 { id, state, meta }` |
| `GET /api/jobs/{id}` | Actual state, measured frame progress, stage, elapsed time, and error |
| `GET /api/jobs/{id}/results` | Official-format predictions plus separate analysis/coverage details and video URL |
| `GET /api/jobs/{id}/video` | Annotated H.264 MP4 with byte-range support |
| `DELETE /api/jobs/{id}` | Cancel a queued/running job |
| `GET /api/samples` | Supplied sample catalogue with verified local availability |
| `POST /api/samples/{id}/jobs` | Analyze a ready server-side organizer sample |

States: queued → running → complete or failed/cancelled. The UI additionally shows the file-upload/preparation stage. Progress is processed frames / expected frames, followed by a final encoding stage; no simulated analysis timer is used. A job interrupted by a server restart is marked failed with a resubmission message. The worker is single-concurrency with at most three queued/running jobs and a 30-minute local processing cap.

Jobs belong to an HttpOnly SameSite=Strict cookie, whose hash is stored with the job. A different session receives 404 for job status, results, and video. Unknown IDs and path-like IDs are rejected. The current local cookie is not marked Secure because loopback development uses HTTP; configure that with TLS before public deployment.

Uploads have an extension, byte-size, actual-decoding, duration, and resolution check. Stored paths are server-generated UUIDs with fixed filenames. Original names are only metadata and official JSON keys. The upload limit is two minutes / 250 MB; trusted server-side samples bypass that public-demo limit. Job metadata and generated artifacts are retained for 24 hours, with periodic cleanup and startup recovery.

`results` contains `team`, `videos`, `analysis`, and `video_url`. Each entry in `videos` contains only `events` and `risk`. Copy the `team` and `videos` fields when creating competition predictions. Each event is `[start_sec, end_sec, label]`; risk is `[t_sec, score]`. The separate `analysis` object contains model/device, source metadata, candidate evidence, calibration status, enabled/disabled classes, measured counts, and limitations.

No authentication/account UI or external hosted inference is involved. This is a local baseline, not a claim of public-production hardening. A public host still needs reverse-proxy body limits (including chunked bodies), request/storage quotas, configured allowed origins, TLS/cookie policy, monitoring, and availability testing.

## Independent review

Completed jobs expose `GET /api/jobs/{id}/source` for clean playback and `GET /api/jobs/{id}/eda/{occupancy|motion|trajectories}` for measured maps. Older jobs need reprocessing to generate these assets. `GET`/`PUT /api/jobs/{id}/labels` load/save owned reviews. `GET /api/jobs/{id}/labels/export` exports official ground truth only after an explicit full-video review and reviewer name; drafts return 409. Same-class overlaps and invalid boundaries return 400. Review bodies are limited to 1 MB and upload bodies are bounded before multipart parsing, including chunked transfer. All artifacts retain job ownership and 24-hour expiry.

Opening a sample (`POST /api/samples/{id}/jobs`) reuses the owner's completed result, or attaches to that owner's active run. Sample identity is checked against the server original, not the uploaded filename. Concurrent requests are serialized; `?force=true` creates an explicit reanalysis only when no run is active. Completed artifacts remain available when a reanalysis is cancelled. Navigating away no longer implicitly cancels processing. Sample responses include an owner-specific `state`, and result responses include `sample_id` when the input is an organizer original.
