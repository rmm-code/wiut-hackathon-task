"""Loose candidate generation for dev-set review (scratch tool)."""
import json
from pathlib import Path
import math
import sys
from itertools import combinations
import numpy as np
from trk import trajectories, intervals, VEHICLES, SETTINGS, CACHE, load, scene_for
from vision.geometry import crossed, inside, cosine, iou
from vision.rules.signals import signal_color

VIDEOS = ["C3896", "C3897", "C3902", "C3905"]
CFG = SETTINGS.camera()
SIG = {s["id"]: s for s in CFG["signals"]}
SE = CFG["signals"][0]
LANES = {l["id"]: l for l in CFG["lanes"]}
LAMP = tuple(SE["roi"])
SIDE_ROAD = lambda x, y: x < 0.36 and y > 0.66


def lamp_timeline(data):
    out = []
    for rec in data["frames"]:
        out.append((rec["t"], signal_color(rec["crops"][LAMP], min_saturation=100, min_value=50)))
    return out


def lamp_at(timeline, t):
    times = [x[0] for x in timeline]
    k = int(np.searchsorted(times, t))
    k = min(max(k, 0), len(timeline) - 1)
    return timeline[k][1]


def phase_change_before(timeline, t):
    """Time since the lamp last changed to its current (stable) colour."""
    state = lamp_at(timeline, t)
    for tt, c in reversed([x for x in timeline if x[0] <= t]):
        if c != state:
            return state, t - tt
    return state, t


def evasive(rows, t):
    """Speed drop >= 45% or heading change >= 25 degrees within 1.2 s after t."""
    before = [r for r in rows if t - 0.4 <= r[0] <= t]
    after = [r for r in rows if t + 0.4 <= r[0] <= t + 1.2]
    if not before or not after:
        return False
    v0, v1 = before[-1][9], after[-1][9]
    s0, s1 = math.hypot(*v0), math.hypot(*v1)
    if s0 < 1e-6:
        return False
    turn = math.degrees(math.acos(max(-1, min(1, (v0[0] * v1[0] + v0[1] * v1[1]) / max(1e-9, s0 * s1))))) if s1 > 1e-6 else 0
    return s1 < 0.55 * s0 or (s1 > 0.5 * s0 and turn >= 25)


def majority(item, rows=None):
    return item["kind"]


