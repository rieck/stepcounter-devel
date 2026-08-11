"""Threshold step detector requiring N consecutive steps (sliding reference).

Copyright (c) 2026 Konrad Rieck. MIT License
"""

from .base import BaseDetector


class ThresholdBoundN2(BaseDetector):
    """ThresholdBoundN variant where the reference advances on every crossing.

    Identical to ThresholdBoundN except that a crossing rejected by the
    min_step refractory gap still moves ``last_step`` to the current
    sample.  This prevents two consecutive short crossings from
    accumulating into a valid step: the intermediate peak resets the
    clock, so the following crossing is measured against it rather than
    against the earlier counted step.
    """

    def __init__(self, threshold=100, min_step=10, max_step=10, min_streak=2, **params):
        super().__init__(**params)
        self.threshold = threshold
        self.min_step = min_step
        self.max_step = max_step
        self.min_streak = min_streak

    def detect_steps(self, x):
        """Detect steps, keeping only streaks of at least min_streak steps."""
        steps = 0
        last_step = None  # index of the previous threshold crossing (counted or not)
        streak_len = 0  # length of the current run of rhythmic steps

        for i in range(0, len(x)):
            mag = x[i] // 256
            if mag > self.threshold:
                if last_step is None or i - last_step >= self.min_step:
                    if last_step is not None and i - last_step <= self.max_step:
                        streak_len += 1
                    else:
                        if streak_len < self.min_streak:
                            steps -= streak_len
                        streak_len = 1
                    steps += 1
                # Always advance the reference, whether the step was counted or not
                last_step = i

        # Drop the trailing streak if it never reached the required length
        if streak_len < self.min_streak:
            steps -= streak_len

        return steps

    @classmethod
    def get_param_grid(cls):
        return {
            "threshold": list(range(50, 151, 2)),
            "max_step": list(range(1, 41)),
            "min_step": list(range(1, 17)),
            "min_streak": list(range(1, 11)),
        }
