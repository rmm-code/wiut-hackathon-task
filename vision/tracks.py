import math
import numpy as np
from .types import Track


class Tracks:
    def __init__(self):
        self.active = {}

    def update(self, observations, t):
        visible = []
        for observation in observations:
            track = self.active.get(observation.id)
            if track is None or t - track.last > 1.3:
                track = Track(observation, t, t)
                self.active[observation.id] = track
            track.observation = observation
            track.last = t
            track.history.append((t, *observation.foot))
            recent = np.asarray([p for p in track.history if t - p[0] <= 0.8])
            track.previous_speed = track.speed
            if len(recent) >= 3 and recent[-1, 0] - recent[0, 0] >= 0.2:
                dt = recent[:, 0] - recent[:, 0].mean()
                velocity = (
                    dt[:, None] * (recent[:, 1:] - recent[:, 1:].mean(axis=0))
                ).sum(axis=0) / max(float((dt * dt).sum()), 1e-9)
                track.velocity = tuple(map(float, velocity))
                track.speed = math.hypot(*track.velocity)
            relative_speed = track.speed / observation.height
            if len(recent) >= 3 and relative_speed < 0.055:
                if track.stopped_since is None:
                    track.stopped_since = float(recent[0, 0])
            else:
                track.stopped_since = None
            visible.append(track)
        for identity in list(self.active):
            if t - self.active[identity].last > 1.3:
                del self.active[identity]
        return visible
