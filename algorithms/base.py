"""Base class for step detection algorithms.

Copyright (c) 2025 Konrad Rieck. MIT License
"""


class BaseDetector:
    """Base class for step detection algorithms."""

    def __init__(self, **params):
        # Initialize detector with parameters
        self.params = params

    def detect_steps(self, mag_series):
        # Override in subclasses to implement step detection
        raise NotImplementedError("Subclasses must implement detect_steps")

    @classmethod
    def get_param_grid(cls):
        # Override in subclasses to define parameter grid
        return {}
