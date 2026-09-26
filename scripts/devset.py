"""Development-set tooling for rule tuning against reviewed sample labels.

    python -m scripts.devset cache [VIDEO ...]   # detector, tracker, specialist and lamp output, once
    python -m scripts.devset replay               # rerun event rules on the cache (seconds, not minutes)
    python -m scripts.devset score                # official Part A metric against devset/labels.json

The cache stores observations below the production confidence cut and specialist
detections below their configured thresholds, so thresholds can be tuned without
re-running detection. Replay mirrors `vision.pipeline.analyze` step for step;
`tests/test_devset.py` checks that equivalence on a real clip.
"""

import argparse
import gzip
import json
import pickle
import sys
import time
from pathlib import Path
import cv2
import numpy as np
from vision.media import metadata
from vision.rules import Rules
from vision.scene import Scene
from vision.segments import Segments
from vision.settings import ROOT, Settings
from vision.specialists import Specialists
from vision.tracks import Tracks
from vision.types import CLASSES, Observation

CACHE = ROOT / "output" / "cache"
LABELS = ROOT / "devset" / "labels.json"
VERSION = 1
FLOOR = 0.1
SPECIALIST_FLOOR = 0.25
# Additional lamp regions (reference coordinates) cached for signal-mapping work.
EXTRA_LAMPS = {
    "left pole pedestrian head": [0.128, 0.438, 0.146, 0.476],
}


class CachedFrame:
    """Stands in for a video frame: rules only read lamp crops from it."""

    def __init__(self, crops):
        self.crops = crops


class ReplayScene(Scene):
    def crop(self, frame, roi):
        return frame.crops[tuple(roi)]


def lamp_regions(config):
    regions = {tuple(signal["roi"]) for signal in config.get("signals", [])}
    return regions | {tuple(roi) for roi in EXTRA_LAMPS.values()}


def cache_path(video):
    return CACHE / (Path(video).stem + ".pkl.gz")


def cache(video, settings):
    from vision.detector import Detector

    meta = metadata(video)
    stride = max(1, round(meta["fps"] / settings.sample_fps))
    config = settings.camera()
    scene = Scene(config)
    detector = Detector(settings, meta["fps"] / stride)
    specialists = Specialists(settings, scene)
    regions = lamp_regions(config)
    frames, found = [], {}
    cap = cv2.VideoCapture(str(video))
    index, started = 0, time.perf_counter()
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            t = index / meta["fps"]
            if index == 0:
                scene.align(frame)
            if index % stride == 0:
                observations = detector.step(frame, floor=FLOOR)
                crops = {roi: scene.crop(frame, roi).copy() for roi in regions}
                frames.append(
                    {
                        "i": index,
                        "t": t,
                        "obs": [(o.id, o.kind, o.score, o.box) for o in observations],
                        "crops": crops,
                    }
                )
                if specialists.due(t):
                    specialists.next_time = t + 1.0
                    found[index] = specialists.detect(frame, floor=SPECIALIST_FLOOR)
                if len(frames) % 250 == 0:
                    rate = index / max(1e-9, time.perf_counter() - started)
                    print(f"  {Path(video).name}: {index}/{meta['n_frames']} ({rate:.1f} fps)")
            index += 1
    finally:
        cap.release()
    data = {
        "version": VERSION,
        "video": Path(video).name,
        "meta": meta,
        "decoded": index,
        "stride": stride,
        "matched": scene.matched,
        "inliers": scene.matches,
        "matrix": None if scene.matrix is None else scene.matrix.tolist(),
        "frames": frames,
        "specialists": found,
        "device": detector.device,
    }
    CACHE.mkdir(parents=True, exist_ok=True)
    with gzip.open(cache_path(video), "wb") as stream:
        pickle.dump(data, stream, protocol=pickle.HIGHEST_PROTOCOL)
    print(f"Cached {Path(video).name}: {len(frames)} sampled frames in {time.perf_counter() - started:.0f} s")


def load(path):
    with gzip.open(path, "rb") as stream:
        data = pickle.load(stream)
    if data.get("version") != VERSION:
        raise ValueError(f"Stale cache {path.name}; run `python -m scripts.devset cache` again.")
    return data


