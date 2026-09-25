from dataclasses import dataclass, field
from collections import deque

CLASSES = [
    "accident",
    "near_miss",
    "red_light",
    "wrong_way",
    "illegal_u_turn",
    "stopped_vehicle",
    "jaywalking",
    "failure_to_yield",
    "illegal_turn",
    "solid_line_crossing",
    "stop_line",
    "congestion",
    "road_obstacle",
    "fire_smoke",
]
VEHICLES = {"car", "truck", "bus", "motorcycle", "bicycle"}


@dataclass
class Observation:
    id: int
    kind: str
    score: float
    box: tuple[float, float, float, float]

    @property
    def foot(self):
        x1, _, x2, y2 = self.box
        return ((x1 + x2) / 2, y2)

    @property
    def height(self):
        return max(0.005, self.box[3] - self.box[1])


@dataclass
class Track:
    observation: Observation
    first: float
    last: float
    history: deque = field(default_factory=lambda: deque(maxlen=100))
    velocity: tuple[float, float] = (0.0, 0.0)
    previous_speed: float = 0.0
    speed: float = 0.0
    stopped_since: float | None = None
    lane: str | None = None


@dataclass
class Flag:
    label: str
    key: str
    start: float
    confidence: float = 0.5
    lane: str | None = None
    evidence: str = ""
    end: float | None = None


@dataclass
class Event:
    label: str
    start: float
    end: float
    confidence: float
    lane: str | None
    evidence: str

    def tuple(self):
        return [round(self.start, 3), round(self.end, 3), self.label]
