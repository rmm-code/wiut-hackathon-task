"""Publish completed organizer outputs to durable, read-only sample storage."""

import argparse
import hashlib
import json
import shutil
import tempfile
from pathlib import Path
import cv2
from vision.settings import ROOT
from api.samples import SAMPLE_IDS

FILES = [
    "analysis.json",
    "annotated.mp4",
    "occupancy.jpg",
    "motion.jpg",
    "trajectories.jpg",
]


def publish(identity, source, destination):
    analysis = json.loads((source / "analysis.json").read_text())
    meta = analysis["meta"]
    if (
        meta["decoded_frames"] != meta["n_frames"]
        or len(analysis["risk"]) != meta["n_frames"]
    ):
        raise ValueError("Only complete analyses can be archived.")
    for name in FILES:
        if not (source / name).is_file():
            raise ValueError(f"Missing artifact: {name}")
    destination.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=identity + "-", dir=destination))
    try:
        checksums = {}
        for name in FILES:
            shutil.copy2(source / name, staging / name)
            with (staging / name).open("rb") as stream:
                checksums[name] = hashlib.file_digest(stream, "sha256").hexdigest()
        cap = cv2.VideoCapture(str(staging / "annotated.mp4"))
        ok, image = cap.read()
        cap.release()
        if not ok:
            raise ValueError("Annotated video cannot be decoded.")
        cv2.imwrite(str(staging / "poster.jpg"), image)
        record = {
            "sample": SAMPLE_IDS[identity],
            "files": checksums,
            "origin": "organizer sample",
            "retention": "permanent",
            "engine": analysis["engine"],
            "reviewed_ground_truth": False,
        }
        (staging / "record.json").write_text(json.dumps(record, indent=2) + "\n")
        target = destination / identity
        if target.exists():
            # Replace only the explicitly managed files; preserve the directory identity.
            for file in staging.iterdir():
                file.replace(target / file.name)
        else:
            staging.rename(target)
        print(
            f"Archived {SAMPLE_IDS[identity]}: {len(analysis['events'])} candidate events"
        )
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "output")
    parser.add_argument("--archive", type=Path, default=ROOT / "artifacts")
    args = parser.parse_args()
    for identity, name in SAMPLE_IDS.items():
        publish(identity, args.output / Path(name).stem, args.archive)


if __name__ == "__main__":
    main()