def replay(data, settings=None, config=None):
    """Run tracks, rules, specialist confirmation and segmentation on cached output."""
    settings = settings or Settings.load()
    config = config or settings.camera()
    scene = ReplayScene(config)
    scene.matched = data["matched"]
    scene.matrix = None if data["matrix"] is None else np.asarray(data["matrix"])
    tracks, rules, segments = Tracks(), Rules(scene), Segments()
    specialists = Specialists(settings, scene, load=False)
    thresholds = {
        label: item["confidence"]
        for item, _ in specialists.models
        for label in item["classes"].values()
    }
    for record in data["frames"]:
        t = record["t"]
        observations = [
            Observation(identity, kind, score, box)
            for identity, kind, score, box in record["obs"]
            if score >= settings.confidence
        ]
        active = tracks.update(observations, t)
        flags = rules.step(active, t, CachedFrame(record["crops"]))
        if specialists.due(t):
            found = [
                item
                for item in data["specialists"].get(record["i"], [])
                if item[0] in thresholds and item[2] >= thresholds[item[0]]
            ]
            specialists.update(found, active, t)
        segments.update(flags, t)
    meta = data["meta"]
    duration = min(meta["duration"], data["decoded"] / meta["fps"])
    segments.completed.extend(specialists.finish(duration))
    return segments.finish(duration)


def caches():
    paths = sorted(CACHE.glob("*.pkl.gz"))
    if not paths:
        sys.exit("No cached videos; run `python -m scripts.devset cache` first.")
    return paths


def predictions(settings=None, config=None, detail=False):
    videos = {}
    for path in caches():
        data = load(path)
        events = replay(data, settings, config)
        videos[data["video"]] = {
            "events": [event.tuple() for event in events],
            "risk": [],
        }
        if detail:
            videos[data["video"]]["details"] = [
                {"label": e.label, "start": e.start, "end": e.end, "key": e.key}
                for e in events
            ]
    return {"team": "crossing-dev", "videos": videos}


def score(pred, labels):
    sys.path.insert(0, str(ROOT))
    from evaluate import evaluate_part_a

    videos = {name: pred["videos"].get(name, {"events": []}) for name in labels}
    report = evaluate_part_a(labels, videos)
    print(f"{'class':<20}{'P@.3':>7}{'R@.3':>7}{'F1@.3':>7}{'F1@.5':>7}{'F1@.7':>7}{'mean':>7}  TP/FP/FN@.3")
    for label in report["classes"]:
        row = report["per_class"][label]
        low = row["0.3"]
        print(
            f"{label:<20}{low['precision']:>7.2f}{low['recall']:>7.2f}"
            + "".join(f"{row[t]['f1']:>7.2f}" for t in ["0.3", "0.5", "0.7"])
            + f"{row['f1_mean']:>7.2f}  {low['tp']}/{low['fp']}/{low['fn']}"
        )
    print(f"Score A on the dev set: {report['score_a']:.4f} over {len(report['classes'])} classes")
    return report


def summary(report, labels, pred):
    """Compact per-class table for the website."""
    rows = []
    for label in report["classes"]:
        row = report["per_class"][label]
        rows.append(
            {
                "label": label,
                "labelled": sum(1 for v in labels.values() for *_, l in v["events"] if l == label),
                "predicted": sum(
                    1 for name in labels for *_, l in pred["videos"].get(name, {"events": []})["events"] if l == label
                ),
                **{f"f1_{t}": round(row[t]["f1"], 3) for t in ["0.3", "0.5", "0.7"]},
                "precision": round(row["0.5"]["precision"], 3),
                "recall": round(row["0.5"]["recall"], 3),
                "f1_mean": round(row["f1_mean"], 3),
            }
        )
    return {
        "score_a": round(report["score_a"], 4),
        "videos": sorted(labels),
        "labelled_events": sum(len(v["events"]) for v in labels.values()),
        "classes": rows,
        "note": "Our own model-assisted labels of the four organizer samples; see devset/README.md.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    make = sub.add_parser("cache")
    make.add_argument("videos", nargs="*", type=Path)
    run = sub.add_parser("replay")
    run.add_argument("--out", type=Path, default=ROOT / "output" / "dev_predictions.json")
    grade = sub.add_parser("score")
    grade.add_argument("--labels", type=Path, default=LABELS)
    grade.add_argument("--pred", type=Path)
    grade.add_argument("--json", type=Path, help="also write a compact report for the website")
    args = parser.parse_args()
    settings = Settings.load()
    if args.command == "cache":
        videos = args.videos or sorted((ROOT / "samples").glob("*.MP4"))
        for video in videos:
            cache(video, settings)
    elif args.command == "replay":
        result = predictions(settings, detail=True)
        args.out.write_text(json.dumps(result, indent=1))
        for name, video in result["videos"].items():
            counts = {}
            for _, _, label in video["events"]:
                counts[label] = counts.get(label, 0) + 1
            print(name, len(video["events"]), dict(sorted(counts.items())))
    else:
        labels = json.loads(args.labels.read_text())
        pred = json.loads(args.pred.read_text()) if args.pred else predictions(settings)
        unknown = {l for v in labels.values() for *_, l in v["events"]} - set(CLASSES)
        if unknown:
            sys.exit(f"Unknown labels: {sorted(unknown)}")
        report = score(pred, labels)
        if args.json:
            args.json.write_text(json.dumps(summary(report, labels, pred), indent=1) + "\n")


if __name__ == "__main__":
    main()
