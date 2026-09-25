import hashlib
import json
from pathlib import Path
from vision.types import CLASSES
from evaluate import validate, OFFICIAL_CLASSES


def test_organizer_files_unchanged():
    hashes = json.loads(Path("research/starter-sha256.json").read_text())
    for name in ["run_submission.py", "evaluate.py"]:
        assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == hashes[name]


def test_official_classes_and_output_contract():
    assert CLASSES == OFFICIAL_CLASSES
    errors, _ = validate(
        {
            "team": "wiut",
            "videos": {
                "clip.mp4": {"events": [[1.0, 3.0, "near_miss"]], "risk": [[0.0, 0.1]]}
            },
        }
    )
    assert errors == []


def test_root_solution_exports_the_exact_harness_interface():
    import solution

    assert solution.CLASSES == OFFICIAL_CLASSES
    assert callable(solution.detect_events)
    assert callable(solution.RiskEstimator.reset)
    assert callable(solution.RiskEstimator.step)
