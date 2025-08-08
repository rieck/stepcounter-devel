"""Random step detector implementation."""

import numpy as np

from .base import BaseDetector


class RandomDetector(BaseDetector):
    """Random step detector that detects steps with given probability."""

    def __init__(self, prob=0.1, **params):
        super().__init__(prob=prob, **params)
        self.prob = prob

    def detect_steps(self, mag_series):
        # For each point, detect step with probability prob
        steps = np.random.random(len(mag_series)) < self.prob
        return int(np.sum(steps))

    @classmethod
    def get_param_grid(cls):
        return {"prob": np.logspace(-10, -1, 100)}
