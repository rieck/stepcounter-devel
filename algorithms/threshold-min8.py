"""Threshold step detector implementation.

Copyright (c) 2025 Konrad Rieck. MIT License
"""

import numpy as np

from .base import BaseDetector


class ThresholdMin8(BaseDetector):
    """Threshold detector with minimum step size (8-bit)."""

    def __init__(self, threshold=100, min_step=10, **params):
        super().__init__(**params)
        self.threshold = threshold
        self.min_step = min_step

    def detect_steps(self, x):
        """Detect steps with minimum step size."""
        steps = 0
        last_step = -self.min_step

        for i in range(0, len(x)):
            mag = x[i] // 256

            # Skip if step is too small
            if i - last_step < self.min_step:
                continue

            # Check for transition
            if mag > self.threshold:
                steps += 1
                last_step = i

        return steps

    @classmethod
    def get_param_grid(cls):
        return {
            "threshold": np.linspace(0, 100, 100).astype(int),
            "min_step": np.linspace(1, 10, 10).astype(int),
        }
