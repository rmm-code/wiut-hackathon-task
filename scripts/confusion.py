"""Class confusion of predictions_samples.json against our dev labels, at temporal IoU 0.3.

Each prediction is matched like the official metric (greedy by IoU, same class, IoU >= 0.3). An
unmatched prediction counts against the labelled class it overlaps most (IoU >= 0.3), or as a false
alarm; an unmatched label with no overlapping prediction of any class is missed.

    python -m scripts.confusion --json devset/confusion.json
"""

import argparse
import json
from pathlib import Path

from evaluate import tiou
from vision.settings import ROOT

from .devset import LABELS

THRESHOLD = 0.3


def matched(truth, pred):
    """Indices of predictions and labels paired by greedy same-class matching."""
    pairs = sorted(
        (
            (tiou((g[0], g[1]), (p[0], p[1])), i, j)
            for i, p in enumerate(pred)
            for j, g in enumerate(truth)
            if p[2] == g[2]
        ),
        reverse=True,
    )
    used_pred, used_truth = set(), set()
    for iou, i, j in pairs:
        if iou >= THRESHOLD and i not in used_pred and j not in used_truth:
            used_pred.add(i)
            used_truth.add(j)
    return used_pred, used_truth


def confusion(labels, predictions):
    rows, missed = {}, {}
    for name, video in labels.items():
        truth = video["events"]
        pred = predictions["videos"].get(name, {"events": []})["events"]
        used_pred, used_truth = matched(truth, pred)
        for i, p in enumerate(pred):
            if i in used_pred:
                column = p[2]
            else:
                best = max(
                    ((tiou((g[0], g[1]), (p[0], p[1])), g[2]) for j, g in enumerate(truth) if j not in used_truth),
                    default=(0.0, None),
                )
                column = best[1] if best[0] >= THRESHOLD else "none"
            row = rows.setdefault(p[2], {})
            row[column] = row.get(column, 0) + 1
        for j, g in enumerate(truth):
            if j in used_truth:
                continue
            if not any(tiou((g[0], g[1]), (p[0], p[1])) >= THRESHOLD for p in pred):
                missed[g[2]] = missed.get(g[2], 0) + 1
    return {"threshold": THRESHOLD, "rows": rows, "missed": missed}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pred", type=Path, default=ROOT / "predictions_samples.json")
    parser.add_argument("--json", type=Path, help="write the table for the website")
    args = parser.parse_args()
    result = confusion(json.loads(LABELS.read_text()), json.loads(args.pred.read_text()))
    for label, row in sorted(result["rows"].items()):
        print(f"{label:<20} {row}")
    print("missed:", result["missed"])
    if args.json:
        args.json.write_text(json.dumps(result, indent=1) + "\n")


if __name__ == "__main__":
    main()
