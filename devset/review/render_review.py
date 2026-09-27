"""Render compact 4-tile review rows for a list of detections, three rows per image.

    python devset/review/render_review.py jaywalking
    python devset/review/render_review.py failure_to_yield

Reads <name>/review.json (video, start, end, ids, source) and writes sheets/<name>_NN.jpg.
"""
import json
import sys
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
import cv2  # noqa: E402
import numpy as np  # noqa: E402
from scripts.sheets import Sheet  # noqa: E402

NAME = sys.argv[1] if len(sys.argv) > 1 else "jaywalking"
ITEMS = json.loads((HERE / NAME / "review.json").read_text())


def job(video):
    sheet = Sheet(video)
    rows = {}
    for k, item in enumerate(ITEMS):
        if item["video"] != video:
            continue
        a, b = item["start"], max(item["end"], item["start"] + 0.6)
        times = [a - 0.6, a + (b - a) * 0.35, a + (b - a) * 0.7, b + 0.4]
        image = sheet.render(a, b, item["ids"], times=times, columns=4, tile=400, margin=1.5)
        label = f"{k:02d} {item['source']} {video[:5]} {a}-{item['end']} ids {item['ids']}"
        cv2.putText(image, label, (6, image.shape[0] - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        rows[k] = image
    return rows


if __name__ == "__main__":
    (HERE / "sheets").mkdir(exist_ok=True)
    with Pool(4) as pool:
        rows = {k: v for part in pool.map(job, sorted({i["video"] for i in ITEMS})) for k, v in part.items()}
    keys = sorted(rows)
    for i in range(0, len(keys), 3):
        group = [rows[k] for k in keys[i:i + 3]]
        width = max(r.shape[1] for r in group)
        group = [cv2.copyMakeBorder(r, 0, 6, 0, width - r.shape[1], cv2.BORDER_CONSTANT, value=(255, 255, 255)) for r in group]
        cv2.imwrite(str(HERE / "sheets" / f"{NAME}_{i // 3:02d}.jpg"), np.vstack(group), [cv2.IMWRITE_JPEG_QUALITY, 82])
    print(len(keys), "rows rendered")
