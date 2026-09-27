"""Wall-clock budget shared by Part A and Part B of one harness run.

The organizers' harness gives each video 3 x its duration for Part A and Part B together,
and a video that runs over is scored as empty, events included. An exception inside
RiskEstimator.step only drops that video's risk curve. So Part A records when it starts,
and Part B stops early when finishing would take the total over the budget. Only clock
readings are shared, never frames or Part A results.
"""

import os
import time
from pathlib import Path

# The organizers' time factor. Override only to rehearse a slower machine, together with
# run_submission.py --time-factor.
FACTOR = float(os.getenv("CROSSING_TIME_FACTOR", "3.0"))
SAFETY = 0.95  # stop Part B when the projected total passes 95% of the budget
_started = {}


def part_a_started(video_path):
    _started[Path(video_path).name] = time.perf_counter()


def deadline(video_id, duration):
    """Latest acceptable finish time for this video (perf_counter clock).

    Unlimited unless Part A of this video ran in this process: only a harness run has a budget.
    """
    if video_id not in _started:
        return float("inf")
    return _started[video_id] + SAFETY * FACTOR * duration
