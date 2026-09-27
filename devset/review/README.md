# Review provenance

Everything used to build `../labels.json`, kept so the labels can be audited and rebuilt. The rendered
contact sheets are not stored; the scripts regenerate them into `sheets/`, which git ignores. Run the
scripts from the repository root after `python -m scripts.devset cache`.

| File | Role |
| --- | --- |
| `rubric.md`, `zones.jpg` | Reviewer instructions quoting the official class definitions, and the named-zone map |
| `cands.py` → `cands.json`, `lamps.json` | Loose candidates for every class from the cached tracks, and per-frame lamp readings |
| `episodes.py` → `episodes.json`, `batches/` | Overlapping candidates grouped into review episodes and split into reviewer batches |
| `results/` | Reviewer-agent verdicts on the episodes (jaywalking in C3896 and part of C3897; failure to yield in part of C3897; all near-miss and wrong-way episodes) |
| `jaywalking/`, `failure_to_yield/` | Manual review of the tuned rule's detections plus a looser rule's extra detections, one verdict per item |
| `render_review.py` | Contact sheets for those two reviews |
| `solid_line/`, `lane_shift.py`, `render_solid.py`, `evidence/` | Solid-line candidates, the lane-coordinate measurement and 4K zoom evidence |
| `stopped_vehicle/` | Review of every stopped-vehicle detection (all rejected, with reasons) |
| `manual_final.json`, `stopline_phases.json`, `uturners.json` | Zoom-checked red-light, stop-line and illegal-turn labels, the per-phase stop-line measurement and the tracked U-turns |
| `assemble.py` | Builds `../labels.json` and `../notes.json` from all of the above |
| `tune.py`, `tune_*.log` | Parameter grids scored with the official metric, and their output |
