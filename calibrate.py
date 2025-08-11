#!/usr/bin/env python3
"""
Calibrate Step Detection Algorithms

This script calibrates step detection algorithms by finding the best
parameters for a given algorithm.
"""

import argparse
import json
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import ParameterGrid
from tqdm import tqdm

from algorithms.registry import detectors


def convert_numpy_types(obj):
    """Convert numpy types to native Python types recursively"""
    if isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return obj


def parse_args():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Grid search for step detection")
    parser.add_argument(
        "-d",
        "--data-dir",
        type=Path,
        metavar="<dir>",
        default=Path("recordings/l2-12hz"),
        help="Directory with recordings (default: recordings/l2-12hz)",
    )
    parser.add_argument(
        "algorithms",
        type=str,
        nargs="+",
        metavar="<algo>",
        help=f"Algorithms to calibrate. Available: {list(detectors.keys())}",
    )

    args = parser.parse_args()

    # Check for valid data directory with split.json
    if not (args.data_dir / "split.json").exists():
        raise FileNotFoundError(f"No valid data directory: {args.data_dir}")

    # Check for valid algorithms
    if "all" in args.algorithms:
        args.algorithms = list(detectors.keys())
    else:
        invalid = [algo for algo in args.algorithms if algo not in detectors]
        if invalid:
            raise ValueError(f"Invalid algorithms: {invalid}")

    return args


def load_data(data_dir):
    """Load data into memory"""
    split = json.load(open(data_dir / "split.json", "r"))
    calib_data, eval_data = [], []

    for fname in split["calibration"]:
        data = pd.read_csv(data_dir / fname)
        true_steps = int(data.iloc[0]["Steps"])
        mag_series = data["Magnitude"].astype(float)
        calib_data.append((mag_series, true_steps, fname))

    for fname in split["evaluation"]:
        data = pd.read_csv(data_dir / fname)
        true_steps = int(data.iloc[0]["Steps"])
        mag_series = data["Magnitude"].astype(float)
        eval_data.append((mag_series, true_steps, fname))

    return calib_data, eval_data


def get_param_grid(algo_name):
    """Get parameter grid for the specified algorithm"""
    detector_class = detectors[algo_name]
    param_grid = detector_class.get_param_grid()

    # Convert numpy types to native Python types
    converted_grid = []
    for params in ParameterGrid(param_grid):
        converted_params = convert_numpy_types(params)
        converted_grid.append(converted_params)
    return converted_grid


def eval_algo(algo_name, data, params):
    """Evaluate the algorithm on the data with the given parameters"""
    detector_class = detectors[algo_name]
    detector = detector_class(**params)

    runs = []
    for mag_series, true_steps, fname in data:
        steps = detector.detect_steps(mag_series)
        runs.append(
            {
                "data": fname,
                "steps": true_steps,
                "predicted": steps,
                "error": abs(steps - true_steps),
            }
        )

    return {
        "error_mean": float(np.mean([run["error"] for run in runs])),
        "error_std": float(np.std([run["error"] for run in runs])),
        "runs": runs,
        "params": params,
    }


def main():
    """Main function"""
    args = parse_args()
    calib_data, eval_data = load_data(args.data_dir)

    # Loop through all algorithms
    for algorithm in args.algorithms:
        param_grid = get_param_grid(algorithm)
        best_params = None
        best_error = float("inf")

        # Parallel evaluation with progress bar
        with ProcessPoolExecutor() as executor:
            # Submit all parameter combinations for evaluation
            future_to_params = {
                executor.submit(eval_algo, algorithm, calib_data, params): params
                for params in param_grid
            }

            # Process completed evaluations with progress bar
            for future in tqdm(
                as_completed(future_to_params),
                total=len(param_grid),
                desc=f"Calibrating {algorithm}",
                leave=False,
            ):
                params = future_to_params[future]
                try:
                    results = future.result()

                    if results["error_mean"] < best_error:
                        best_error = results["error_mean"]
                        best_params = params
                except Exception as e:
                    print(f"Error evaluating parameters {params}: {e}")
                    continue

        # Evaluate best parameters on evaluation data
        results = eval_algo(algorithm, eval_data, best_params)
        print(f"- algorithm: {algorithm}")
        print(f"  best_param: {best_params}")
        print(f"  calib_error: {best_error:.2f}")
        print(f"  eval_error: {results['error_mean']:.2f}")


if __name__ == "__main__":
    main()
