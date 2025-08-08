"""Base class for step detection algorithms."""


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
