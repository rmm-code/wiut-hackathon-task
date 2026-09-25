import cv2
import numpy as np
from .geometry import inside
from .settings import ROOT


class Scene:
    def __init__(self, config):
        self.config = config
        self.matched = False
        self.matches = 0
        self.matrix = None
        self.reference = cv2.imread(str(ROOT / config["reference"]))

    def align(self, frame):
        self.matched, self.matrix, self.matches = False, None, 0
        if self.reference is None:
            return False
        # Retry at the reference's native resolution without relaxing geometry checks.
        for size in [(960, 540), (640, 360)]:
            matrix, matches = self._alignment(frame, size)
            self.matches = matches
            if matrix is not None:
                scale = np.diag([960 / size[0], 540 / size[1], 1.0])
                self.matrix = scale @ matrix @ np.linalg.inv(scale)
                self.matched = True
                return True
        return False

    def _alignment(self, frame, size):
        cv2.setRNGSeed(42)
        image = cv2.resize(frame, size, interpolation=cv2.INTER_AREA)
        reference = cv2.resize(self.reference, size, interpolation=cv2.INTER_CUBIC)
        features = cv2.SIFT_create(nfeatures=3500, contrastThreshold=0.02)
        contrast = cv2.createCLAHE(2, (8, 8))
        kp1, d1 = features.detectAndCompute(
            contrast.apply(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)), None
        )
        kp2, d2 = features.detectAndCompute(
            contrast.apply(cv2.cvtColor(reference, cv2.COLOR_BGR2GRAY)), None
        )
        if d1 is None or d2 is None:
            return None, 0
        pairs = cv2.BFMatcher().knnMatch(d1, d2, k=2)
        good = [
            m
            for pair in pairs
            if len(pair) == 2
            for m, n in [pair]
            if m.distance < 0.75 * n.distance
        ]
        if len(good) < 18:
            return None, 0
        source = np.float32([kp1[m.queryIdx].pt for m in good])
        target = np.float32([kp2[m.trainIdx].pt for m in good])
        matrix, mask = cv2.findHomography(source, target, cv2.RANSAC, 4)
        if matrix is None or mask is None:
            return None, 0
        matches = int(mask.sum())
        width, height = size
        corners = np.float32([[[0, 0], [width, 0], [width, height], [0, height]]])
        projected = cv2.perspectiveTransform(corners, matrix)[0]
        area = abs(cv2.contourArea(projected)) / (width * height)
        spread = cv2.contourArea(cv2.convexHull(target[mask.ravel().astype(bool)])) / (
            width * height
        )
        valid = (
            matches >= 16
            and float(mask.mean()) >= 0.4
            and 0.65 < area < 1.5
            and spread > 0.08
        )
        return (matrix if valid else None), matches

    def point(self, point):
        if self.matrix is None:
            return point
        xy = np.float32([[[point[0] * 960, point[1] * 540]]])
        p = cv2.perspectiveTransform(xy, self.matrix)[0, 0]
        return float(p[0] / 960), float(p[1] / 540)

    def on_road(self, point, margin=0.0):
        p = self.point(point)
        if not self.matched:
            return False
        road_distance = cv2.pointPolygonTest(
            np.asarray(self.config["road"], np.float32), p, True
        )
        islands = [
            cv2.pointPolygonTest(np.asarray(poly, np.float32), p, True)
            for poly in self.config["islands"]
        ]
        return road_distance > margin and not any(value >= -margin for value in islands)

    def crossing(self, point):
        p = self.point(point)
        return next(
            (
                item["id"]
                for item in self.config["crossings"]
                if inside(p, item["polygon"])
            ),
            None,
        )

    def near_crossing(self, point, margin):
        p = self.point(point)
        return any(
            cv2.pointPolygonTest(np.asarray(item["polygon"], np.float32), p, True)
            >= -margin
            for item in self.config["crossings"]
        )

    def lane(self, point):
        p = self.point(point)
        return next(
            (item for item in self.config["lanes"] if inside(p, item["polygon"])), None
        )

    def queue_zone(self, point):
        return any(
            inside(self.point(point), poly)
            for poly in self.config.get("queue_zones", [])
        )

    def summary(self):
        return {
            "id": self.config["id"],
            "matched": self.matched,
            "inliers": self.matches,
            "calibration": self.config["status"],
        }

    def crop(self, frame, roi):
        h, w = frame.shape[:2]
        x1, y1, x2, y2 = roi
        points = np.float32(
            [
                [
                    [x1 * 960, y1 * 540],
                    [x2 * 960, y1 * 540],
                    [x2 * 960, y2 * 540],
                    [x1 * 960, y2 * 540],
                ]
            ]
        )
        if self.matrix is not None:
            points = cv2.perspectiveTransform(points, np.linalg.inv(self.matrix))
        points = points[0] / [960, 540] * [w, h]
        lower = np.floor(points.min(axis=0)).astype(int)
        upper = np.ceil(points.max(axis=0)).astype(int)
        return frame[
            max(0, lower[1]) : min(h, upper[1]), max(0, lower[0]) : min(w, upper[0])
        ]
