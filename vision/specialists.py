from dataclasses import dataclass
from .geometry import iou
from .settings import ROOT, device_name
from .types import Event, VEHICLES
from .weights import load_model


@dataclass
class Incident:
    label: str
    box: tuple
    start: float
    last: float
    score: float
    hits: int = 1
    confirmed: bool = False
    stopped_since: float | None = None
    settled: bool = False


class Specialists:
    """Part A appearance evidence with temporal confirmation; never used by Part B."""

    def __init__(self, settings, scene, load=True):
        self.scene = scene
        self.device = device_name(settings.device) if load else "cpu"
        self.models = []
        self.active = []
        self.completed = []
        self.resolved = []
        self.next_time = 0.0
        for item in scene.config.get("specialists", []):
            if item.get("enabled"):
                model = load_model(ROOT / item["weights"]) if load else None
                self.models.append((item, model))

    @property
    def labels(self):
        return {label for item, _ in self.models for label in item["classes"].values()}

    def detect(self, frame, floor=None):
        """Road-gated specialist detections; `floor` lowers thresholds for caching."""
        found = []
        h, w = frame.shape[:2]
        for item, model in self.models:
            result = model.predict(
                frame,
                device=self.device,
                imgsz=640,
                conf=item["confidence"] if floor is None else floor,
                verbose=False,
            )[0]
            for detection in result.boxes.cpu().numpy():
                label = item["classes"].get(
                    str(model.names[int(detection.cls[0])]).lower()
                )
                if not label:
                    continue
                x1, y1, x2, y2 = map(float, detection.xyxy[0])
                box = (x1 / w, y1 / h, x2 / w, y2 / h)
                if self._on_road(box):
                    found.append((label, box, float(detection.conf[0])))
        return found

    def due(self, t):
        return self.scene.matched and t + 1e-6 >= self.next_time

    def _on_road(self, box):
        x1, y1, x2, y2 = box
        return any(
            self.scene.on_road(point)
            for point in [
                ((x1 + x2) / 2, y2),
                ((x1 + x2) / 2, (y1 + y2) / 2),
                (x1, y2),
                (x2, y2),
            ]
        )

    def step(self, frame, tracks, t):
        if self.due(t):
            self.update(self.detect(frame), tracks, t)

    def update(self, found, tracks, t):
        self.next_time = t + 1.0
        updated = set()
        for label, box, score in found:
            previous = next(
                (
                    item
                    for item in self.resolved
                    if item.label == label and iou(item.box, box) >= 0.1
                ),
                None,
            )
            if previous:
                previous.last = t
                continue
            choices = [
                (iou(box, incident.box), i)
                for i, incident in enumerate(self.active)
                if incident.label == label and i not in updated
            ]
            match = max(choices, default=(0, -1))
            if match[0] >= 0.1:
                index = match[1]
                incident = self.active[index]
                incident.box, incident.last = box, t
                incident.score = max(incident.score, score)
                incident.hits += 1
            else:
                self.active.append(Incident(label, box, t, t, score))
                index = len(self.active) - 1
                incident = self.active[index]
            updated.add(index)
            incident.confirmed = incident.hits >= 2
        keep = []
        for incident in self.active:
            end = None
            if incident.label == "accident" and incident.confirmed:
                participants = [
                    tr
                    for tr in tracks
                    if tr.observation.kind in VEHICLES
                    and iou(tr.observation.box, incident.box) > 0.05
                ]
                stopped = participants and all(
                    tr.stopped_since is not None for tr in participants
                )
                if stopped:
                    incident.stopped_since = (
                        incident.stopped_since
                        if incident.stopped_since is not None
                        else t
                    )
                    if t - incident.stopped_since >= 1:
                        incident.settled = True
                        end = incident.stopped_since
                else:
                    incident.stopped_since = None
            if t - incident.last > 2.1:
                end = incident.last
            if end is not None:
                self._close(incident, end)
                if incident.label == "accident" and incident.confirmed:
                    self.resolved.append(incident)
            else:
                keep.append(incident)
        self.active = keep
        self.resolved = [item for item in self.resolved if t - item.last < 3]

    def _close(self, incident, end):
        # A collision ends with its participants at rest; overlapping vehicles that
        # drive on (perspective overlap, dense traffic) are not accidents.
        settled = incident.label != "accident" or incident.settled
        if incident.confirmed and settled and end > incident.start:
            self.completed.append(
                Event(
                    incident.label,
                    incident.start,
                    end,
                    incident.score,
                    None,
                    "Specialist appearance detection confirmed across frames; boundary accuracy requires review.",
                )
            )

    def finish(self, duration):
        for incident in self.active:
            self._close(
                incident, duration if duration - incident.last < 2.1 else incident.last
            )
        self.active.clear()
        return self.completed
