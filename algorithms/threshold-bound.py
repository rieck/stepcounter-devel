"""Threshold step detector implementation."""

import numpy as np

from .base import BaseDetector


class ThresholdBound(BaseDetector):
    """Threshold detector with bounded step size"""

    def __init__(self, threshold=100, min_step=10, max_step=10, **params):
        super().__init__(**params)
        self.threshold = threshold
        self.min_step = min_step
        self.max_step = max_step

    def detect_steps(self, x):
        """Detect steps with basic validation against random movement."""
        steps = 0
        last_step1 = -self.min_step
        last_step2 = last_step1

        for i in range(0, len(x)):
            # Skip if step is too small
            if i - last_step1 < self.min_step:
                continue

            # Check for transition
            if x[i] > self.threshold:
                steps += 1
                last_step2 = last_step1
                last_step1 = i

            # Reduce step count if step is too large
            if (
                i - last_step1 > self.max_step
                and last_step1 - last_step2 > self.max_step
            ):
                steps -= 1
                last_step1 = last_step2

        return steps

    @classmethod
    def get_param_grid(cls):
        return {
            "threshold": np.linspace(23000, 34000, 100).astype(int),
            "max_step": np.linspace(1, 40, 40).astype(int),
            "min_step": np.linspace(1, 10, 10).astype(int),
        }
