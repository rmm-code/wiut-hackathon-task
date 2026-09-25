# Local weights

Run `sh weights/download.sh` once with internet after installing Python dependencies. Activate your Python environment first, or set `PYTHON=/path/to/python`. The script downloads and verifies every checkpoint in `manifest.json`. Inference requires these local files and never downloads missing weights.

| File | Purpose |
| --- | --- |
| `yolo11s.pt` | COCO road-user and supported animal detection |
| `accident.pt` | Provisional accident appearance detection |
| `fire.pt` | Provisional fire/smoke appearance detection |

The three checkpoints total approximately 139.1 MB, below the 5 GB limit. Exact source URLs, pinned revisions, SHA-256 hashes and declared licences are in `manifest.json`; attribution and limitations are in [model research](../docs/research.md). Ultralytics runtime/base-model licence obligations remain applicable separately from specialist checkpoint declarations. No local training or fine-tuning has been performed. Pothole weights are not used.

Checkpoint binaries are excluded from Git. Download them before the offline run, or include the verified files in the separate submission archive supplied to organizers.
