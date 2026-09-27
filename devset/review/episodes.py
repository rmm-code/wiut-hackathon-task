"""Group loose candidates into review episodes and render one contact sheet per episode."""
import json
import sys
from multiprocessing import Pool
from pathlib import Path

SP = Path(__file__).resolve().parent
OUT = SP / "sheets"
GAP = {"jaywalking": 1.0, "failure_to_yield": 0.5, "stopped_vehicle": 2.0, "near_miss": 0.5}


def group(cands):
    eps = []
    by = {}
    for c in cands:
        by.setdefault((c["video"], c["hint"]), []).append(c)
    for (video, hint), items in sorted(by.items()):
        items.sort(key=lambda c: c["t0"])
        cur = None
        for c in items:
            gap = GAP.get(hint, -1)
            if cur and gap >= 0 and c["t0"] <= cur["t1"] + gap and len(cur["ids"]) < 8:
                cur["t1"] = max(cur["t1"], c["t1"])
                cur["ids"] = sorted(set(cur["ids"]) | set(c["ids"]))
                cur["members"].append({k: c[k] for k in ("cid", "t0", "t1", "ids", "note")})
            else:
                cur = {"video": video, "hint": hint, "t0": c["t0"], "t1": c["t1"], "ids": list(c["ids"]),
                       "members": [{k: c[k] for k in ("cid", "t0", "t1", "ids", "note")}]}
                eps.append(cur)
    for k, e in enumerate(eps):
        e["eid"] = f"{e['hint'][:4]}-{e['video'][:5]}-{k:04d}"
        e["sheet"] = "sheets/" + e["eid"] + ".jpg"
    return eps


def render(batch):
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2]))
    import cv2
    from scripts.sheets import Sheet
    video, eps = batch
    sheet = Sheet(video)
    for e in eps:
        if (SP / e["sheet"]).exists():
            continue
        span = e["t1"] - e["t0"]
        count = 6 if span < 6 else 9
        pad = 1.0 if e["hint"] in ("jaywalking", "failure_to_yield", "near_miss", "red_light", "illegal_turn", "turn_legal") else 0.5
        img = sheet.render(max(0, e["t0"] - pad), e["t1"] + pad, e["ids"], count=count, columns=3, tile=600)
        cv2.imwrite(str(SP / e["sheet"]), img, [cv2.IMWRITE_JPEG_QUALITY, 82])
    return len(eps)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    cands = json.load(open(SP / "cands.json"))
    eps = group(cands)
    json.dump(eps, open(SP / "episodes.json", "w"), indent=1)
    from collections import Counter
    print(len(eps), Counter(e["hint"] for e in eps))
    batches = []
    for video in sorted({e["video"] for e in eps}):
        items = [e for e in eps if e["video"] == video]
        for k in range(0, len(items), 25):
            batches.append((video, items[k:k + 25]))
    with Pool(6) as pool:
        print(sum(pool.map(render, batches)), "rendered")
