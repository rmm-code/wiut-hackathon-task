"""Render review contact sheets for labeling sample footage.

    python -m scripts.sheets C3905.MP4 12.0 18.5 --ids 41,57 --out sheet.jpg
    python -m scripts.sheets C3905.MP4 0 60 --every 5 --out scan.jpg     # full-frame scan

Tracked boxes come from the dev cache (`python -m scripts.devset cache`); the
highlighted identities are drawn thick and the crop follows them. Scene zones are
projected from reference coordinates with the cached camera alignment.
"""

import argparse
from pathlib import Path
import cv2
import numpy as np
from vision.settings import ROOT, Settings
from scripts.devset import cache_path, load

COLORS = {
    "crossings": (0, 200, 255),
    "islands": (180, 105, 255),
    "stop_line": (0, 0, 255),
    "solid": (255, 255, 255),
}


class Sheet:
    def __init__(self, video):
        self.video = ROOT / "samples" / video if not Path(video).is_file() else Path(video)
        self.data = load(cache_path(self.video))
        self.config = Settings.load().camera()
        matrix = self.data["matrix"]
        self.inverse = np.linalg.inv(np.asarray(matrix)) if matrix is not None else None
        self.times = np.asarray([record["t"] for record in self.data["frames"]])
        self.cap = cv2.VideoCapture(str(self.video))
        self.fps = self.data["meta"]["fps"]

    def project(self, points, w, h):
        pts = np.float32([[[x * 960, y * 540] for x, y in points]])
        if self.inverse is not None:
            pts = cv2.perspectiveTransform(pts, self.inverse)
        return (pts[0] / [960, 540] * [w, h]).astype(np.int32)

    def frame(self, t):
        last = self.data["decoded"] - 1
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, min(last, max(0, int(round(t * self.fps)))))
        ok, image = self.cap.read()
        if not ok:
            raise ValueError(f"Cannot read {self.video.name} at {t:.2f} s")
        return image

    def record(self, t):
        return self.data["frames"][int(np.abs(self.times - t).argmin())]

    def boxes(self, t, ids):
        return {
            identity: box
            for identity, kind, score, box in self.record(t)["obs"]
            if not ids or identity in ids
        }

    def draw(self, image, t, ids, zones=True):
        h, w = image.shape[:2]
        if zones:
            overlay = image.copy()
            for crossing in self.config["crossings"]:
                cv2.polylines(overlay, [self.project(crossing["polygon"], w, h)], True, COLORS["crossings"], 4)
            for island in self.config["islands"]:
                cv2.polylines(overlay, [self.project(island, w, h)], True, COLORS["islands"], 3)
            for signal in self.config.get("signals", []):
                cv2.polylines(overlay, [self.project(signal["stop_line"], w, h)], False, COLORS["stop_line"], 4)
            for line in self.config.get("solid_lines", []):
                cv2.polylines(overlay, [self.project(line["points"], w, h)], False, COLORS["solid"], 4)
            cv2.addWeighted(overlay, 0.55, image, 0.45, 0, image)
        for identity, kind, score, box in self.record(t)["obs"]:
            x1, y1, x2, y2 = (int(v * s) for v, s in zip(box, [w, h, w, h]))
            chosen = identity in ids
            color = (0, 255, 0) if chosen else (200, 200, 200)
            cv2.rectangle(image, (x1, y1), (x2, y2), color, 6 if chosen else 2)
            if chosen or not ids:
                cv2.putText(image, f"{kind[:4]}#{identity}", (x1, max(30, y1 - 10)),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.4, color, 3, cv2.LINE_AA)
        return image

    def region(self, start, end, ids, w, h, margin):
        boxes = [
            box
            for t in np.linspace(start, end, 12)
            for box in self.boxes(t, ids).values()
        ] if ids else []
        if not boxes:
            return 0, 0, w, h
        arr = np.asarray(boxes) * [w, h, w, h]
        x1, y1 = arr[:, 0].min(), arr[:, 1].min()
        x2, y2 = arr[:, 2].max(), arr[:, 3].max()
        size = max(x2 - x1, (y2 - y1) * 16 / 9, 900) * (1 + margin)
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        width, height = min(w, size), min(h, size * 9 / 16)
        left = int(np.clip(cx - width / 2, 0, w - width))
        top = int(np.clip(cy - height / 2, 0, h - height))
        return left, top, int(left + width), int(top + height)

    def lamp(self, image, roi, size=110):
        """Enlarged crop of a signal head, located through the camera alignment."""
        h, w = image.shape[:2]
        corners = self.project([roi[:2], [roi[2], roi[1]], roi[2:], [roi[0], roi[3]]], w, h)
        x1, y1 = corners.min(axis=0)
        x2, y2 = corners.max(axis=0)
        crop = image[max(0, y1):y2, max(0, x1):x2]
        return cv2.resize(crop, (int(size * crop.shape[1] / crop.shape[0]), size), interpolation=cv2.INTER_CUBIC)

    def render(self, start, end, ids=(), count=6, columns=3, tile=640, margin=0.6, times=None, zones=True, lamp=None):
        times = list(times) if times is not None else list(np.linspace(start, end, count))
        first = self.frame(times[0])
        h, w = first.shape[:2]
        left, top, right, bottom = self.region(min(times), max(times), set(ids), w, h, margin)
        tiles = []
        for t in times:
            raw = self.frame(t)
            inset = self.lamp(raw, lamp) if lamp else None
            image = self.draw(raw, t, set(ids), zones)
            crop = image[top:bottom, left:right]
            crop = cv2.resize(crop, (tile, int(tile * crop.shape[0] / crop.shape[1])), interpolation=cv2.INTER_AREA)
            cv2.rectangle(crop, (0, 0), (150, 34), (0, 0, 0), -1)
            cv2.putText(crop, f"{t:7.2f}s", (4, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
            if inset is not None:
                crop[-inset.shape[0]:, -inset.shape[1]:] = inset
            tiles.append(crop)
        while len(tiles) % columns:
            tiles.append(np.full_like(tiles[0], 255))
        rows = [np.hstack(tiles[i:i + columns]) for i in range(0, len(tiles), columns)]
        return np.vstack(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("video")
    parser.add_argument("start", type=float)
    parser.add_argument("end", type=float)
    parser.add_argument("--ids", default="")
    parser.add_argument("--count", type=int, default=6)
    parser.add_argument("--every", type=float, help="full-frame scan interval in seconds")
    parser.add_argument("--columns", type=int, default=3)
    parser.add_argument("--tile", type=int, default=640)
    parser.add_argument("--no-zones", action="store_true")
    parser.add_argument("--lamp", action="store_true", help="inset the first configured signal head")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    sheet = Sheet(args.video)
    ids = [int(v) for v in args.ids.split(",") if v]
    times = np.arange(args.start, args.end + 1e-6, args.every) if args.every else None
    lamp = sheet.config["signals"][0]["roi"] if args.lamp and sheet.config.get("signals") else None
    image = sheet.render(args.start, args.end, ids, args.count, args.columns, args.tile,
                         times=times, zones=not args.no_zones, lamp=lamp)
    cv2.imwrite(str(args.out), image, [cv2.IMWRITE_JPEG_QUALITY, 85])
    print(args.out, image.shape[1], "x", image.shape[0])


if __name__ == "__main__":
    main()
