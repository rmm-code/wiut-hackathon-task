"""Download only the four organizer-supplied sample videos."""

import argparse
import hashlib
import json
import gdown
from vision.media import metadata
from vision.settings import ROOT

FILES = {
    "C3896.MP4": "1kR9jODA2Wotw4gwkvpRKdqFADNJNc1nS",
    "C3897.MP4": "1hp8DYeqtYHSwfM6qAo9FPSRHlpMFrIN_",
    "C3902.MP4": "10cHEReCWzO3u-Vk1CnNgHAx6egGy5MwJ",
    "C3905.MP4": "1aJ-QsAZVYJtLKHiRvKKeBq1D3GWNobRd",
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("names", nargs="*", metavar="VIDEO")
    args = parser.parse_args()
    if any(name not in FILES for name in args.names):
        parser.error("Choose only organizer sample names: " + ", ".join(FILES))
    for name in args.names or FILES:
        path = ROOT / "samples" / name
        path.parent.mkdir(exist_ok=True)
        if not path.is_file():
            temporary = path.with_suffix(".download")
            gdown.download(id=FILES[name], output=str(temporary), resume=True)
            temporary.replace(path)
        info = metadata(path)
        digest = hashlib.file_digest(path.open("rb"), "sha256").hexdigest()
        info.update(
            sha256=digest, source=f"https://drive.google.com/file/d/{FILES[name]}/view"
        )
        path.with_suffix(path.suffix + ".ready").write_text(json.dumps(info, indent=2))
        print(
            f"Ready: {name}, {info['duration']:.2f}s, {info['width']}x{info['height']}"
        )


if __name__ == "__main__":
    main()
