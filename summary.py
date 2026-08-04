#!/usr/bin/env python3
"""
Summarize Calibration Results

Reads all calibration result files (recordings/*.yml) written by
calibrate.py and prints a unified table comparing every algorithm across
every recording set.

By default it shows the absolute error metrics as stored in the result
files. With --relative it recomputes the walking error as a percentage of
the true step count, which is comparable across recording sets with
different walk lengths (the absolute step error is not).

Copyright (c) 2025 Konrad Rieck. MIT License
"""

import argparse
import ast
from pathlib import Path

# Error metrics available in each result block, in reporting order.
METRICS = [
    "calibration_error",
    "balanced_error",
    "walking_error",
    "non_walking_error",
]


def parse_results(path):
    """Parse a single recordings/<set>.yml result file.

    Returns a dict mapping algorithm name -> dict of fields. Error fields
    are floats; best_parameters is the [params1, params2] list.
    """
    results = {}
    current = None

    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        if line.startswith("- algorithm:"):
            name = line.split(":", 1)[1].strip()
            current = {}
            results[name] = current
        elif current is not None and line.startswith("  "):
            key, _, value = line.strip().partition(":")
            value = value.strip()
            if key == "best_parameters":
                current[key] = ast.literal_eval(value)
            else:
                current[key] = float(value)

    return results


def relative_errors(data_dir, algorithm, best_parameters):
    """Recompute walking/non-walking error from the raw recordings.

    Mirrors the cross-validation in calibrate.py: the two calibrated
    parameter sets are evaluated on the opposite split (params1 -> set2,
    params2 -> set1), so every recording is scored exactly once.

    Returns (walking_pct, non_walking_count):
      - walking_pct:       mean of |pred - true| / true over walking
                           recordings, in percent (comparable across sets).
      - non_walking_count: mean false steps over non-walking recordings
                           (true count is 0, so this stays an absolute
                           count -- there is nothing to normalize by).
    """
    from calibrate import eval_algo, load_data

    set1_data, set2_data = load_data(data_dir)
    params1, params2 = best_parameters

    runs = eval_algo(algorithm, set2_data, params1)["runs"]
    runs += eval_algo(algorithm, set1_data, params2)["runs"]

    walk = [r for r in runs if "walking" in r["data"]]
    non = [r for r in runs if "walking" not in r["data"]]

    walking_pct = (
        100.0
        * sum(abs(r["predicted"] - r["steps"]) / r["steps"] for r in walk)
        / len(walk)
        if walk
        else None
    )
    # For non-walking recordings the true count is 0, so error == predicted.
    non_walking_count = sum(r["predicted"] for r in non) / len(non) if non else None

    return walking_pct, non_walking_count


def parse_args():
    parser = argparse.ArgumentParser(
        description="Summarize calibration results across all recording sets"
    )
    parser.add_argument(
        "-d",
        "--dir",
        type=Path,
        metavar="<dir>",
        default=Path("recordings"),
        help="Directory with result files (default: recordings)",
    )
    parser.add_argument(
        "-m",
        "--metric",
        choices=METRICS,
        default="balanced_error",
        help="Error metric to compare (default: balanced_error)",
    )
    parser.add_argument(
        "-r",
        "--relative",
        action="store_true",
        help="Recompute walking error as %% of true steps (comparable "
        "across sets); non-walking stays an absolute false-step count",
    )
    return parser.parse_args()


def collect(args):
    """Load result files and the union of algorithms, in first-seen order."""
    files = sorted(args.dir.glob("*.yml"))
    if not files:
        raise FileNotFoundError(f"No result files (*.yml) in {args.dir}")

    sets = {path.stem: parse_results(path) for path in files}

    algorithms = []
    for results in sets.values():
        for algo in results:
            if algo not in algorithms:
                algorithms.append(algo)

    return sets, algorithms


def print_table(title, set_names, rows, algo_width, col_width, unit=""):
    """Print one sorted table: algorithm | value per set | mean."""
    header = f"{'algorithm':<{algo_width}}"
    for name in set_names:
        header += f"  {name:>{col_width}}"
    header += f"  {'mean':>{col_width}}"

    print(title)
    print(header)
    print("-" * len(header))

    # Best (lowest mean) first; algorithms with no data sort last.
    rows = sorted(rows, key=lambda row: row[2])
    for algo, values, mean in rows:
        line = f"{algo:<{algo_width}}"
        for value in values:
            cell = "-" if value is None else f"{value:.2f}{unit}"
            line += f"  {cell:>{col_width}}"
        mean_cell = "-" if mean == float("inf") else f"{mean:.2f}{unit}"
        line += f"  {mean_cell:>{col_width}}"
        print(line)


def build_rows(sets, algorithms, value_of):
    """Build (algo, [value per set], mean) rows using value_of(set, algo)."""
    rows = []
    for algo in algorithms:
        values = [value_of(name, algo) for name in sets]
        present = [v for v in values if v is not None]
        mean = sum(present) / len(present) if present else float("inf")
        rows.append((algo, values, mean))
    return rows


def rank_by_mean(rows):
    """Map algorithm -> rank (1 = best/lowest mean) from build_rows output."""
    ordered = sorted(rows, key=lambda row: row[2])
    return {algo: rank for rank, (algo, _, _) in enumerate(ordered, start=1)}


def main():
    args = parse_args()
    sets, algorithms = collect(args)
    set_names = list(sets)

    algo_width = max([len("algorithm")] + [len(a) for a in algorithms])
    col_width = max(10, max(len(n) for n in set_names))

    if not args.relative:
        rows = build_rows(
            sets,
            algorithms,
            lambda name, algo: sets[name].get(algo, {}).get(args.metric),
        )
        print(f"Metric: {args.metric}  (lower is better)")
        print_table("", set_names, rows, algo_width, col_width)
        return

    # Relative mode: recompute from the raw recordings once per (set, algo).
    walk = {}  # (set, algo) -> walking error %
    nonwalk = {}  # (set, algo) -> false-step count
    for name in set_names:
        data_dir = args.dir / name
        for algo, fields in sets[name].items():
            w, n = relative_errors(data_dir, algo, fields["best_parameters"])
            walk[(name, algo)] = w
            nonwalk[(name, algo)] = n

    walk_rows = build_rows(sets, algorithms, lambda name, algo: walk[(name, algo)])
    non_rows = build_rows(sets, algorithms, lambda name, algo: nonwalk[(name, algo)])

    print("Walking error, relative to true steps  (lower is better)")
    print_table("", set_names, walk_rows, algo_width, col_width, unit="%")
    print()
    print("Non-walking error, false steps per recording  (lower is better)")
    print_table("", set_names, non_rows, algo_width, col_width)
    print()

    # Combined view: rank in each table, then average the two ranks. Ranking
    # sidesteps the incompatible units (% vs. count) -- an algorithm that is
    # good on both rises; one that wins a single table by being degenerate
    # (e.g. never firing) is pulled back by its rank in the other.
    walk_rank = rank_by_mean(walk_rows)
    non_rank = rank_by_mean(non_rows)
    combined = []
    for algo in algorithms:
        wr, nr = walk_rank[algo], non_rank[algo]
        combined.append((algo, [float(wr), float(nr)], (wr + nr) / 2))

    print("Combined ranking  (average of walking-% rank and non-walking rank)")
    print_table("", ["walk_rank", "nonwalk_rank"], combined, algo_width, col_width)


if __name__ == "__main__":
    main()
