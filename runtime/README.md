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
