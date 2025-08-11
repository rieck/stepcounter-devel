"""Threshold step detector implementation."""

from collections import deque

import numpy as np

from .base import BaseDetector


class ThresholdHp(BaseDetector):
    """Threshold detector with high-pass filter."""

    def __init__(self, threshold=100, win_size=100, **params):
        super().__init__(**params)
        self.threshold = threshold
        self.win_size = win_size

    def detect_steps(self, x):
        # Count threshold crossings (transitions from below to above threshold)
        steps = 0
        buffer = deque(maxlen=self.win_size)

        for i in range(0, len(x)):
            buffer.append(x[i])
            if len(buffer) < self.win_size:
                continue

            # High-pass filter: remove static gravity component
            mean_mag = sum(buffer) / self.win_size
            hp_value = x[i] - mean_mag

            if hp_value > self.threshold:
                steps += 1

        return steps

    @classmethod
    def get_param_grid(cls):
        return {
            "threshold": np.linspace(1000, 8000, 100).astype(int),
            "win_size": np.unique(np.logspace(0, 2, 50).astype(int)),
        }
