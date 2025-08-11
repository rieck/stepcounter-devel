"""Peak detection step detection algorithm.

Copyright (c) 2025 Konrad Rieck. MIT License
"""

import numpy as np

from .base import BaseDetector


class PeakDetect(BaseDetector):
    """Step detection algorithm based on peak detection."""

    def __init__(self, mean_win=12, detect_win=12, bounce_win=3, thres=1.2, **params):
        super().__init__(**params)
        self.mean_win = mean_win
        self.detect_win = detect_win
        self.bounce_win = bounce_win
        self.thres = thres

    def calc_mean_diffs(self, x):
        """Calculate mean differences with neighbors."""
        n = len(x)
        diffs = np.zeros(n)

        for i in range(n):
            start = max(0, i - self.mean_win)
            end = min(n, i + self.mean_win + 1)
            diffs[i] = x[i] - np.mean(x[start:end])

        return diffs

    def find_outliers(self, x):
        """Find outlier points using running statistics."""
        outliers = []

        # Pre-compute rolling means and stds using numpy
        window_size = 2 * self.detect_win + 1
        weights = np.ones(window_size)
        means = np.convolve(x, weights / weights.sum(), mode="same")

        # Calculate rolling std using vectorized operations
        x2 = np.convolve(x**2, weights / weights.sum(), mode="same")
        stds = np.sqrt(x2 - means**2)

        # Find outliers using vectorized comparison
        mask = (x - means) > (self.thres * stds)
        outliers = np.where(mask)[0].tolist()

        return outliers

    def filter_bounces(self, outliers, diffs):
        """Remove bounce artifacts by keeping strongest peaks in groups."""
        if not outliers:
            return []

        # Convert to numpy array for faster operations
        outliers = np.array(outliers)

        # Calculate differences between consecutive outliers
        gaps = np.diff(outliers)

        # Find where groups start (gap >= bounce_win)
        group_starts = np.where(gaps >= self.bounce_win)[0] + 1

        # Add start and end indices to get complete groups
        group_indices = np.concatenate(([0], group_starts, [len(outliers)]))

        # Process each group to keep strongest peak
        filtered = []
        for start, end in zip(group_indices[:-1], group_indices[1:]):
            group = outliers[start:end]
            # Get strongest peak in group
            strongest = group[np.argmax(diffs[group])]
            filtered.append(strongest)

        return filtered

    def detect_steps(self, mag_series):
        """Detect steps using peak detection algorithm."""
        diffs = self.calc_mean_diffs(mag_series)
        outliers = self.find_outliers(diffs)
        peaks = self.filter_bounces(outliers, diffs)
        return len(peaks)

    @classmethod
    def get_param_grid(cls):
        return {
            "mean_win": np.unique(np.logspace(0, 2, 10).astype(int)),
            "detect_win": np.unique(np.logspace(0, 2, 10).astype(int)),
            "bounce_win": np.unique(np.logspace(0, 2, 10).astype(int)),
            "thres": np.round(np.linspace(1.0, 3.0, 25), 10),
        }
