"""Threshold step detector implementation."""

import numpy as np

from .base import BaseDetector


class ThresholdMin(BaseDetector):
    """Threshold detector with minimum step size"""

    def __init__(self, threshold=100, min_step=10, **params):
        super().__init__(**params)
        self.threshold = threshold
        self.min_step = min_step

    def detect_steps(self, x):
        """Detect steps with basic validation against random movement."""
        steps = 0
        last_step = -self.min_step

        for i in range(0, len(x)):
            # Skip if step is too small
            if i - last_step < self.min_step:
                continue

            # Check for transition
            if x[i] > self.threshold:
                steps += 1
                last_step = i

        return steps

    @classmethod
    def get_param_grid(cls):
        return {
            "threshold": np.linspace(23000, 30000, 100).astype(int),
            "min_step": np.linspace(1, 10, 10).astype(int),
        }
