"""Threshold step detector implementation.

Copyright (c) 2025 Konrad Rieck. MIT License
"""

from collections import deque

import numpy as np

from .base import BaseDetector


class ThresholdLp(BaseDetector):
    """Threshold detector with low-pass filter."""

    def __init__(self, threshold=100, win_size=100, **params):
        super().__init__(**params)
        self.threshold = threshold
        self.win_size = win_size

    def detect_steps(self, x):
        """Detect steps with low-pass filter."""
        steps = 0
        buffer = deque(maxlen=self.win_size)

        for i in range(0, len(x)):
            buffer.append(x[i])
            if len(buffer) < self.win_size:
                continue

            # Low-pass filter: remove high-frequency noise
            lp_value = sum(buffer) / self.win_size
            if lp_value > self.threshold:
                steps += 1

        return steps

    @classmethod
    def get_param_grid(cls):
        return {
            "threshold": np.linspace(20000, 32000, 100).astype(int),
            "win_size": np.unique(np.logspace(0, 2, 50).astype(int)),
        }
