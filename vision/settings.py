import json
import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
(ROOT / ".cache" / "yolo" / "Ultralytics").mkdir(parents=True, exist_ok=True)
os.environ.setdefault("YOLO_CONFIG_DIR", str(ROOT / ".cache" / "yolo"))
os.environ.setdefault("YOLO_AUTOINSTALL", "false")
os.environ.setdefault("YOLO_OFFLINE", "true")
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".cache" / "matplotlib"))


@dataclass(frozen=True)
class Settings:
    weights: Path = ROOT / "weights" / "yolo11s.pt"
    scene: Path = ROOT / "config" / "camera.json"
    device: str = "auto"
    image_size: int = 640
    sample_fps: float = 8.0
    confidence: float = 0.2
    max_seconds: float = 120.1
    # Cloudflare-proxied hosts reject request bodies above 100 MB.
    max_bytes: int = 95 * 1024 * 1024

    @classmethod
    def load(cls):
        return cls(
            weights=Path(os.getenv("CROSSING_WEIGHTS", str(cls.weights))).resolve(),
            scene=Path(os.getenv("CROSSING_SCENE", str(cls.scene))).resolve(),
            device=os.getenv("CROSSING_DEVICE", "auto"),
            sample_fps=float(os.getenv("CROSSING_FPS", "8")),
            max_bytes=int(float(os.getenv("CROSSING_MAX_MB", "95")) * 1024 * 1024),
        )

    def camera(self):
        return json.loads(self.scene.read_text())


def device_name(requested: str):
    import torch

    if requested != "auto":
        return requested
    if torch.cuda.is_available():
        return "cuda:0"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"
