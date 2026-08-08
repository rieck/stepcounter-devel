# Run-Time Benchmarks

## Math Benchmark

The file [`math_bench.c`](math_bench.c) implements math functions commonly used in step-counting algorithms, including absolute value functions and different vector norms.

### Absolute Value Functions

- `int_abs()`
  Uses the default integer function `abs` provided by the C enviromment

- `float_abs()`
  Uses the default floating-point function `fabs` provided by the C  enviromment.

- `bitwise_abs()`
  Branchless implementation using bit shifts and XOR.  

- `branch_abs()`
  Uses an `if` statement to check the sign and negate if negative.  

### Norm Functions

- `plain_l2_norm()`
  Calculates the exact Euclidean (L2) norm:  `sqrt(x^2 + y^2 + z^2)`.  

- `plain_l1_norm()`
  Computes the Manhattan (L1) norm: `abs(x) + abs(y) + abs(z)`.  

- `approx_l2_norm()`
  Fast approximation of the Euclidean norm using integer operations  

### Results

Results for the absolute value functions on the SensorBoard Pro. Each function is evaluated for 200 random numbers, with the measurement repeated 10,000 times.

```console
Benchmarking abs (200x10000)
  int_abs():  4 s
  float_abs(): 30 s
  bitwise_abs(): 5 s
  branch_abs(): 4 s
```

Results for the norm functions on the SensorBoard Pro. Each function is evaluated for 200 random numbers, with the measurement repeated 10,000 times.

```console
Benchmarking norm (200x10000)
  plain_l2_norm(): 364
  approx_l2_norm(): 14 s
  plain_l1_norm(): 9 s
```

## Step-Detector Benchmark

The file [`step_bench.c`](step_bench.c) compares the per-sample runtime of
three streaming step detectors. All three are fed the *same* walking-like
magnitude stream (≈1 g baseline with periodic peaks) and each applies its
own internal scaling exactly as on the watch, so the comparison is
apples-to-apples on identical input.

- `threshold_bound8`
  From `rieck/second-movement` (`stepcounter_face` branch),
  `step_counter_face.c::_detect_steps`. Per sample: clamp/`>>8`, one
  threshold compare, and a bounded-gap check against the last two step
  positions. Integer-only.

- `espruino`
  From `voloved/second-movement` PR #191 (`COUNT_STEPS_USE_ESPRUINO`),
  `count_steps_espruino_sample` (ports gfwilliams/step-count). Per sample:
  DC-removal EMA + **7-tap FIR** + activity gate + peak detection + a
  4-state machine. Structurally the heaviest.

- `threshold_bound_n`
  This project's `algorithms/threshold-boundn.py`, ported to C.
  Generalizes `bound8` to require a streak of *N* consecutive rhythmic
  steps, tracked with a single streak-length counter (no history buffer).

### Build & Run

```console
make        # builds step_bench
make run    # builds and runs
```

(or directly: `cc -O2 -Wall -o step_bench step_bench.c -lm`). The detector
functions are plain integer C and drop straight into the on-watch
`math_bench.c` harness (swap `clock_gettime` for `watch_rtc_*`).

### Results

Each detector processes a 200-sample stream 100,000 times, over 11 trials.
The **median** trial is reported (mean, min and standard deviation are
printed alongside so the spread is visible). Numbers below are from a
desktop (Apple Silicon, `-O2`); the watch's Cortex-M0+ is far slower in
absolute terms and the `espruino` gap widens further there (per-sample FIR
multiplies, no pipelining), but the relative ordering holds.

```console
Benchmarking step detectors (200 samples x 100000 iter x 11 trials; median reported)
  threshold_bound_n  median    6.85 ms  (mean    6.87, min    6.83, sd  0.04)   0.34 ns/sample   1.00x
  threshold_bound8   median   26.39 ms  (mean   26.38, min   26.27, sd  0.07)   1.32 ns/sample   3.85x
  espruino           median   87.10 ms  (mean   86.96, min   86.46, sd  0.30)   4.36 ns/sample  12.72x
```

`threshold_bound_n` is the cheapest: on non-step samples its only work is
clamp/shift/compare/increment, whereas `bound8` runs its bounded-gap
removal check on *every* sample. `espruino` is ~13x the cost of `bound_n`
(~3x of `bound8`), dominated by the per-sample FIR and DC filter. The exact
multiplier drifts with machine load (an earlier run under load showed
~17x); the relative ordering is stable.
