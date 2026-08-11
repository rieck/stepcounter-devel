#!/usr/bin/env python3
"""Generate synthetic rapid-burst recordings for calibration.

Produces CSV files that look like rapid hand movements (e.g. lace-closing):
sustained oscillations that cross the detection threshold every few samples.
Ground truth is 0 steps for all files.

Magnitude scale from real recordings (l2-25hz-bw4):
  resting baseline:  ~19 000 (below threshold 25 600 = 100 * 256)
  burst peaks:       ~33 000 (well above threshold, ~1.3x)

Copyright (c) 2026 Konrad Rieck. MIT License
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

SAMPLE_RATE = 25  # Hz
THRESHOLD_RAW = 100 * 256  # = 25 600 — must stay consistent with calibrate.py default
BASELINE = 19_000  # resting magnitude (below threshold)
PEAK = 33_000  # burst peak magnitude (above threshold)
NOISE_STD = 400  # sample-to-sample noise on resting baseline

OUT_DIR = Path("recordings/l2-25hz-bw4")


def sine_burst(n_samples, half_period):
    """Sine wave oscillating between BASELINE and PEAK with the given half-period.

    half_period is the number of samples between a threshold crossing on the
    rising edge and the next crossing on the falling edge — i.e. how long the
    magnitude stays above threshold.  The full oscillation period is
    2 * half_period.
    """
    t = np.arange(n_samples)
    period = 2 * half_period
    wave = (PEAK - BASELINE) / 2 * np.sin(2 * np.pi * t / period) + (
        PEAK + BASELINE
    ) / 2
    return wave.astype(np.int32)


def rest_section(n_samples, rng):
    """Flat resting baseline with small noise, clearly below threshold."""
    return (rng.normal(BASELINE, NOISE_STD, n_samples)).astype(np.int32)


def make_recording(sections, rng):
    """Build a magnitude array from (kind, n_samples[, half_period]) tuples."""
    parts = []
    for sec in sections:
        if sec[0] == "rest":
            parts.append(rest_section(sec[1], rng))
        elif sec[0] == "burst":
            burst = sine_burst(sec[1], sec[2])
            # Add light noise to make it look more natural
            burst = burst + rng.normal(0, NOISE_STD // 2, sec[1]).astype(np.int32)
            parts.append(burst)
    return np.concatenate(parts)


def write_csv(path, magnitudes, rng):
    n = len(magnitudes)
    timestamps = np.arange(n) / SAMPLE_RATE

    header_meta = json.dumps(
        {
            "version": 1,
            "device_state": {
                "mode": 0,
                "data_rate": 3,
                "low_power": 0,
                "bwf_mode": 1,
                "range": 0,
                "filter": 0,
                "low_noise": 0,
            },
            "data_type": 2,
            "synthetic": True,
        }
    )

    rows = []
    for i, (ts, mag) in enumerate(zip(timestamps, magnitudes)):
        row = {"Timestamp": round(ts, 4), "Magnitude": int(mag)}
        if i == 0:
            row["Steps"] = 0
            row["Header"] = header_meta
        else:
            row["Steps"] = None
            row["Header"] = None
        rows.append(row)

    df = pd.DataFrame(rows, columns=["Timestamp", "Magnitude", "Steps", "Header"])
    df.to_csv(path, index=False)
    print(f"  wrote {path} ({n} samples, {n / SAMPLE_RATE:.0f} s)")


def main():
    rng = np.random.default_rng(42)

    # Verify our peaks actually cross the threshold
    assert PEAK > THRESHOLD_RAW, "burst peak must exceed threshold"
    assert BASELINE < THRESHOLD_RAW, "resting baseline must be below threshold"

    recordings = {
        # half_period=5 → threshold crossings every 5 samples (2.5 Hz oscillation)
        # Most adversarial: every other crossing is exactly min_step=10 away
        "rapid-burst1.csv": [
            ("rest", 250),  # 10 s rest
            ("burst", 500, 5),  # 20 s burst, half-period 5
            ("rest", 125),  # 5 s rest
            ("burst", 375, 5),  # 15 s burst, half-period 5
            ("rest", 250),  # 10 s rest
        ],
        # half_period=5 again but with shorter, repeated bursts
        "rapid-burst2.csv": [
            ("rest", 125),
            ("burst", 250, 5),  # 10 s burst
            ("rest", 125),
            ("burst", 250, 5),  # 10 s burst
            ("rest", 125),
            ("burst", 250, 5),  # 10 s burst
            ("rest", 125),
            ("burst", 250, 5),  # 10 s burst
            ("rest", 125),
        ],
        # half_period=4 → crossings every 4 samples (3.1 Hz, faster motion)
        "rapid-burst3.csv": [
            ("rest", 250),
            ("burst", 750, 4),  # 30 s burst, half-period 4
            ("rest", 500),
        ],
        # half_period=6 → crossings every 6 samples (2.1 Hz, slightly slower)
        # Tests whether calibration also covers this slower variant
        "rapid-burst4.csv": [
            ("rest", 250),
            ("burst", 500, 6),  # 20 s burst, half-period 6
            ("rest", 125),
            ("burst", 375, 6),  # 15 s burst, half-period 6
            ("rest", 250),
        ],
    }

    for fname, sections in recordings.items():
        mag = make_recording(sections, rng)
        write_csv(OUT_DIR / fname, mag, rng)

    print()
    print("Add to split.json:")
    print('  set1: "rapid-burst1.csv", "rapid-burst2.csv"')
    print('  set2: "rapid-burst3.csv", "rapid-burst4.csv"')


if __name__ == "__main__":
    main()
