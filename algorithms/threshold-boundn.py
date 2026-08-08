"""Threshold step detector requiring N consecutive steps.

Copyright (c) 2025 Konrad Rieck. MIT License
"""

from .base import BaseDetector


class ThresholdBoundN(BaseDetector):
    """Threshold detector requiring a run of N rhythmic steps.

    Generalization of ThresholdBound8: instead of using a single
    additional step to reject isolated movements, a detected step is
    only counted if it belongs to a streak of at least ``min_streak``
    consecutive steps whose gaps stay within ``max_step``.  With
    ``min_streak == 2`` this reproduces the isolated-step rejection of
    ThresholdBound8.
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
        last_step = None  # index of the previous detected step
        streak_len = 0  # length of the current run of rhythmic steps

        for i in range(0, len(x)):
            mag = x[i] // 256
            if mag > self.threshold:
                # Enforce refractory gap between consecutive steps
                if last_step is None or i - last_step >= self.min_step:
                    if last_step is not None and i - last_step <= self.max_step:
                        # Step continues the current rhythmic streak
                        streak_len += 1
                    else:
                        # Rhythm broken: drop the previous streak if too short
                        if streak_len < self.min_streak:
                            steps -= streak_len
                        streak_len = 1
                    steps += 1
                    last_step = i

        # Drop the trailing streak if it never reached the required length
        if streak_len < self.min_streak:
            steps -= streak_len

        return steps

    @classmethod
    def get_param_grid(cls):
        return {
            "threshold": [100],  # np.linspace(50, 150, 100).astype(int),
            "max_step": list(range(5, 41, 5)),  # max gap between rhythmic steps
            "min_step": list(range(4, 13, 2)),  # min gap (refractory) between steps
            "min_streak": list(range(1, 11)),  # require 1..10 consecutive steps
        }
