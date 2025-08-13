"""Threshold step detector implementation.

Copyright (c) 2025 Konrad Rieck. MIT License
"""

from collections import deque

import numpy as np

from .base import BaseDetector


class ThresholdHp8(BaseDetector):
    """Threshold detector with high-pass filter (8-bit)."""

    def __init__(self, threshold=100, win_size=100, **params):
        super().__init__(**params)
        self.threshold = threshold
        self.win_size = win_size

    def detect_steps(self, x):
        """Detect steps with high-pass filter."""
        steps = 0
        buffer = deque(maxlen=self.win_size)

        for i in range(0, len(x)):
            mag = x[i] // 256
            buffer.append(mag)
            if len(buffer) < self.win_size:
                continue

            # High-pass filter: remove static gravity component
            mean_mag = sum(buffer) / self.win_size
            hp_value = mag - mean_mag

            if hp_value > self.threshold:
                steps += 1

        return steps

    @classmethod
    def get_param_grid(cls):
        return {
            "threshold": np.linspace(1, 100, 100).astype(int),
            "win_size": np.unique(np.linspace(10, 100, 90).astype(int)),
        }
