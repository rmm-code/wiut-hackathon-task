from vision import budget
from vision.pipeline import analyze
from vision.risk import RiskEstimator
from vision.types import CLASSES

__all__ = ["CLASSES", "detect_events", "RiskEstimator"]


def detect_events(video_path: str) -> list[list]:
    budget.part_a_started(video_path)
    return analyze(video_path)["events"]
