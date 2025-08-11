"""Threshold step detector implementation.

Copyright (c) 2025 Konrad Rieck. MIT License
"""

import numpy as np

from .base import BaseDetector


class ThresholdEdge(BaseDetector):
    """Threshold detector with minimum step size and edge detection."""

    def __init__(self, threshold=100, min_step=10, **params):
        super().__init__(**params)
        self.threshold = threshold
        self.min_step = min_step

    def detect_steps(self, x):
        """Detect steps with edge detection."""
        steps = 0
        last_step = -self.min_step
        above = False

        for i in range(0, len(x)):
            if not above and x[i] > self.threshold:
                # Rising edge detected
                if i - last_step >= self.min_step:
                    steps += 1
                    last_step = i
                above = True
            elif above and x[i] < self.threshold:
                # Falling edge detected, reset flag
                above = False

        return steps

    @classmethod
    def get_param_grid(cls):
        return {
            "threshold": np.linspace(23000, 30000, 100).astype(int),
            "min_step": np.linspace(1, 10, 10).astype(int),
        }
