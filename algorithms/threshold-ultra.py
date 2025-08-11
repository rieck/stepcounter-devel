"""Threshold step detector implementation.

Copyright (c) 2025 Konrad Rieck. MIT License
"""

from collections import deque

import numpy as np

from .base import BaseDetector


class ThresholdUltra(BaseDetector):
    """Threshold detector with bounded step size"""

    def __init__(
        self, threshold=100, min_step=10, max_step=10, win_lp=100, win_hp=100, **params
    ):
        super().__init__(**params)
        self.threshold = threshold
        self.min_step = min_step
        self.max_step = max_step
        self.win_lp = win_lp
        self.win_hp = win_hp

    def detect_steps(self, x):
        """Detect steps with basic validation against random movement."""
        steps = 0
        last_step1 = -self.min_step
        last_step2 = last_step1
        hp_buffer = deque(maxlen=self.win_hp)
        lp_buffer = deque(maxlen=self.win_lp)

        for i in range(0, len(x)):
            hp_buffer.append(x[i])
            lp_buffer.append(x[i])
            if len(hp_buffer) < self.win_hp or len(lp_buffer) < self.win_lp:
                continue

            # Skip if step is too small
            if i - last_step1 < self.min_step:
                continue

            mag = x[i]
            if self.win_lp > 0:
                mag = sum(lp_buffer) / self.win_lp

            if self.win_hp > 0:
                mag = mag - sum(hp_buffer) / self.win_hp

            # Check for transition
            if mag > self.threshold:
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
            "threshold": np.linspace(1000, 5000, 25).astype(int),
            "max_step": np.linspace(0, 30, 10).astype(int),
            "min_step": np.linspace(0, 4, 4).astype(int),
            "win_lp": np.unique(np.logspace(0, 2, 5).astype(int)),
            "win_hp": np.unique(np.logspace(0, 2, 5).astype(int)),
        }
