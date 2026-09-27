"""Scratch analysis helpers: per-track trajectories from the dev cache (reference coordinates)."""
import sys
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2]))
from scripts.devset import CACHE, load, ReplayScene  # noqa: E402
from vision.settings import Settings  # noqa: E402
from vision.tracks import Tracks  # noqa: E402
from vision.types import Observation, VEHICLES  # noqa: E402
from vision.rules.crossing import is_rider  # noqa: E402

SETTINGS = Settings.load()


def scene_for(data, config=None):
    scene = ReplayScene(config or SETTINGS.camera())
    scene.matched = data["matched"]
    scene.matrix = None if data["matrix"] is None else np.asarray(data["matrix"])
    return scene


def trajectories(name, config=None):
    """Return data, scene, and {id: dict(kind, rows=[(t, fx, fy, rx, ry, speed_rel, stopped, box, rider)])}."""
    data = load(CACHE / f"{name}.pkl.gz")
    scene = scene_for(data, config)
    tracks = Tracks()
    out = defaultdict(lambda: {"votes": Counter(), "rows": []})
    for record in data["frames"]:
        t = record["t"]
        obs = [Observation(i, k, s, b) for i, k, s, b in record["obs"] if s >= SETTINGS.confidence]
        active = tracks.update(obs, t)
        for tr in active:
            o = tr.observation
            rx, ry = scene.point(o.foot)
            rider = o.kind == "person" and is_rider(tr, active)
            item = out[o.id]
            item["votes"][o.kind] += 1
            item["rows"].append(
                (t, o.foot[0], o.foot[1], rx, ry, tr.speed / o.height,
                 tr.stopped_since is not None, o.box, rider, tr.velocity)
            )
    result = {}
    for identity, item in out.items():
        kind = item["votes"].most_common(1)[0][0]
        result[identity] = {"kind": kind, "rows": item["rows"]}
    return data, scene, result


def intervals(times, flags, gap=1.0, minimum=0.4):
    """Merge sampled boolean flags into [start, end] intervals."""
    spans, start, last = [], None, None
    for t, f in zip(times, flags):
        if f:
            if start is None or t - last > gap:
                if start is not None and last - start >= minimum:
                    spans.append((start, last))
                start = t
            last = t
    if start is not None and last - start >= minimum:
        spans.append((start, last))
    return spans
