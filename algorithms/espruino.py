"""Espruino / gfwilliams state-machine pedometer.

Ported from voloved's second-movement PR #191 (lib/embedded_pedometer/
count_steps.c, function count_steps_espruino), which itself ports
https://github.com/gfwilliams/step-count.

Pipeline per sample: DC-removal EMA filter -> 7-tap FIR -> activity gate ->
peak detection -> a 4-state machine that only credits steps once it has seen
X_STEPS in a row, each within a timing window [t_min_step, t_max_step].

The original constants are tuned for 12.5 Hz and a 4 g range. Our recordings
are 25 Hz / +-2 g, so the input scale (out_shift), sensitivity (raw_threshold)
and timing bounds are exposed as parameters for the grid search to fit.

The step-counting algorithm originates in Espruino (libs/misc/stepcount.c),
Copyright (c) 2021 Gordon Williams <gw@pur3.co.uk>, and is licensed under the
Mozilla Public License, v. 2.0. This Python port (Copyright (c) 2026 Konrad
Rieck) is a derivative work and therefore remains under the MPL-2.0, not the
MIT license used by the rest of this repository.

This Source Code Form is subject to the terms of the Mozilla Public License,
v. 2.0. If a copy of the MPL was not distributed with this file, You can
obtain one at http://mozilla.org/MPL/2.0/.
"""

from .base import BaseDetector

# Fixed 7-tap FIR filter and DC-removal window, as in the original C.
_FILTER_TAPS = (-11, -15, 44, 68, 44, -15, -11)
_NTAPS = len(_FILTER_TAPS)
_DC_NSAMPLE = 12  # DC-removal EMA: alpha = 1 / NSAMPLE


def _clip(v, lo, hi):
    return lo if v < lo else (hi if v > hi else v)


class Espruino(BaseDetector):
    """gfwilliams/Espruino state-machine pedometer (the algorithm used in PR #191)."""

    def __init__(
        self,
        raw_threshold=15,
        t_min_step=4,
        t_max_step=16,
        out_shift=5,
        x_steps=6,
        n_active_samples=3,
        **params,
    ):
        super().__init__(**params)
        self.raw_threshold = raw_threshold
        self.t_min_step = t_min_step
        self.t_max_step = t_max_step
        self.out_shift = out_shift
        self.x_steps = x_steps
        self.n_active_samples = n_active_samples

    def detect_steps(self, x):
        RAW, TMIN, TMAX = self.raw_threshold, self.t_min_step, self.t_max_step
        XS, NACT, OUT = self.x_steps, self.n_active_samples, self.out_shift

        # Per-session state (mirrors count_steps_espruino_init).
        dc_avg_total = 8192 * _DC_NSAMPLE
        fir_hist = [0] * _NTAPS
        fir_ix = 0
        acc_filtered = 0
        acc_hist = [0, 0]  # [older, newer] previous FIR outputs
        step_state = 0  # 0=STILL 1=STEP_1 2=STEP_22N 3=STEPPING
        hold_steps = 0
        step_length = 0
        active = 0
        gate_open = False
        total = 0

        for mag in x:
            if mag == 0:  # all-zero == misread, skip
                continue
            acc = int(mag) << 1  # scaling from count_steps_espruino

            # DC-removal EMA filter.
            dc_avg_total += acc - dc_avg_total // _DC_NSAMPLE
            v = (acc - dc_avg_total // _DC_NSAMPLE) >> OUT
            v = _clip(v, -128, 127)

            # 7-tap FIR (newest sample weighted by taps[0]).
            fir_hist[fir_ix] = v
            fir_ix = (fir_ix + 1) % _NTAPS
            acc_hist[0] = acc_hist[1]
            acc_hist[1] = acc_filtered
            a = 0
            idx = fir_ix
            for tap in _FILTER_TAPS:
                idx = idx - 1 if idx != 0 else _NTAPS - 1
                a += fir_hist[idx] * tap
            acc_filtered = _clip(a >> 2, -32768, 32767)

            # Activity gate: open after NACT consecutive active samples.
            if v > RAW or v < -RAW:
                if active < NACT:
                    active += 1
                if active == NACT:
                    gate_open = True
            else:
                if active > 0:
                    active -= 1
                if active == 0:
                    gate_open = False

            if step_length < 255:
                step_length += 1

            # Peak in the middle of the 3-sample window -> run the state machine.
            if gate_open and acc_hist[1] > acc_hist[0] and acc_hist[1] > acc_filtered:
                in_window = TMIN <= step_length <= TMAX
                if step_state == 0:  # S_STILL
                    step_state, hold_steps = 1, 1
                elif step_state == 1:  # S_STEP_1
                    if in_window:
                        step_state, hold_steps = 2, 2
                    else:
                        hold_steps = 1
                elif step_state == 2:  # S_STEP_22N
                    if in_window:
                        hold_steps += 1
                        if hold_steps >= XS:
                            step_state = 3
                            total += XS
                    else:
                        step_state = 1
                elif step_state == 3:  # S_STEPPING
                    if in_window:
                        total += 1
                    else:
                        step_state = 1
                step_length = 0

        return total

    @classmethod
    def get_param_grid(cls):
        return {
            "out_shift": [5, 6, 7, 8, 9],
            "raw_threshold": [8, 15, 25, 40],
            "t_min_step": [4, 6, 8],
            "t_max_step": [16, 24, 32],
        }
