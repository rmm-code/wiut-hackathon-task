"""Build explicit release archives without uploads, secrets, or development caches."""

import argparse
import json
import tarfile
from pathlib import Path
from .setup import digest, ensure_model
from vision.settings import ROOT
from api.samples import SAMPLE_IDS


def pack(destination, name, files):
    target = destination / name
    with tarfile.open(target, "w") as archive:
        for path, relative in files:
            archive.add(path, arcname=relative, recursive=False)
    return {"file": name, "bytes": target.stat().st_size, "sha256": digest(target)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=ROOT / "release")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((ROOT / "weights/manifest.json").read_text())
    weights = []
    for item in manifest["models"]:
        path = ensure_model(item, ROOT / "weights", check_only=True)
        weights.append((path, "weights/" + path.name))
    weights += [
        (ROOT / name, name)
        for name in [
            "weights/manifest.json",
            "weights/README.md",
            "config/models.json",
            "README.md",
        ]
    ]
    samples = []
    for identity in SAMPLE_IDS:
        folder = ROOT / "artifacts" / identity
        record = json.loads((folder / "record.json").read_text())
        for name, expected in record["files"].items():
            path = folder / name
            if digest(path) != expected:
                raise ValueError(f"Archive checksum mismatch: {identity}/{name}")
        for name in [*record["files"], "record.json", "poster.jpg"]:
            samples.append((folder / name, f"artifacts/{identity}/{name}"))
    samples.append((ROOT / "predictions_samples.json", "predictions_samples.json"))
    results = [
        pack(args.out, "weights.tar", weights),
        pack(args.out, "samples.tar", samples),
    ]
    (args.out / "checksums.json").write_text(json.dumps(results, indent=2) + "\n")
    for result in results:
        print(result["file"], round(result["bytes"] / 1e6, 1), "MB", result["sha256"])


if __name__ == "__main__":
    main()
