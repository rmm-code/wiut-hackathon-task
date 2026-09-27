import json
import math
import time
from collections import Counter, defaultdict
from pathlib import Path
import cv2
from .coverage import coverage
from .detector import Detector
from .media import FrameReader, metadata, VideoWriter
from .risk import RiskModel
from .rules import Rules
from .scene import Scene
from .segments import Segments
from .settings import Settings
from .tracks import Tracks
from .types import VEHICLES
from .specialists import Specialists
from .eda import Eda


def write_json(path, data):
    path = Path(path)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, allow_nan=False, separators=(",", ":")))
    temp.replace(path)


def analyze(
    path, settings=None, output=None, progress=None, cancelled=None, time_limit=None
):
    settings = settings or Settings.load()
    progress = progress or (lambda **kw: None)
    cancelled = cancelled or (lambda: False)
    started = time.perf_counter()
    meta = metadata(path)
    stride = max(1, round(meta["fps"] / settings.sample_fps))
    progress(
        stage="Preparing model",
        progress=0.0,
        processed_frames=0,
        total_frames=meta["n_frames"],
    )
    detector = Detector(settings, meta["fps"] / stride)
    scene = Scene(settings.camera())
    tracks, rules, segments, risk_model = (
        Tracks(),
        Rules(scene),
        Segments(),
        RiskModel(),
    )
    specialists = Specialists(settings, scene)
    eda = Eda(scene, stride / meta["fps"])
    writer = None
    source_writer = None
    output = Path(output) if output else None
    if output:
        output.mkdir(parents=True, exist_ok=True)
        writer = VideoWriter(output / "annotated.mp4", meta)
        source_writer = VideoWriter(output / "source.mp4", meta, annotate=False)
    identities, buckets, curve, first_seen = {}, {}, [], {}
    class_votes = defaultdict(Counter)
    observations, flags, index, score = [], [], 0, 0.0
    brightness = []
    success = False
    # Rendering needs every frame; analysis only every stride-th one.
    reader = FrameReader(path, (lambda i: True) if output else (lambda i: i % stride == 0))
    try:
        for position, frame in reader:
            if cancelled():
                raise InterruptedError("Analysis was cancelled.")
            if time_limit and time.perf_counter() - started > time_limit:
                raise TimeoutError("Analysis exceeded its runtime limit.")
            assert position == index
            t = index / meta["fps"]
            if index == 0:
                scene.align(frame)
                eda.background = scene.reference if scene.matched else frame.copy()
            if index % stride == 0:
                observations = detector.step(frame)
                active = tracks.update(observations, t)
                flags = rules.step(active, t, frame)
                specialists.step(frame, active, t)
                eda.update(active, t)
                segments.update(flags, t)
                score = risk_model.step(active, t, scene)
                for obs in observations:
                    identities[obs.id] = obs.kind
                    class_votes[obs.id][obs.kind] += 1
                    if obs.id not in first_seen:
                        first_seen[obs.id] = t
                if (
                    len(brightness) < 300
                    and index % max(stride, int(meta["fps"])) < stride
                ):
                    brightness.append(
                        float(
                            cv2.cvtColor(
                                cv2.resize(frame, (160, 90)), cv2.COLOR_BGR2GRAY
                            ).mean()
                        )
                    )
                progress(
                    stage="Detecting and tracking",
                    progress=min(0.98, index / meta["n_frames"]),
                    processed_frames=index,
                    total_frames=meta["n_frames"],
                    objects=len(identities),
                )
            curve.append([round(t, 4), round(float(score), 4)])
            if writer:
                writer.write(frame, observations, t, score, scene.matched)
                source_writer.write(frame, observations, t, score, scene.matched)
            index += 1
        if index == 0:
            raise ValueError("No video frames could be decoded.")
        if index < meta["n_frames"] * 0.98:
            raise ValueError("Video decoding stopped early; the file may be truncated.")
        duration = min(meta["duration"], index / meta["fps"])
        segments.completed.extend(specialists.finish(duration))
        events = segments.finish(duration)
        progress(
            stage="Finalizing video",
            progress=0.99,
            processed_frames=index,
            total_frames=meta["n_frames"],
        )
        if writer:
            writer.close()
            writer = None
            source_writer.close()
            source_writer = None
        for identity, votes in class_votes.items():
            kind = votes.most_common(1)[0][0]
            identities[identity] = kind
            group = (
                "people"
                if kind == "person"
                else "buses"
                if kind in {"bus", "truck"}
                else "cars"
                if kind in VEHICLES
                else None
            )
            if group:
                buckets.setdefault(int(first_seen[identity] // 60), Counter())[
                    group
                ] += 1
        counts = Counter(
            kind for kind in identities.values() if kind in VEHICLES or kind == "person"
        )
        activity = [
            {
                "time": f"{minute:02d}:00",
                "cars": buckets.get(minute, {}).get("cars", 0),
                "buses": buckets.get(minute, {}).get("buses", 0),
                "people": buckets.get(minute, {}).get("people", 0),
            }
            for minute in range(max(1, math.ceil(duration / 60)))
        ]
        report = {
            "events": [event.tuple() for event in events],
            "risk": curve,
            "meta": {
                **meta,
                "decoded_frames": index,
                "sample_fps": meta["fps"] / stride,
            },
            "engine": {
                "model": settings.weights.name,
                "device": detector.device,
                "tracker": "ByteTrack",
                "synthetic": False,
            },
            "scene": scene.summary(),
            "coverage": coverage(scene, detector.names.values(), specialists.labels),
            "eda": eda.finish(output),
            "summary": {
                "road_users": sum(counts.values()),
                "by_class": dict(counts),
                "activity": activity,
                "brightness_mean": round(sum(brightness) / max(1, len(brightness)), 2),
                "runtime_sec": round(time.perf_counter() - started, 2),
            },
            "details": [
                {
                    "label": event.label,
                    "start": event.start,
                    "end": event.end,
                    "confidence": event.confidence,
                    "lane": event.lane,
                    "evidence": event.evidence,
                    "key": event.key,
                }
                for event in events
            ],
            "limitations": [
                "Rule accuracy and camera geometry are provisional; these results are not ground truth.",
                "Risk is an uncalibrated image-space conflict score, not a validated accident probability.",
                "Counts are unique tracker IDs and can be affected by identity switches and missed detections.",
            ],
        }
        if output:
            write_json(output / "analysis.json", report)
        success = True
        return report
    finally:
        reader.close()
        if writer:
            writer.close(success=False)
        if source_writer:
            source_writer.close(success=False)
        if output and not success:
            (output / "annotated.mp4").unlink(missing_ok=True)
            (output / "source.mp4").unlink(missing_ok=True)
