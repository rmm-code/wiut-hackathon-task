"""Assemble every reviewed verdict into devset/labels.json (official GT format) and devset/notes.json.

Sources, all in this directory:
  results/*.json            reviewer-agent verdicts on the original loose-candidate episodes
  jaywalking/review.json + verdicts.json    manual jaywalking review (C3897, C3902, C3905)
  failure_to_yield/review.json    manual failure-to-yield review, verdicts embedded (all videos)
  manual_final.json         stop_line phases, red_light and illegal_turn (zoom-checked)
  solid_line/verdicts.json  solid_line_crossing (lane-coordinate measurement + 4K zoom)
  stopped_vehicle/verdicts.json   stopped_vehicle review (all rejected)

Jaywalking boundaries for the manual review come from the pedestrian's ground point with no margins
("steps onto the carriageway -> leaves it"), not from the rule under test.
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(HERE))
from trk import trajectories, intervals, SETTINGS  # noqa: E402

META = {
    "C3896.MP4": (340.34, 29.97002997002997),
    "C3897.MP4": (317.8175, 29.97002997002997),
    "C3902.MP4": (317.8175, 29.97002997002997),
    "C3905.MP4": (127.6275, 29.97002997002997),
}
events, notes = defaultdict(list), []
tracks = {}


def load(name):
    path = HERE / name
    return json.loads(path.read_text()) if path.exists() else []


def add(video, label, start, end, source, why, ids=()):
    start, end = max(0.0, float(start)), min(META[video][0], float(end))
    if end - start < 0.3:
        notes.append({"video": video, "label": label, "status": "dropped-short", "start": start, "end": end, "why": why})
        return
    events[video].append([round(start, 2), round(end, 2), label])
    notes.append({"video": video, "label": label, "status": "accepted", "start": round(start, 2), "end": round(end, 2),
                  "ids": [int(i) for i in ids if i is not None], "source": source, "why": why})


def reject(video, label, status, why, ids=(), source=""):
    notes.append({"video": video, "label": label, "status": status, "ids": [int(i) for i in ids if i is not None],
                  "source": source, "why": why})


def on_road_span(video, ids, start, end):
    """Zero-margin interval(s) with the pedestrians' feet on the carriageway outside crossings."""
    if video not in tracks:
        tracks[video] = trajectories(video[:5], SETTINGS.camera())
    _, scene, tr = tracks[video]
    spans = []
    for identity in ids:
        rows = [r for r in tr.get(identity, {"rows": []})["rows"] if start - 3 <= r[0] <= end + 3]
        flags = [scene.on_road((r[1], r[2])) and scene.crossing((r[1], r[2])) is None for r in rows]
        spans += [s for s in intervals([r[0] for r in rows], flags, gap=1.0, minimum=0.3) if s[1] >= start and s[0] <= end]
    if not spans:
        return start, end
    return min(s[0] for s in spans), max(s[1] for s in spans)


def main():
    episodes = {e["eid"]: e for e in load("episodes.json")}
    # 1. Reviewer agents on the original candidate episodes.
    for batch in ["jaywalking_0", "failure_to_yield_1", "near_miss_0", "wrong_way_0"]:
        for item in load(f"results/{batch}.json"):
            episode = episodes[item["eid"]]
            video, label = episode["video"], episode["hint"]
            members = {m["ids"][0]: m for m in episode["members"]}
            for verdict in item.get("verdicts", []):
                ids = [verdict.get("id")]
                if verdict["verdict"] != "yes":
                    reject(video, label, verdict["verdict"], verdict.get("why", ""), ids, "agent:" + batch)
                    continue
                member = members.get(verdict.get("id"), {})
                start = verdict.get("start", member.get("t0", episode["t0"]))
                end = verdict.get("end", member.get("t1", episode["t1"]))
                why = verdict.get("why", "") + (f" [{verdict['tag']}]" if verdict.get("tag") else "")
                add(video, label, start, end, "agent:" + batch, why, ids)
            for extra in item.get("extra", []):
                add(video, extra.get("label", label), extra["start"], extra["end"], "agent-extra:" + batch, extra.get("why", ""))
    # 2. Manual jaywalking review.
    items = load("jaywalking/review.json")
    verdicts = load("jaywalking/verdicts.json")
    for k, item in enumerate(items):
        status, start, end, why = verdicts[f"{k:02d}"]
        video = item["video"]
        if status == "yes":
            start, end = on_road_span(video, item["ids"], item["start"], item["end"])
            add(video, "jaywalking", start, end, "manual:jaywalking", why, item["ids"])
        elif status == "partial":
            add(video, "jaywalking", start, end, "manual:jaywalking", why, item["ids"])
        else:
            reject(video, "jaywalking", status, why, item["ids"], "manual:jaywalking")
    # 3. Manual failure-to-yield review (interval = vehicle traversal of the crossing).
    for item in load("failure_to_yield/review.json"):
        if item["verdict"] == "yes":
            add(item["video"], "failure_to_yield", item["start"], item["end"], "manual:failure_to_yield",
                f"vehicle traverses {item['key'].split(', ')[-1].rstrip(')')} beside a walking pedestrian ({item['source']} detection)",
                item["ids"])
        else:
            reject(item["video"], "failure_to_yield", item["verdict"], f"{item['source']} detection", item["ids"],
                   "manual:failure_to_yield")
    # 4. Zoom-checked signal and turn labels, solid lines, stopped vehicles.
    for item in load("manual_final.json"):
        add(item["video"], item["label"], item["start"], item["end"], "manual:zoom", item["why"], item.get("ids", []))
    for item in load("solid_line/verdicts.json"):
        if item["verdict"] == "yes":
            add(item["video"], "solid_line_crossing", item["start"], item["end"], "manual:solid", item["why"], [item["id"]])
        else:
            reject(item["video"], "solid_line_crossing", item["verdict"], item["why"], [item["id"]], "manual:solid")
    for item in load("stopped_vehicle/verdicts.json"):
        reject(item["video"], "stopped_vehicle", item["verdict"], item["why"], item["ids"], "manual:stopped")

    labels = {}
    for video, (duration, fps) in META.items():
        merged = []
        for start, end, label in sorted(events[video], key=lambda e: (e[2], e[0])):
            if merged and merged[-1][2] == label and start <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], end)
            else:
                merged.append([start, end, label])
        labels[video] = {"duration": duration, "fps": fps, "events": sorted(merged, key=lambda e: (e[0], e[2]))}
    out = REPO / "devset"
    (out / "labels.json").write_text(json.dumps(labels, indent=1) + "\n")
    (out / "notes.json").write_text(json.dumps(notes, indent=1) + "\n")
    from collections import Counter
    counts = Counter(e[2] for v in labels.values() for e in v["events"])
    print("labelled segments:", dict(sorted(counts.items())), "total", sum(counts.values()))
    print("per video:", {v: len(x["events"]) for v, x in labels.items()})
    print("notes:", dict(Counter(n["status"] for n in notes)))


if __name__ == "__main__":
    main()
