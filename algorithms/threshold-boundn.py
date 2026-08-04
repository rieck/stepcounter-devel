"""Threshold step detector requiring N consecutive steps.

Copyright (c) 2025 Konrad Rieck. MIT License
"""

from .base import BaseDetector


class ThresholdBoundN(BaseDetector):
    """Threshold detector requiring a run of N rhythmic steps.

    Generalization of ThresholdBound8: instead of using a single
    additional step to reject isolated movements, a detected step is
    only counted if it belongs to a run of at least ``min_run``
    consecutive steps whose gaps stay within ``max_step``.  With
    ``min_run == 2`` this reproduces the isolated-step rejection of
    ThresholdBound8.
    """

    def __init__(self, threshold=100, min_step=10, max_step=10, min_run=2, **params):
        super().__init__(**params)
        self.threshold = threshold
        self.min_step = min_step
        self.max_step = max_step
        self.min_run = min_run

    def detect_steps(self, x):
        """Detect steps, keeping only runs of at least min_run steps."""
        steps = 0
        last_step = None  # index of the previous detected step
        run_len = 0  # length of the current run of rhythmic steps

        for i in range(0, len(x)):
            mag = x[i] // 256
            if mag > self.threshold:
                # Enforce refractory gap between consecutive steps
                if last_step is None or i - last_step >= self.min_step:
                    if last_step is not None and i - last_step <= self.max_step:
                        # Step continues the current rhythmic run
                        run_len += 1
                    else:
                        # Rhythm broken: drop the previous run if too short
                        if run_len < self.min_run:
                            steps -= run_len
                        run_len = 1
                    steps += 1
                    last_step = i

        # Drop the trailing run if it never reached the required length
        if run_len < self.min_run:
            steps -= run_len

        return steps

    @classmethod
    def get_param_grid(cls):
        return {
            "threshold": [100],  # np.linspace(50, 150, 100).astype(int),
            "max_step": list(range(5, 41, 5)),  # max gap between rhythmic steps
            "min_step": list(range(4, 13, 2)),  # min gap (refractory) between steps
            "min_run": list(range(1, 11)),  # require 1..10 consecutive steps
        }
