from collections import Counter, defaultdict
import cv2
import numpy as np


class Eda:
    def __init__(self, scene, interval):
        self.scene, self.interval = scene, interval
        self.background = scene.reference
        self.occupancy = np.zeros((45, 80), np.float32)
        self.motion = np.zeros_like(self.occupancy)
        self.paths = defaultdict(list)
        self.counts = []
        self.next_count = 0.0

    def update(self, tracks, t):
        counts = Counter()
        for track in tracks:
            obs = track.observation
            x, y = self.scene.point(obs.foot) if self.scene.matched else obs.foot
            if not 0 <= x <= 1 or not 0 <= y <= 1:
                continue
            row, col = min(44, int(y * 45)), min(79, int(x * 80))
            self.occupancy[row, col] += self.interval
            self.motion[row, col] += track.speed * self.interval
            counts[obs.kind] += 1
            points = self.paths[obs.id]
            if (not points or t - points[-1][0] >= 0.5) and len(points) < 1200:
                points.append([round(t, 3), round(x, 4), round(y, 4), obs.kind])
        if t >= self.next_count:
            self.counts.append(
                {
                    "time": round(t, 2),
                    "objects": dict(counts),
                    "total": sum(counts.values()),
                }
            )
            self.next_count = t + 1

    def finish(self, output=None):
        result = {
            "counts": self.counts,
            "trajectories": dict(self.paths),
            "occupancy": self.occupancy.round(3).tolist(),
            "motion": self.motion.round(5).tolist(),
            "units": {
                "counts": "Visible tracked objects per sampled second",
                "occupancy": "Tracked ground-point occupancy in seconds",
                "motion": "Image-space tracked displacement; not physical speed",
            },
        }
        if output:
            base = cv2.resize(self.background, (1280, 720))
            for name, values in [
                ("occupancy", self.occupancy),
                ("motion", self.motion),
            ]:
                normalized = np.log1p(values)
                normalized = np.uint8(
                    normalized / max(float(normalized.max()), 1e-9) * 255
                )
                heat = cv2.applyColorMap(
                    cv2.resize(normalized, (1280, 720)), cv2.COLORMAP_TURBO
                )
                alpha = cv2.resize(normalized, (1280, 720)).astype(float) / 255 * 0.65
                image = np.uint8(
                    base * (1 - alpha[:, :, None]) + heat * alpha[:, :, None]
                )
                cv2.imwrite(str(output / f"{name}.jpg"), image)
            image = base.copy()
            for identity, points in self.paths.items():
                if len(points) < 3:
                    continue
                color = (
                    100 + (identity * 37) % 130,
                    100 + (identity * 61) % 130,
                    100 + (identity * 89) % 130,
                )
                poly = np.int32([[p[1] * 1280, p[2] * 720] for p in points])
                cv2.polylines(image, [poly], False, color, 1, cv2.LINE_AA)
            cv2.imwrite(str(output / "trajectories.jpg"), image)
        return result
