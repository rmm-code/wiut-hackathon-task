import random
from types import SimpleNamespace
import numpy as np
from .settings import Settings, device_name
from .types import Observation

ALIASES = {"light-vehicle": "car", "heavy-vehicle": "truck", "pedestrian": "person"}
ACCEPTED = {
    "car",
    "truck",
    "bus",
    "person",
    "bicycle",
    "motorcycle",
    "dog",
    "cat",
    "horse",
    "cow",
    "sheep",
    "smoke",
    "fire",
    "debris",
}


class Detector:
    def __init__(self, settings: Settings, fps: float):
        import torch
        from .weights import load_model
        from ultralytics.utils import SETTINGS
        from ultralytics.trackers.byte_tracker import BYTETracker, STrack

        if not settings.weights.is_file():
            raise FileNotFoundError(
                f"Local model weights are missing: {settings.weights.name}. Run scripts/setup.py first."
            )
        if SETTINGS.get("sync"):
            SETTINGS.update({"sync": False})
        random.seed(42)
        np.random.seed(42)
        torch.manual_seed(42)
        torch.set_num_threads(4)
        torch.backends.cudnn.benchmark = False
        torch.backends.cudnn.deterministic = True
        self.device = device_name(settings.device)
        self.settings = settings
        self.model = load_model(settings.weights)
        self.names = {
            int(k): ALIASES.get(str(v).lower(), str(v).lower())
            for k, v in self.model.names.items()
        }
        self.ids = [k for k, name in self.names.items() if name in ACCEPTED]
        counter = 0

        class LocalTrack(STrack):
            @staticmethod
            def next_id():
                nonlocal counter
                counter += 1
                return counter

        class LocalTracker(BYTETracker):
            track_class = LocalTrack

        args = SimpleNamespace(
            track_high_thresh=0.3,
            track_low_thresh=0.1,
            new_track_thresh=0.3,
            track_buffer=max(1, round(fps * 1.2)),
            match_thresh=0.8,
            fuse_score=True,
        )
        self.tracker = LocalTracker(args)

    def step(self, frame):
        result = self.model.predict(
            frame,
            device=self.device,
            imgsz=self.settings.image_size,
            conf=0.1,
            classes=self.ids,
            verbose=False,
            save=False,
        )[0]
        boxes = result.boxes.cpu().numpy()
        tracked = self.tracker.update(boxes, frame)
        h, w = frame.shape[:2]
        observations = []
        for row in tracked:
            x1, y1, x2, y2, identity, score, category = row[:7]
            if score < self.settings.confidence:
                continue
            box = tuple(
                float(np.clip(v, 0, 1)) for v in (x1 / w, y1 / h, x2 / w, y2 / h)
            )
            observations.append(
                Observation(int(identity), self.names[int(category)], float(score), box)
            )
        return observations