def main(video):
    data, scene, tr = trajectories(video, CFG)
    timeline = lamp_timeline(data)
    cands = []
    add = lambda cls, t0, t1, ids, note: cands.append(
        {"video": video + ".MP4", "hint": cls, "t0": round(t0, 2), "t1": round(t1, 2), "ids": ids, "note": note})
    persons = {i: it for i, it in tr.items() if it["kind"] == "person"}
    vehicles = {i: it for i, it in tr.items() if it["kind"] in VEHICLES and it["kind"] != "bicycle"}
    # 1. jaywalking: pedestrian foot on carriageway outside crossings
    for i, it in persons.items():
        rows = it["rows"]
        riders = sum(r[8] for r in rows) / len(rows)
        if riders > 0.5:
            continue
        flags = []
        for r in rows:
            margin = max(0.004, (r[7][3] - r[7][1]) * 0.06)
            flags.append(scene.on_road((r[1], r[2]), margin) and not scene.near_crossing((r[1], r[2]), margin))
        for t0, t1 in intervals([r[0] for r in rows], flags, gap=1.5, minimum=1.0):
            add("jaywalking", t0, t1, [i], f"person on carriageway outside crossings for {t1 - t0:.1f}s")
    # 2. failure_to_yield: vehicle in a crossing while a person is on it
    ped_on = {}
    for i, it in persons.items():
        for r in it["rows"]:
            c = scene.crossing((r[1], r[2]))
            if c and not r[8]:
                ped_on.setdefault((c, round(r[0], 2)), []).append(i)
    for i, it in vehicles.items():
        rows = it["rows"]
        occ = [(r[0], scene.crossing((r[1], r[2]))) for r in rows]
        for cross in {c for _, c in occ if c}:
            flags = [c == cross for _, c in occ]
            for t0, t1 in intervals([t for t, _ in occ], flags, gap=1.0, minimum=0.2):
                peds = sorted({p for (c, t), ps in ped_on.items() if c == cross and t0 - 0.5 <= t <= t1 + 0.3 for p in ps})
                if peds:
                    add("failure_to_yield", t0, t1, [i] + peds[:4], f"vehicle in {cross} with {len(peds)} pedestrian track(s) on it")
    # 3. red_light / stop_line: stop-line crossings while lamp not green; stationary beyond line on red
    for i, it in vehicles.items():
        rows = it["rows"]
        for sig, direction in [(SE, 1)]:
            fx, fy = sig["front"]
            pts = []
            for r in rows:
                x1, y1, x2, y2 = r[7]
                pts.append((r[0], scene.point((x1 + (x2 - x1) * fx, y1 + (y2 - y1) * fy)), r[6]))
            for (ta, pa, _), (tb, pb, _) in zip(pts, pts[1:]):
                if tb - ta < 0.6 and crossed(pa, pb, sig["stop_line"]):
                    from vision.geometry import line_side
                    if line_side(pb, sig["stop_line"]) * sig["entry_side"] > 0:
                        state, since = phase_change_before(timeline, tb)
                        came = any(inside(p, sig["approach"]) for t, p, _ in pts if tb - 3 <= t < ta + 1e-6)
                        onward = any(inside(p, sig["intersection"]) for t, p, _ in pts if tb < t <= tb + 4)
                        if state != "green" and came and onward:
                            add("red_light", ta, tb + 3, [i], f"{sig['id']}: crossed stop line with lamp {state} ({since:.1f}s into it)")
                        break
            stopped_beyond = [(t, st and inside(p, sig["beyond_line"]) and lamp_at(timeline, t) == "red") for t, p, st in pts]
            for t0, t1 in intervals([t for t, _ in stopped_beyond], [f for _, f in stopped_beyond], gap=1.0, minimum=1.0):
                add("stop_line", t0, t1, [i], f"{sig['id']}: stationary beyond stop line during red")
    # 4. stopped_vehicle: stationary >= 8 s, excluding pure red-phase approach queues
    for i, it in vehicles.items():
        rows = it["rows"]
        flags = [r[6] and scene.on_road((r[1], r[2])) for r in rows]
        for t0, t1 in intervals([r[0] for r in rows], flags, gap=1.0, minimum=8.0):
            seg = [r for r in rows if t0 <= r[0] <= t1]
            in_queue = np.mean([inside(scene.point((r[1], r[2])), SE["approach"]) or inside(scene.point((r[1], r[2])), LANES["nw-approach"]["polygon"]) for r in seg])
            green = np.mean([lamp_at(timeline, r[0]) == "green" for r in seg])
            if in_queue > 0.8 and green < 0.3:
                continue
            p = scene.point((seg[0][1], seg[0][2]))
            add("stopped_vehicle", t0, t1, [i], f"stationary {t1 - t0:.0f}s at ({p[0]:.2f},{p[1]:.2f}); in approach {in_queue:.0%}; green {green:.0%}")
    # 5. wrong_way: sustained motion against the carriageway direction
    for i, it in vehicles.items():
        rows = it["rows"]
        flags = []
        for r in rows:
            p = scene.point((r[1], r[2]))
            lane = next((l for l in CFG["lanes"] if inside(p, l["polygon"])), None)
            v = r[9]
            speed_ok = r[5] > 0.15
            flags.append(bool(lane and speed_ok and cosine(v, lane["vector"]) < -0.5))
        for t0, t1 in intervals([r[0] for r in rows], flags, gap=1.0, minimum=1.0):
            add("wrong_way", t0, t1, [i], "motion opposes carriageway direction")
    # 6. turns: SE right turn into side road, U-turn between carriageways
    A, B = SE["stop_line"]
    for i, it in vehicles.items():
        rows = it["rows"]
        P = [(r[0], scene.point((r[1], r[2]))) for r in rows]
        s_at = None
        for (ta, pa), (tb, pb) in zip(P, P[1:]):
            if crossed(pa, pb, [A, B]) and pb[1] > pa[1]:
                d = np.subtract(B, A)
                m = ((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2)
                s_at = (tb, float(np.dot(np.subtract(m, A), d) / np.dot(d, d)))
                break
        end = P[-1][1]
        if s_at and SIDE_ROAD(*end):
            add("illegal_turn" if s_at[1] > 0.18 else "turn_legal", s_at[0] - 2, P[-1][0], [i],
                f"SE right turn into side road from stop-line position s={s_at[1]:.2f} (curb lane < 0.18)")
        start = P[0][1]
        in_se = inside(start, LANES["se-approach"]["polygon"])
        in_nwd = inside(end, LANES["nw-departure"]["polygon"])
        in_nwa = inside(start, LANES["nw-approach"]["polygon"])
        if (in_se and in_nwd) or (in_nwa and inside(end, LANES["se-approach"]["polygon"])):
            add("illegal_u_turn", P[0][0], P[-1][0], [i], "track starts and ends on opposite carriageways")
    # 7. near_miss: close approach with evasive change
    frames = {}
    for i, it in tr.items():
        for r in it["rows"]:
            frames.setdefault(round(r[0], 2), []).append((i, it["kind"], r))
    seen = {}
    for t, items in sorted(frames.items()):
        for (i, ki, ra), (j, kj, rb) in combinations(items, 2):
            if ki not in VEHICLES and kj not in VEHICLES:
                continue
            if ki == "person" and ra[8] or kj == "person" and rb[8]:
                continue
            ha = ra[7][3] - ra[7][1]; hb = rb[7][3] - rb[7][1]
            scale = (ha + hb) / 2
            pos = (rb[1] - ra[1], rb[2] - ra[2]); vel = (rb[9][0] - ra[9][0], rb[9][1] - ra[9][1])
            sp2 = vel[0] ** 2 + vel[1] ** 2
            if sp2 < (scale * 0.1) ** 2:
                continue
            ttc = -(pos[0] * vel[0] + pos[1] * vel[1]) / sp2
            if not 0 < ttc < 1.5:
                continue
            miss = math.hypot(pos[0] + vel[0] * ttc, pos[1] + vel[1] * ttc)
            if miss < scale * 0.35 and iou(ra[7], rb[7]) < 0.05 and math.hypot(*pos) < scale * 3 \
                    and ra[5] > 0.3 and rb[5] > 0.3 and (evasive(tr[i]["rows"], t) or evasive(tr[j]["rows"], t)):
                key = tuple(sorted((i, j)))
                if key not in seen or t - seen[key] > 3:
                    add("near_miss", t - 1.5, t + 2.5, list(key), f"TTC {ttc:.1f}s, predicted miss {miss / scale:.2f} scale ({ki}/{kj})")
                seen[key] = t
    return cands, timeline


if __name__ == "__main__":
    allc, lamps = [], {}
    for v in VIDEOS:
        c, tl = main(v)
        allc += c
        lamps[v] = tl
        print(v, len(c))
    for k, i in enumerate(allc):
        i["cid"] = f"{i['hint'][:3]}-{k:04d}"
    json.dump(allc, open(Path(__file__).parent / "cands.json", "w"), indent=1)
    json.dump({v: [[round(t, 2), c] for t, c in tl] for v, tl in lamps.items()}, open(Path(__file__).parent / "lamps.json", "w"))
    from collections import Counter
    print(Counter(c["hint"] for c in allc))
