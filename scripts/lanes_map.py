"""Render the scene map with lane directions for the website's EDA section.

The background is the temporal median of 45 frames of a sample, which removes the traffic. On it:
each mapped carriageway with arrows along its verified direction, the stop line, the solid lane
lines and the crossings, all from config/camera.json.

    python -m scripts.lanes_map samples/C3896.MP4
"""

import argparse
import json
from pathlib import Path

import cv2
import numpy as np

from vision.settings import ROOT

SIZE = (1440, 810)
COLOURS = {"se-approach": (60, 140, 235), "nw-departure": (80, 175, 90), "nw-approach": (200, 120, 60)}


def background(video, frames=45):
    capture = cv2.VideoCapture(str(video))
    total = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    stack = []
    for index in np.linspace(0, total - 1, frames).astype(int):
        capture.set(cv2.CAP_PROP_POS_FRAMES, int(index))
        ok, frame = capture.read()
        if ok:
            stack.append(cv2.resize(frame, SIZE, interpolation=cv2.INTER_AREA))
    capture.release()
    return np.median(np.stack(stack), axis=0).astype(np.uint8)


def pixels(points):
    return np.int32([[x * SIZE[0], y * SIZE[1]] for x, y in points])


def label(image, text, origin, colour):
    font, scale, thickness = cv2.FONT_HERSHEY_SIMPLEX, 0.62, 2
    (width, height), _ = cv2.getTextSize(text, font, scale, thickness)
    x, y = int(origin[0]), int(origin[1])
    cv2.rectangle(image, (x - 6, y - height - 8), (x + width + 6, y + 8), (20, 20, 20), -1)
    cv2.putText(image, text, (x, y), font, scale, colour, thickness, cv2.LINE_AA)


def render(video, config):
    image = background(video)
    overlay = image.copy()
    for lane in config["lanes"]:
        cv2.fillPoly(overlay, [pixels(lane["polygon"])], COLOURS.get(lane["id"], (180, 180, 180)))
    image = cv2.addWeighted(overlay, 0.28, image, 0.72, 0)
    for crossing in config["crossings"]:
        cv2.polylines(image, [pixels(crossing["polygon"])], True, (40, 220, 240), 2, cv2.LINE_AA)
    for line in config["solid_lines"]:
        cv2.polylines(image, [pixels(line["points"])], False, (255, 255, 255), 3, cv2.LINE_AA)
    stop = next((rule["start_line"] for rule in config["turn_rules"] if "start_line" in rule), None)
    if stop:
        cv2.polylines(image, [pixels(stop)], False, (40, 40, 230), 4, cv2.LINE_AA)
    for lane in config["lanes"]:
        polygon = pixels(lane["polygon"]).astype(np.float32)
        colour = COLOURS.get(lane["id"], (180, 180, 180))
        centre = polygon.mean(axis=0)
        direction = np.float32(lane["vector"]) * np.float32(SIZE)
        direction /= np.linalg.norm(direction)
        for offset in (-110, 0, 110):
            start = centre + direction * (offset - 45)
            end = centre + direction * (offset + 45)
            cv2.arrowedLine(image, tuple(int(v) for v in start), tuple(int(v) for v in end), colour, 5, cv2.LINE_AA, tipLength=0.35)
        label(image, f"{lane['id']}: {lane['direction']}", centre + np.float32([-90, -38]), (255, 255, 255))
    return image


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("video", type=Path)
    parser.add_argument("--out", type=Path, default=ROOT / "web/public/images/lanes.jpg")
    args = parser.parse_args()
    config = json.loads((ROOT / "config/camera.json").read_text())
    cv2.imwrite(str(args.out), render(args.video, config), [cv2.IMWRITE_JPEG_QUALITY, 84])
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
