# 🏃‍♂️ Step Counter Development

This repository contains tools and experiments for developing a step counting algorithms for [SensorWatch Pro](https://www.sensorwatch.net). The goal is to experiment with different signal processing approaches to accurately detect steps from accelerometer data of the watch.

## Directory Structure

- `recordings/` - Samples of recorded accelerometer data

- `algorithms/` - Step detection algorithm implementations

- `runtime/` - Runtime performance benchmarks and measurements

- `watch_face/` - Watch face for recording accelerometer data

## Setup

The project uses a Makefile for common development tasks:

### Installation

```bash
# Install the package in development mode
make install

# Install with development dependencies
make install-dev
```

## Data Analysis

### Data Parser

The `parse.py` tool processes binary accelerometer data recorded on the SensorWatch device using the experimental watch-face `stepcounter_logging_face.c` It supports both raw binary and base64 encoded files. Moreover, it parses metadata about the  device configuration used during recording.

#### Usage

```bash
# Parse a base64 encoded file
python parse.py recordings/l2-12hz/fast-walking-bf.b64

# Export to CSV format
python parse.py --csv recordings/l2-12hz/normal-walking-sh.b64

# Show detailed header information
python parse.py --header recordings/l2-12hz/slow-walking-bf.b64
```

### Algorithm Analysis

The `calibrate.py` tool performs grid search over parameter spaces to find optimal configurations for step detection algorithms so that their performance can be compared. It automatically splits data into calibration and evaluation sets, leverages parallel processing, and provides support for calibrating multiple algorithms simultaneously using the `all` option.

#### Usage

```bash
# Calibrate a single algorithm
python calibrate.py threshold_bound

# Calibrate all available algorithms
python calibrate.py all

# Use custom data directory
python calibrate.py -d recordings/l2-25hz-bw2 threshold
```

#### Algorithms Available

- `threshold` - Basic threshold-based detection
- `threshold_lp` - Threshold with low-pass filter
- `threshold_hp` - Threshold with high-pass filter
- `threshold_hp8` - High-pass filter with edge detection (8-bit magnitude)
- `threshold_min` - Threshold with minimum step size (refractory gap)
- `threshold_min8` - Minimum step size (8-bit magnitude)
- `threshold_max` - Threshold with maximum step size
- `threshold_bound` - Bounded step size (min and max) with edge detection
- `threshold_bound8` - Bounded step size with edge detection (8-bit magnitude)
- `threshold_bound_n` - Bounded detector requiring a streak of N rhythmic steps
- `threshold_edge` - Minimum step size with edge detection
- `peak_detect` - Classic peak detection
- `espruino` - Espruino / gfwilliams state-machine pedometer
- `adaptive` - Adaptive-threshold detector (voloved's `count_steps_simple`)

#### Calibration Results

The table below compares the balanced error (lower is better) of every
algorithm across all recording sets, as produced by `summary.py`. The
balanced error weights the walking (step-count) error against false steps
detected during non-walking activity.

| Algorithm | l1-12hz-bw2 | l2-12hz-bw2 | l2-25hz-bw2 | l2-25hz-bw4 | Mean |
|-----------|------------:|------------:|------------:|------------:|-----:|
| **threshold_bound_n** | 22.50 | 13.58 | 12.75 | 9.25 | **14.52** |
| espruino | 17.79 | 30.46 | 16.71 | 15.08 | 20.01 |
| threshold_bound | 24.83 | 28.42 | 16.62 | 17.38 | 21.81 |
| threshold_min | 28.00 | 30.25 | 17.54 | 16.50 | 23.07 |
| threshold_edge | 30.29 | 28.71 | 13.50 | 21.46 | 23.49 |
| threshold_hp8 | 36.08 | 35.79 | 15.67 | 17.83 | 26.34 |
| threshold_hp | 38.96 | 25.21 | 23.96 | 18.88 | 26.75 |
| threshold_min8 | 48.46 | 30.92 | 14.54 | 14.17 | 27.02 |
| threshold_bound8 | 50.96 | 39.71 | 13.58 | 11.08 | 28.83 |
| threshold | 61.79 | 51.00 | 34.25 | 32.00 | 44.76 |
| peak_detect | 64.08 | 50.50 | 30.58 | 35.12 | 45.07 |
| threshold_max | 61.83 | 49.04 | 29.96 | 63.92 | 51.19 |
| threshold_lp | 89.21 | 56.38 | 37.08 | 89.00 | 67.92 |
| adaptive | 87.71 | 78.38 | 68.08 | 64.29 | 74.61 |

Per-set calibration results are stored in [`recordings/`](recordings/) as
one `<set>.yml` file per recording set. Regenerate this comparison with:

```bash
# Balanced error across all sets (as shown above)
python summary.py

# Choose a different metric, or use relative (percentage) errors
python summary.py -m walking_error
python summary.py --relative
```

## Runtime Analysis

The `runtime/` directory contains two benchmarks for measuring on-device
performance: a math benchmark for the low-level operations used by the
detectors, and a step-detector benchmark comparing whole algorithms.

### Math Benchmark

[`math_bench.c`](runtime/math_bench.c) times the primitive operations used
by step-counting algorithms.

- **Absolute Value Functions**: Different implementations based on integer and floating-point code.
- **Norm Functions**: Different implementations, e.g., L1 (Manhattan), L2 (Euclidean) norms.

Benchmarks show that integer operations significantly outperform floating-point calculations on device (No surprise, the ARM Cortex M0+ does not have a FP unit). The L1 norm executes approximately 40 times faster than the L2 norm. An approximate L2 norm calculation provides an effective compromise between computational performance and accuracy for the step detection use case.

### Step-Detector Benchmark

[`step_bench.c`](runtime/step_bench.c) compares the per-sample cost of
three streaming detectors on an identical walking-like magnitude stream.
`threshold_bound_n` is the cheapest (clamp/shift/compare/increment on
non-step samples), `threshold_bound8` is ~4x slower (it runs its
bounded-gap check on every sample), and `espruino` is ~13x the cost of
`bound_n`, dominated by its per-sample FIR and DC filter.

See [`runtime/README.md`](runtime/README.md) for the full function
descriptions, build instructions, and detailed timing results.
