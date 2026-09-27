"""Ablations on the dev set, replayed from the cached detections of `scripts.devset cache`.

Each variant changes one thing and is scored against devset/labels.json with the official metric:
- the rule sampling rate (every 2nd or 4th cached frame; tracks stay the 8 frames/s ByteTrack IDs),
- tracking switched off (every detection gets a fresh identity, so no rule sees motion),
- a higher detector confidence threshold.

    python -m scripts.ablation --json devset/ablation.json
"""

import argparse
import dataclasses
import itertools
import json
from pathlib import Path

from evaluate import evaluate_part_a
from vision.settings import ROOT, Settings

from .devset import LABELS, caches, load, replay


def every(step):
    def keep(data):
        return {**data, "frames": data["frames"][::step]}

    return keep


def untracked(data):
    fresh = itertools.count(10**9)
    frames = [
        {**record, "obs": [(next(fresh), kind, score, box) for _, kind, score, box in record["obs"]]}
        for record in data["frames"]
    ]
    return {**data, "frames": frames}


def score(labels, settings, change=lambda data: data):
    videos = {}
    for path in caches():
        data = change(load(path))
        videos[data["video"]] = {"events": [event.tuple() for event in replay(data, settings)]}
    report = evaluate_part_a(labels, {name: videos.get(name, {"events": []}) for name in labels})
    return {
        "score_a": round(report["score_a"], 4),
        "events": sum(len(video["events"]) for video in videos.values()),
        "per_class": {label: round(report["per_class"][label]["f1_mean"], 3) for label in report["classes"]},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--json", type=Path, help="write the table for the website")
    args = parser.parse_args()
    labels = json.loads(LABELS.read_text())
    settings = Settings.load()
    variants = [
        ("Submitted: rules at 8 frames/s, ByteTrack, confidence 0.20", settings, lambda data: data),
        ("Rules at 4 frames/s", settings, every(2)),
        ("Rules at 2 frames/s", settings, every(4)),
        ("No tracking (a new identity per detection)", settings, untracked),
        ("Detector confidence 0.30", dataclasses.replace(settings, confidence=0.3), lambda data: data),
        ("Detector confidence 0.40", dataclasses.replace(settings, confidence=0.4), lambda data: data),
    ]
    rows = []
    for name, variant, change in variants:
        result = score(labels, variant, change)
        rows.append({"variant": name, **result})
        print(f"{result['score_a']:.4f}  {result['events']:>4} events  {name}")
    if args.json:
        args.json.write_text(json.dumps({"labels": str(LABELS.relative_to(ROOT)), "rows": rows}, indent=1) + "\n")


if __name__ == "__main__":
    main()
