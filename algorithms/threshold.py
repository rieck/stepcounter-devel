"""Threshold step detector implementation.

Copyright (c) 2025 Konrad Rieck. MIT License
"""

import numpy as np

from .base import BaseDetector


class Threshold(BaseDetector):
    """Static threshold detector that counts steps above a magnitude threshold."""

    def __init__(self, threshold=100, **params):
        super().__init__(**params)
        self.threshold = threshold

    def detect_steps(self, x):
        """Detect steps above a magnitude threshold."""
        steps = 0
        for i in range(0, len(x)):
            if x[i] > self.threshold:
                steps += 1

        return steps

    @classmethod
    def get_param_grid(cls):
        return {
            "threshold": np.linspace(20000, 40000, 100).astype(int),
        }
