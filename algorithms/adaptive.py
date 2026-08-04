"""Adaptive-threshold step detector (voloved's count_steps_simple).

Ported from second-movement PR #191 (lib/embedded_pedometer/count_steps.c,
function count_steps_simple). It runs once per FIFO read (~once per second):
inside a batch it counts a step whenever the (>>3 scaled) magnitude crosses a
threshold, skipping a few samples afterwards, then nudges the threshold via an
exponential moving average toward `threshold_mult` times the batch mean.

Because the threshold adapts per batch (not per sample) and the batch has size
and step caps, the flat magnitude series is re-chunked into batches here.
The original caps (max_fifo_size=13, batch_size ~ one second) are tuned for
12.5 Hz, so they are exposed as parameters for the grid search.

Copyright (c) 2025 Konrad Rieck. MIT License
"""

from .base import BaseDetector


class Adaptive(BaseDetector):
    """Adaptive EMA-threshold detector (count_steps_simple from PR #191)."""

    def __init__(
        self,
        init_threshold=2000,
        threshold_mult=1.3,
        samp_ignore=3,
        avg_window_shift=7,
        max_fifo_size=13,
        batch_size=25,
        **params,
    ):
        super().__init__(**params)
        self.init_threshold = init_threshold
        self.threshold_mult = threshold_mult
        self.samp_ignore = samp_ignore
        self.avg_window_shift = avg_window_shift
        self.max_fifo_size = max_fifo_size
        self.batch_size = batch_size

    def detect_steps(self, x):
        x = list(x)  # accept list / ndarray / pandas Series with any index
        threshold = self.init_threshold
        avg_window = (1 << self.avg_window_shift) - 1
        max_steps = (
            self.max_fifo_size // self.samp_ignore
            if self.samp_ignore
            else self.max_fifo_size
        )
        total = 0

        # Process the series in per-FIFO-read batches; threshold persists across them.
        for start in range(0, len(x), self.batch_size):
            batch = x[start : start + self.batch_size]
            new_steps = 0
            samples_processed = 0
            samples_sum = 0

            i = 0
            n = len(batch)
            while i < n:
                if i >= self.max_fifo_size:
                    break
                mag = int(batch[i]) >> 3
                if mag == 0:  # all-zero == misread, skip
                    i += 1
                    continue
                if mag >= threshold:
                    new_steps += 1
                    i += self.samp_ignore  # refractory: ignore the next few samples
                samples_processed += 1
                samples_sum += mag
                i += 1

            # EMA nudge of the threshold toward threshold_mult * batch mean.
            if samples_processed > 0:
                avg = int((samples_sum // samples_processed) * self.threshold_mult)
                threshold = (threshold * avg_window + avg) >> self.avg_window_shift

            if new_steps > max_steps:
                new_steps = max_steps
            total += new_steps

        return total

    @classmethod
    def get_param_grid(cls):
        return {
            "threshold_mult": [1.1, 1.3, 1.5, 1.75],
            "samp_ignore": [2, 3, 4, 5],
            "max_fifo_size": [13, 20, 25, 32],
            "batch_size": [13, 25],
        }
