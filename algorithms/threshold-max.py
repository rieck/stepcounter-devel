"""Threshold step detector implementation.

Copyright (c) 2025 Konrad Rieck. MIT License
"""

import numpy as np

from .base import BaseDetector


class ThresholdMax(BaseDetector):
    """Threshold detector with maximum step size"""

    def __init__(self, threshold=100, max_step=10, **params):
        super().__init__(**params)
        self.threshold = threshold
        self.max_step = max_step

    def detect_steps(self, x):
        """Detect steps with maximum step size."""
        steps = 0
        last_step1 = -1
        last_step2 = last_step1

        for i in range(0, len(x)):
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
        }
