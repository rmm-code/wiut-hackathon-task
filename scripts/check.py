"""Read-only submission preflight. Missing release inputs are explicit blockers."""

import hashlib
import json
from pathlib import Path
from vision.types import CLASSES

ROOT = Path(__file__).resolve().parents[1]


def inspect():
    checks = []

    def add(name, passed, detail):
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    hashes = json.loads((ROOT / "research/starter-sha256.json").read_text())
    for name in ["run_submission.py", "evaluate.py"]:
        add(
            name,
            hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == hashes[name],
            "Must match organizer original",
        )
    manifest = json.loads((ROOT / "weights/manifest.json").read_text())
    total = 0
    for item in manifest["models"]:
        path = ROOT / "weights" / item["file"]
        valid = (
            path.is_file()
            and hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]
        )
        total += path.stat().st_size if path.exists() else 0
        add(item["file"], valid, "Pinned local checkpoint SHA-256")
    add("Weight budget", 0 < total <= 5_000_000_000, f"{total / 1e6:.1f} MB / 5000 MB")
    import solution

    add(
        "Root interface",
        solution.CLASSES == CLASSES
        and callable(solution.detect_events)
        and hasattr(solution.RiskEstimator, "step"),
        "Exact competition contract",
    )
    predictions = ROOT / "predictions_samples.json"
    videos = (
        json.loads(predictions.read_text()).get("videos", {})
        if predictions.exists()
        else {}
    )
    for name in ["C3896.MP4", "C3897.MP4", "C3902.MP4", "C3905.MP4"]:
        add(
            name,
            (ROOT / "samples" / (name + ".ready")).exists() and name in videos,
            "Local sample and official predictions required",
        )
    release = json.loads((ROOT / "config/release.json").read_text())
    for key in ["website", "repository", "tag", "weights_url", "predictions_url"]:
        add(
            key,
            release.get(key),
            "Provide a verified public release target"
            if key != "tag"
            else "Provide the release tag",
        )
    team = release.get("team", [])
    add(
        "Team",
        len(team) == 3
        and all(all(member.get(k) for k in ["name", "role", "url"]) for member in team),
        "Three real members with roles and profile links",
    )
    add(
        "Target runtime",
        release.get("nvidia_benchmark_verified") is True,
        "Measure combined A+B on the intended NVIDIA environment",
    )
    return checks


def main():
    checks = inspect()
    for item in checks:
        print(
            f"{'PASS' if item['passed'] else 'MISSING'}: {item['name']} — {item['detail']}"
        )
    missing = sum(not item["passed"] for item in checks)
    print(
        f"\n{missing} incomplete checks. This preflight does not measure accuracy or verify public URL availability."
    )
    raise SystemExit(1 if missing else 0)


if __name__ == "__main__":
    main()
