"""Threshold step detector with two independent references.

Copyright (c) 2026 Konrad Rieck. MIT License
"""

from .base import BaseDetector


class ThresholdBoundN3(BaseDetector):
    """ThresholdBoundN variant with separate min-step and streak references.

    Uses two independent reference points:
    - last_crossing: updated on every threshold crossing (counted or not).
      Used for the min_step refractory gate. This prevents two consecutive
      short crossings from accumulating into a valid step: every crossing
      resets the clock, so rapid bursts (e.g. lace-closing) can only ever
      count the first peak.
    - last_counted: updated only on accepted steps.
      Used for the max_step / streak check. Streak continuity is measured
      from the last real step, not from any intermediate echo peak, so the
      streak is not disrupted by noise between footfalls.
    """

    def __init__(self, threshold=100, min_step=10, max_step=10, min_streak=2, **params):
        super().__init__(**params)
        self.threshold = threshold
        self.min_step = min_step
        self.max_step = max_step
        self.min_streak = min_streak

    def detect_steps(self, x):
        """Detect steps, keeping only streaks of at least min_streak steps."""
        steps = 0
        last_crossing = None  # last threshold crossing, counted or not
        last_counted = None  # last accepted step
        streak_len = 0

        for i in range(len(x)):
            mag = x[i] // 256
            if mag > self.threshold:
                if last_crossing is None or i - last_crossing >= self.min_step:
                    # Streak continuity measured from last counted step
                    if last_counted is not None and i - last_counted <= self.max_step:
                        streak_len += 1
                    else:
                        if streak_len < self.min_streak:
                            steps -= streak_len
                        streak_len = 1
                    steps += 1
                    last_counted = i
                # Always advance the crossing reference
                last_crossing = i

        if streak_len < self.min_streak:
            steps -= streak_len

        return steps

    @classmethod
    def get_param_grid(cls):
        return {
            "threshold": list(range(50, 151, 2)),
            "max_step": list(range(1, 41)),
            "min_step": list(range(1, 17)),
            "min_streak": list(range(1, 11)),
        }
