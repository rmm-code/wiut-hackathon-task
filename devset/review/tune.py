"""Tune rule parameters against devset/labels.json with the official Part A metric.

    python devset/review/tune.py baseline      # all classes, current parameters
    python devset/review/tune.py jaywalking    # grid over jaywalking margins / minimum / merge gap
    python devset/review/tune.py yield         # grid over failure_to_yield reach / end margin / walking speed

Each grid prints the pooled mean F1 over tIoU 0.3/0.5/0.7 and the per-video F1@0.5, so a
setting that only wins on one clip can be told apart from one that is stable across all four.
"""
import itertools
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from evaluate import evaluate_part_a  # noqa: E402
from scripts.devset import CACHE, load, replay  # noqa: E402
from vision.rules.crossing import CrossingRules  # noqa: E402
from vision.rules.road import RoadRules  # noqa: E402
from vision.segments import Segments  # noqa: E402

LABELS = json.loads((REPO / "devset" / "labels.json").read_text())
DATA = [load(p) for p in sorted(CACHE.glob("*.pkl.gz"))]


def predict(classes):
    return {d["video"]: {"events": [e.tuple() for e in replay(d) if e.label in classes]} for d in DATA}


def report(pred, classes):
    gt = {k: {**v, "events": [e for e in v["events"] if e[2] in classes]} for k, v in LABELS.items()}
    return evaluate_part_a(gt, pred, per_video=False)


def per_video(pred, label):
    out = []
    for video in sorted(LABELS):
        gt = {video: {**LABELS[video], "events": [e for e in LABELS[video]["events"] if e[2] == label]}}
        p = {video: {"events": [e for e in pred[video]["events"] if e[2] == label]}}
        r = evaluate_part_a(gt, p)["per_class"].get(label)
        out.append(r["0.5"]["f1"] if r else float("nan"))
    return out


def row(rep, label):
    r = rep["per_class"].get(label)
    if not r:
        return f"{label:<20} absent"
    m = r["0.5"]
    return (f"{label:<20} P {m['precision']:.2f} R {m['recall']:.2f}  F1 {r['0.3']['f1']:.2f}/{r['0.5']['f1']:.2f}/"
            f"{r['0.7']['f1']:.2f}  mean {r['f1_mean']:.3f}  TP/FP/FN@.5 {m['tp']}/{m['fp']}/{m['fn']}")


def grid(label, space, apply):
    results = []
    for values in itertools.product(*space.values()):
        params = dict(zip(space, values))
        apply(**params)
        pred = predict({label})
        rep = report(pred, {label})
        mean = rep["per_class"][label]["f1_mean"] if label in rep["per_class"] else 0.0
        pv = per_video(pred, label)
        results.append((mean, params, pv))
        print(f"{params}  {row(rep, label)}  per-video F1@.5 {['%.2f' % x for x in pv]}")
    results.sort(key=lambda r: -r[0])
    print("\nbest:")
    for mean, params, pv in results[:5]:
        print(f"  {mean:.3f} {params} per-video {['%.2f' % x for x in pv]}")
    return results


def jaywalking(edge, crossing, minimum, gap):
    RoadRules.edge_margin, RoadRules.crossing_margin = edge, crossing
    Segments.minimum = {**Segments.minimum, "jaywalking": minimum}
    Segments.merge_gap = {**Segments.merge_gap, "jaywalking": gap}


def yield_(reach, end_margin, walking, gap):
    CrossingRules.reach, CrossingRules.end_margin, CrossingRules.walking = reach, end_margin, walking
    Segments.merge_gap = {**Segments.merge_gap, "failure_to_yield": gap}


if __name__ == "__main__":
    what = sys.argv[1:] or ["baseline"]
    if "baseline" in what:
        from vision.types import CLASSES
        pred = predict(set(CLASSES))
        rep = report(pred, set(CLASSES))
        for label in rep["classes"]:
            print(row(rep, label))
        print(f"Score A on dev labels: {rep['score_a']:.4f} over {len(rep['classes'])} classes")
    if "jaywalking" in what:
        grid("jaywalking", {"edge": [0.0, 0.06, 0.12], "crossing": [0.0, 0.06, 0.12],
                            "minimum": [1.0, 2.0, 3.0], "gap": [0.0, 1.5]}, jaywalking)
    if "yield" in what:
        grid("failure_to_yield", {"reach": [0.75, 1.0, 1.5], "end_margin": [0.03, 0.06, 0.12],
                                  "walking": [0.2, 0.3, 0.45], "gap": [0.0]}, yield_)
