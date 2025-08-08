#!/usr/bin/env python3
"""
Grid Search for Step Detection Algorithms

This script performs grid search over different parameters for step detection algorithms
and evaluates their performance against ground truth step counts from CSV files.
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import ParameterGrid
from tqdm import tqdm


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


class BaselineDetector(BaseDetector):
    """Baseline step detector that returns a number based on sequence length."""

    def __init__(self, scale=0.1, **params):
        super().__init__(scale=scale, **params)
        self.scale = scale

    def detect_steps(self, mag_series):
        # Detect steps based on sequence length
        return max(0, int(len(mag_series) * self.scale))

    @classmethod
    def get_param_grid(cls):
        return {"scale": np.logspace(-10, -1, 100)}


class ThresholdDetector(BaseDetector):
    """Threshold detector that counts steps above a magnitude threshold."""

    def __init__(self, threshold=1000, **params):
        super().__init__(threshold=threshold, **params)
        self.threshold = threshold

    def detect_steps(self, mag_series):
        # Count steps above threshold
        return int(np.sum(mag_series > self.threshold))

    @classmethod
    def get_param_grid(cls):
        return {"threshold": np.logspace(2, 5, 100)}


# Detector registry
detectors = {
    "baseline": BaselineDetector,
    "random": RandomDetector,
    "threshold": ThresholdDetector,
}


class StepEvaluator:
    """Evaluator for step detection algorithms."""

    def __init__(self, algo_name):
        # Initialize evaluator
        self.algo_name = algo_name
        self.detector_class = self._get_detector_class()

    def _get_detector_class(self):
        # Get the detector class based on name
        if self.algo_name not in detectors:
            raise ValueError(f"Unknown algorithm: {self.algo_name}")

        return detectors[self.algo_name]

    def load_csv_data(self, csv_file):
        # Load magnitude data and ground truth step count from CSV file
        df = pd.read_csv(csv_file)

        # Get ground truth steps from the first row
        true_steps = int(df.iloc[0]["Steps"])

        # Get magnitude series
        mag_series = df["Magnitude"].astype(float)

        return mag_series, true_steps

    def eval_series(self, csv_file, params):
        # Evaluate algorithm on a single CSV file
        mag_series, true_steps = self.load_csv_data(csv_file)

        # Initialize detector with parameters
        detector = self.detector_class(**params)

        # Detect steps
        pred_steps = detector.detect_steps(mag_series)

        return {
            "file": str(csv_file),
            "steps": true_steps,
            "predicted": pred_steps,
            "error": abs(pred_steps - true_steps) / max(true_steps, 1),
            "length": len(mag_series),
        }

    def eval_dataset(self, csv_files, params):
        # Evaluate algorithm on all CSV files with given parameters
        results = []

        for csv_file in csv_files:
            result = self.eval_series(csv_file, params)
            results.append(result)

        # Aggregate metrics
        errors = [r["error"] for r in results]

        return {
            "params": params,
            "num_files": len(results),
            "error_mean": np.mean(errors),
            "error_std": np.std(errors),
            "results": results,
        }


def find_csv_files(data_dir):
    # Find all CSV files in the data directory
    csv_files = list(data_dir.rglob("*.csv"))
    print(f"Found {len(csv_files)} CSV files in {data_dir}")
    return csv_files


def get_param_grid(algo_name):
    # Get parameter grid for the specified algorithm
    if algo_name in detectors:
        detector_class = detectors[algo_name]
        param_grid = detector_class.get_param_grid()
        return list(ParameterGrid(param_grid))
    else:
        # Default parameter grid for other algorithms
        return []


def parse_args():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Grid search for step detection")
    parser.add_argument(
        "-d",
        "--data-dir",
        type=Path,
        default=Path("recordings"),
        help="Directory containing CSV files (default: recordings)",
    )
    parser.add_argument(
        "-a",
        "--algorithm",
        type=str,
        default="baseline",
        help="Algorithm name (default: baseline)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output JSON file for results(default: None)",
    )

    return parser.parse_args()


def main():
    """Main function."""
    args = parse_args()

    # Find CSV files
    csv_files = find_csv_files(args.data_dir)

    # Initialize evaluator
    evaluator = StepEvaluator(args.algorithm)

    # Get parameter grid
    param_grid = get_param_grid(args.algorithm)
    print(f"Testing {len(param_grid)} parameter combinations")

    # Perform grid search
    all_results = []
    best_result = None
    best_score = float("inf")

    for params in tqdm(param_grid, desc="Grid search"):
        result = evaluator.eval_dataset(csv_files, params)
        all_results.append(result)

        # Track best result (lowest error)
        if "error_mean" in result:
            if result["error_mean"] < best_score:
                best_score = result["error_mean"]
                best_result = result

    # Prepare final results
    final_results = {
        "algorithm": args.algorithm,
        "data_directory": str(args.data_dir),
        "num_files": len(csv_files),
        "grid_size": len(param_grid),
        "best_params": best_result["params"] if best_result else None,
        "best_error": best_score if best_result else None,
        "all_results": all_results,
    }

    # Print summary to stdout
    print(f"\nGrid Search Results for {args.algorithm}")
    print("=" * 50)
    print(f"Data directory: {args.data_dir}")
    print(f"Number of CSV files: {len(csv_files)}")
    print(f"Parameter combinations tested: {len(param_grid)}")

    print(f"\nBest parameters: {best_result['params']}")
    print(f"Best error: {best_result['error_mean']:.2%}")

    # Write results to JSON file
    if args.output:
        with open(args.output, "w") as f:
            json.dump(final_results, f, indent=2)


if __name__ == "__main__":
    main()
