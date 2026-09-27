"""Lateral lane coordinate of solid-line candidates, from the dev cache.

Solid lane lines sit at 1.5, 2.5, 3.5 and 4.5; lane centres are integers (1 = kerb lane,
5 = median lane). A lane change shows as a sustained, jump-free shift of about one lane
inside the solid section; tracker flicker and identity switches do not.

    python devset/review/lane_shift.py
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
import numpy as np  # noqa: E402
from scripts.devset import CACHE, ReplayScene, load  # noqa: E402
from vision.settings import Settings  # noqa: E402

CONFIG = Settings.load().camera()
LINES = [line["points"] for line in CONFIG["solid_lines"]]
MEDIAN_SIDE = (0.5, 0.2)


def side(point, a, b):
    (ax, ay), (bx, by) = a, b
    signed = ((bx - ax) * (point[1] - ay) - (by - ay) * (point[0] - ax)) / np.hypot(bx - ax, by - ay)
    return signed * np.sign((bx - ax) * (MEDIAN_SIDE[1] - ay) - (by - ay) * (MEDIAN_SIDE[0] - ax))


def coordinate(point):
    d = [side(point, a, b) for a, b in LINES]
    for i in range(3):
        if d[i] >= 0 > d[i + 1]:
            return i + 1.5 + d[i] / (d[i] - d[i + 1])
    if d[0] < 0:
        return 1.5 + d[0] / (d[0] - d[1])
    return 4.5 + d[3] / (d[2] - d[3])


def along(point):
    (ax, ay), (bx, by) = LINES[0]
    return ((point[0] - ax) * (bx - ax) + (point[1] - ay) * (by - ay)) / ((bx - ax) ** 2 + (by - ay) ** 2)


def main():
    items = json.loads((HERE / "solid_line" / "items.json").read_text())
    scenes = {}
    for k, item in enumerate(items):
        video = item["video"]
        if video not in scenes:
            data = load(CACHE / (video[:5] + ".pkl.gz"))
            scene = ReplayScene(CONFIG)
            scene.matched, scene.matrix = True, np.asarray(data["matrix"])
            scenes[video] = (data, scene)
        data, scene = scenes[video]
        t0 = item["changes"][0][0]
        series = [
            (record["t"], coordinate(p), along(p))
            for record in data["frames"]
            if t0 - 4 <= record["t"] <= t0 + 4
            for identity, _, _, box in record["obs"]
            if identity == item["id"]
            for p in [scene.point(((box[0] + box[2]) / 2, box[3]))]
        ]
        if len(series) < 6:
            print(f"{k:02d} {video[:5]} id {item['id']}: too few observations")
            continue
        t, c, f = map(np.array, zip(*series))
        solid = (f >= -0.05) & (f <= 1.0)
        before, after = c[(t < t0 - 0.8) & solid], c[(t > t0 + 0.8) & solid]
        shift = np.median(after) - np.median(before) if len(before) >= 3 and len(after) >= 3 else float("nan")
        step = float(np.max(np.abs(np.diff(c))))
        flag = "lane change" if abs(shift) >= 0.7 and step < 0.45 else ""
        print(f"{k:02d} {video[:5]} id {item['id']:5d}: shift {shift:+.2f}  largest step {step:.2f}  {flag}")


if __name__ == "__main__":
    main()
