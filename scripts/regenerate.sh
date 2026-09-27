#!/bin/sh
# Rebuild every sample artifact from the current code, check it, and package the release.
# Run from the repository root with the four organizer samples in samples/.
set -eu
PY=${PYTHON:-.venv/bin/python}

echo "== web pipeline: annotated video, EDA maps, analysis =="
for v in C3896 C3897 C3902 C3905; do
  rm -rf "output/$v"
  $PY -m vision.cli "samples/$v.MP4" --output "output/$v"
done

echo "== official harness, Part A + Part B =="
$PY run_submission.py --videos samples --out predictions_samples.json --team crossing

echo "== determinism: second harness run on C3905 =="
mkdir -p output/determinism
$PY run_submission.py --videos samples/C3905.MP4 --out output/determinism/predictions.json --team crossing
$PY - <<'EOF'
import json
first = json.load(open("predictions_samples.json"))["videos"]["C3905.MP4"]
second = json.load(open("output/determinism/predictions.json"))["videos"]["C3905.MP4"]
web = json.load(open("output/C3905/analysis.json"))
print("C3905 events identical:", first["events"] == second["events"], "| risk identical:", first["risk"] == second["risk"])
print("web pipeline events identical to harness:", web["events"] == first["events"])
EOF

echo "== format check and dev-set score =="
$PY evaluate.py --pred predictions_samples.json --validate-only
$PY evaluate.py --pred predictions_samples.json --gt devset/labels.json --per-video
$PY -m scripts.devset score --pred predictions_samples.json --json devset/report.json

echo "== permanent sample gallery and release archives =="
$PY -m scripts.archive
$PY -m scripts.package
