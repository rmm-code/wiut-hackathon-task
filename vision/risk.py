import math
import time
from itertools import combinations
from .geometry import dot, distance
from .types import VEHICLES


# Raw conflict level mapped to the 0.5 alarm threshold. On the four accident-free samples,
# raw 0.5 gave 2.9 alarms per minute and raw 0.65 gives 0.87. The mapping is monotonic,
# so the ranking (and average precision) is unchanged; only alarms become rarer.
ALARM_RAW = 0.65


def calibrate(raw):
    if raw <= ALARM_RAW:
        return 0.5 * raw / ALARM_RAW
    return 0.5 + 0.5 * (raw - ALARM_RAW) / (1 - ALARM_RAW)


class RiskModel:
    def __init__(self):
        self.value = 0.0
        self.last_t = None

    def step(self, tracks, t, scene):
        peak = 0.0
        eligible = [
            tr
            for tr in tracks
            if t - tr.first >= 0.7 and scene.on_road(tr.observation.foot)
        ]
        for a, b in combinations(eligible, 2):
            if (
                a.observation.kind not in VEHICLES
                and b.observation.kind not in VEHICLES
            ):
                continue
            pa, pb = a.observation.foot, b.observation.foot
            position = (pb[0] - pa[0], pb[1] - pa[1])
            velocity = (b.velocity[0] - a.velocity[0], b.velocity[1] - a.velocity[1])
            speed2 = dot(velocity, velocity)
            scale = (a.observation.height + b.observation.height) / 2
            if speed2 < (scale * 0.08) ** 2 or dot(position, velocity) >= 0:
                continue
            ttc = -dot(position, velocity) / speed2
            if not 0 < ttc <= 5:
                continue
            miss = math.hypot(
                position[0] + velocity[0] * ttc, position[1] + velocity[1] * ttc
            )
            if miss > scale * 0.38 or distance(pa, pb) > scale * 5:
                continue
            spatial = max(0, 1 - miss / (scale * 0.38))
            urgency = 1 - ttc / 6
            confidence = min(a.observation.score, b.observation.score)
            peak = max(peak, spatial * urgency * confidence)
        dt = max(0, t - self.last_t) if self.last_t is not None else 0
        self.value = min(1.0, max(peak, self.value * math.exp(-dt / 0.5)))
        self.last_t = t
        return calibrate(self.value)


class RiskEstimator:
    def reset(self, meta):
        from . import budget
        from .settings import Settings
        from .scene import Scene
        from .tracks import Tracks

        self.meta = dict(meta)
        self.warm = None
        self.frames = int(meta.get("n_frames") or 0)
        self.deadline = (
            budget.deadline(meta.get("video_id", ""), self.frames / float(meta["fps"]))
            if self.frames
            else float("inf")
        )
        self.settings = Settings.load()
        self.scene = Scene(self.settings.camera())
        self.tracks = Tracks()
        self.model = RiskModel()
        self.detector = None
        self.last_score = 0.0
        self.last_timestamp = -1.0
        self.frame_index = 0
        self.stride = max(1, round(float(meta["fps"]) / self.settings.sample_fps))
        self.initialized = False

    def step(self, frame, t_sec):
        from .detector import Detector

        if t_sec < self.last_timestamp:
            raise ValueError("RiskEstimator requires monotonically ordered frames.")
        self.last_timestamp = t_sec
        index = self.frame_index
        self.frame_index += 1
        if index == 50:
            self.warm = time.perf_counter()  # pace excludes model loading at the first frame
        if index >= 150 and index % 25 == 0:
            now = time.perf_counter()
            pace = (now - self.warm) / (index - 50)
            if now + pace * (self.frames - index) > self.deadline:
                raise TimeoutError(
                    "Stopped Part B early to keep this video inside the time budget; Part A events are kept."
                )
        if index % self.stride:
            return self.last_score
        if not self.initialized:
            self.scene.align(frame)
            self.initialized = True
            self.detector = Detector(
                self.settings, float(self.meta["fps"]) / self.stride
            )
        observations = self.detector.step(frame)
        tracks = self.tracks.update(observations, t_sec)
        self.last_score = self.model.step(tracks, t_sec, self.scene)
        return float(self.last_score)
