"""Threshold step detector implementation."""

import numpy as np

from .base import BaseDetector


class ThresholdDetector(BaseDetector):
    """Threshold detector that counts steps above a magnitude threshold."""

    def __init__(self, threshold=1000, **params):
        super().__init__(threshold=threshold, **params)
        self.threshold = threshold

    def detect_steps(self, mag_series):
        # Count steps above threshold
        return int(np.sum(mag_series > self.threshold))

    @classmethod
    def get_param_grid(cls):
        return {"threshold": np.logspace(2, 5, 100)}
