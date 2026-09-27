"""Compact solid-line review sheets: 4 tiles per candidate around its first lane change, 3 candidates per image."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2]))
import cv2, numpy as np
from multiprocessing import Pool
from scripts.sheets import Sheet

HERE = Path(__file__).resolve().parent
items = json.load(open(HERE / "solid_line" / "candidates.json"))
items += [
    {"video": "C3896.MP4", "id": 1595, "t0": 122.1, "t1": 128.3, "changes": [[124.5, 3, 4]], "rule": True},
    {"video": "C3905.MP4", "id": 936, "t0": 49.4, "t1": 52.9, "changes": [[50.9, 4, 5]], "rule": True},
]

def job(video):
    sh = Sheet(video)
    out = {}
    for k, d in enumerate(items):
        if d["video"] != video:
            continue
        t = d["changes"][0][0]
        times = [t - 2.0, t - 0.7, t + 0.7, t + 2.0]
        img = sh.render(t - 2, t + 2, [d["id"]], times=times, columns=4, tile=460, margin=-0.3)
        label = f"{k:02d} {video[:5]} id {d['id']} changes {d['changes'][:3]}{' RULE' if d.get('rule') else ''}"
        cv2.putText(img, label, (6, img.shape[0] - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)
        out[k] = img
    return out

if __name__ == "__main__":
    json.dump(items, open(HERE / "solid_line" / "items.json", "w"), indent=1)
    with Pool(4) as pool:
        parts = pool.map(job, sorted({d["video"] for d in items}))
    rows = {k: v for part in parts for k, v in part.items()}
    keys = sorted(rows)
    for i in range(0, len(keys), 3):
        group = [rows[k] for k in keys[i:i + 3]]
        w = max(r.shape[1] for r in group)
        group = [cv2.copyMakeBorder(r, 0, 6, 0, w - r.shape[1], cv2.BORDER_CONSTANT, value=(255, 255, 255)) for r in group]
        cv2.imwrite(str(HERE / "sheets" / f"solid_{i // 3:02d}.jpg"), np.vstack(group), [cv2.IMWRITE_JPEG_QUALITY, 84])
    print(len(keys), "rendered")
