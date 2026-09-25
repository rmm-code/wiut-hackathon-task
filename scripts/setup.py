"""Explicit, checksum-verified pre-run weight download; never called by inference."""

import argparse
import hashlib
import json
import shutil
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def ensure_model(item, root, check_only=False):
    path = root / item["file"]
    if path.parent != root or path.name != item["file"]:
        raise ValueError("Checkpoint names must be plain filenames.")
    if path.is_file() and digest(path) == item["sha256"]:
        return path
    if check_only:
        raise ValueError(f"Missing or invalid checkpoint: {path.name}")
    root.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=root, suffix=".download", delete=False
    ) as temporary:
        partial = Path(temporary.name)
    try:
        with (
            urllib.request.urlopen(item["url"], timeout=60) as source,
            partial.open("wb") as target,
        ):
            shutil.copyfileobj(source, target, length=1024 * 1024)
        if digest(partial) != item["sha256"]:
            raise ValueError(
                f"Checksum mismatch for {path.name}; existing weights were not replaced."
            )
        partial.replace(path)
    finally:
        partial.unlink(missing_ok=True)
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check", action="store_true", help="Verify offline without downloading."
    )
    args = parser.parse_args()
    manifest = json.loads((ROOT / "weights/manifest.json").read_text())
    total = 0
    for item in manifest["models"]:
        path = ensure_model(item, ROOT / "weights", args.check)
        total += path.stat().st_size
        print(f"Verified {path.name}")
    if total > 5_000_000_000:
        raise ValueError("Checkpoint total exceeds the 5 GB competition limit.")
    print(f"Local checkpoints: {total / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
