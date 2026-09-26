from dataclasses import dataclass
from .types import Event


@dataclass
class Pending:
    flag: object
    first: float
    last: float


class Segments:
    # Shortest observed interval kept per class, in seconds; stopped_vehicle has its own 10 s rule.
    minimum = {"jaywalking": 0.5, "wrong_way": 0.5, "road_obstacle": 0.5, "congestion": 0.5}
    default_minimum = 0.12

    def __init__(self):
        self.pending = {}
        self.completed = []

    def update(self, flags, t):
        seen = set()
        for flag in flags:
            key = (flag.label, flag.key)
            seen.add(key)
            if key not in self.pending:
                self.pending[key] = Pending(flag, t, t)
            pending = self.pending[key]
            pending.last = t
            pending.flag.start = min(flag.start, pending.flag.start)
            pending.flag.confidence = max(flag.confidence, pending.flag.confidence)
            if flag.end is not None:
                pending.flag.end = flag.end
                self._close(key, flag.end)
        for key in list(self.pending):
            pending = self.pending[key]
            if key not in seen and t - pending.last > 0.5:
                self._close(key, pending.last)

    def _close(self, key, end):
        pending = self.pending.pop(key)
        flag = pending.flag
        minimum = self.minimum.get(flag.label, self.default_minimum)
        observed = end - (flag.start if flag.end is not None else pending.first)
        if observed < minimum and flag.label != "stopped_vehicle":
            return
        if end > flag.start:
            self.completed.append(
                Event(
                    flag.label,
                    flag.start,
                    end,
                    flag.confidence,
                    flag.lane,
                    flag.evidence,
                    flag.key,
                )
            )

    def finish(self, duration):
        for key in list(self.pending):
            pending = self.pending[key]
            self._close(
                key, duration if duration - pending.last < 0.6 else pending.last
            )
        output = []
        for event in sorted(self.completed, key=lambda e: (e.label, e.start)):
            event.start = max(0.0, event.start)
            event.end = min(duration, event.end)
            if event.end <= event.start:
                continue
            if (
                output
                and output[-1].label == event.label
                and event.start <= output[-1].end
            ):
                output[-1].end = max(output[-1].end, event.end)
                output[-1].confidence = max(output[-1].confidence, event.confidence)
                output[-1].key = "|".join(filter(None, [output[-1].key, event.key]))
            else:
                output.append(event)
        return sorted(output, key=lambda e: (e.start, e.label))
