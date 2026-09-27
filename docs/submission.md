# Submission checklist

Requirements from [the task](task.md) and [package instructions](package.md), with where each is met.

| Requirement | Status |
| --- | --- |
| Public repository, tagged commit | https://github.com/rmm-code/wiut-hackathon-task, tag `v1.0.0` |
| `solution.py` with `CLASSES`, `detect_events`, `RiskEstimator` | Root; `tests/test_contract.py` |
| `run_submission.py`, `evaluate.py` unchanged | Hash-checked against the starter kit in `tests/` |
| One-command run, offline | `pip install -r requirements.txt` then `python run_submission.py --videos /data/test --out predictions.json`; no network use at inference |
| Weights ≤ 5 GB, obtainable before the run | 139.1 MB; `weights/download.sh` verifies SHA-256; also `weights.tar` in the release |
| `predictions_samples.json` | Produced by the harness from the tagged code; passes `evaluate.py --validate-only` |
| Time budget (3 × duration) | Harness time 0.76–0.87 × duration on Apple M5 (25%–29% of the budget). C3905 on an RTX 4060: 35%, and 61% pinned to two CPU cores. A video that would run over keeps its events: Part B stops early (`vision/budget.py`) |
| Determinism | Seeds fixed; a repeated harness run on C3905 was identical |
| README: install and run, approach, datasets and licences, learned vs rule-based, seeds, team | [README](../README.md) |
| Website: team, approach, EDA, annotated samples, live demo, report, links | https://wiut.mardonjon.me |
| Technical report | [docs/report.md](report.md) and the website's Report page |
| Own dev labels and error analysis | [devset/](../devset/README.md); per-class table on the website |
| Open weights only; no hosted models | Three pinned open checkpoints; no API calls |

## Known gaps

- **Team contributions.** The Team page lists names, roles and profile links. Individual
  contributions are not described.
- **Judging-GPU runtime.** Measured on an Apple M5 (MPS), an RTX 4060 under Windows, and on CPU for
  the website. Not measured on a T4 or on the organizers' CPU, which sets the pace: 4K decoding
  dominates.
- **Dev labels.** They are model-assisted AI reviews, not independent human annotation, and the rules
  were tuned on the same videos.
- **Unmeasured classes.** Accident, fire and smoke, road obstacle, congestion, wrong way and illegal
  U-turn never occur in the samples. Their behaviour on real events is unmeasured.
