"""Explicit pre-run weight download; never called during inference."""

import hashlib
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    manifest = json.loads((ROOT / "weights" / "manifest.json").read_text())
    for item in manifest["models"]:
        path = ROOT / "weights" / item["file"]
        if not path.is_file():
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_suffix(".download")
            urllib.request.urlretrieve(item["url"], temporary)
            temporary.replace(path)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != item["sha256"]:
            raise RuntimeError(f"Checksum mismatch for {path.name}.")
        print(f"Verified {path.name}")


if __name__ == "__main__":
    main()
