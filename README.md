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
python calibrate.py threshold-bound

# Calibrate all available algorithms
python calibrate.py all

# Use custom data directory
python calibrate.py -d recordings/l2-25hz threshold
```

#### Algorithms Available

- `threshold` - Basic threshold-based detection
- `threshold-lp` - Threshold with low-pass filtering
- `threshold-hp` - Threshold with high-pass filtering
- `threshold-min/max` - Threshold with step time bounds
- `threshold-bound` - Threshold with min and max bounds
- `threshold-ultra` - Threshold with all of the above
- `peak-detect` - Classic peak detection

#### Calibration Results

| Algorithm | Calibration Error | Evaluation Error | Best Params 1 | Best Params 2 |
|-----------|------------------|------------------|---------------|---------------|
| **threshold_hp** | 23.10 | **23.40** | `{'threshold': 6727, 'win_size': 100}` | `{'threshold': 6515, 'win_size': 7}` |
| **threshold_edge** | 22.70 | **24.20** | `{'min_step': 1, 'threshold': 26606}` | `{'min_step': 1, 'threshold': 26323}` |
| **threshold_bound** | 19.50 | **24.50** | `{'max_step': 18, 'min_step': 1, 'threshold': 26444}` | `{'max_step': 15, 'min_step': 3, 'threshold': 25666}` |
| **threshold_min** | 15.90 | **29.50** | `{'min_step': 3, 'threshold': 27666}` | `{'min_step': 3, 'threshold': 26181}` |
| **threshold_ultra** | 14.70 | **31.50** | `{'max_step': 12, 'min_step': 2, 'threshold': 2454, 'win_hp': 4, 'win_lp': 18}` | `{'max_step': 16, 'min_step': 4, 'threshold': 1161, 'win_hp': 4, 'win_lp': 6}` |
| **peak_detect** | 42.30 | **46.20** | `{'bounce_win': 4, 'detect_win': 100, 'mean_win': 1, 'thres': 1.0}` | `{'bounce_win': 4, 'detect_win': 100, 'mean_win': 7, 'thres': 1.0}` |
| **threshold_max** | 31.90 | **57.60** | `{'max_step': 8, 'threshold': 33888}` | `{'max_step': 11, 'threshold': 30666}` |
| **threshold** | 32.60 | **58.70** | `{'threshold': 34545}` | `{'threshold': 31111}` |
| **threshold_lp** | 33.20 | **65.60** | `{'threshold': 31636, 'win_size': 4}` | `{'threshold': 31030, 'win_size': 1}` |

Calibration results are stored in [`results.yml`](results.yml).

## Runtime Analysis

The `runtime/` directory contains code snippets for measuring the performance of mathematical operations on device.

#### Available Functions

- **Absolute Value Functions**: Different implementations based on integer and floating-point code.
- **Norm Functions**: Different implementations, e.g., L1 (Manhattan), L2 (Euclidean) norms.

#### Runtime Results

Benchmarks show that integer operations significantly outperform floating-point calculations on device (No surprise, the ARM Cortex M0+ does not have a FP unit). The L1 norm executes approximately 40 times faster than the L2 norm. An approximate L2 norm calculation provides an effective compromise between computational performance and accuracy for the step detection use case. See [`runtime/README.md`](runtime/README.md) for detailed results.
