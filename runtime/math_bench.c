#include <math.h>

#define TEST_ITERATIONS 10000
#define TEST_NUMBERS 200
int32_t test_numbers[200] = {
    24741, 13699, 24989, -12175, 21274, -30947, -32625, 27295, 24247, -5223, -5552, -10419, -26207, -27114, -25115,
    -3296, 5760, -15892, 6158, -6602, 5451, 18266, 20402, -4077, -32085, 19546, 5488, 23328, -11613, -6605, 9712,
    20642, -19122, 23569, -30113, -21690, -10262, 4603, 1187, 26816, -4638, 28149, 27183, -7469, 30559, 968, -21694,
    3741, -23088, -2942, -15426, -8147, -20479, -3524, -17129, -17963, -31049, 16634, 8757, 19799, 16741, -24958,
    26424, 5330, -13932, -6108, -30815, 20652, -1075, -1494, -16270, -17142, -25751, 20365, -29265, 3403, -3217,
    -4159, -18202, -14236, 1979, -16908, -13360, -16258, -11628, 20953, 13165, 7978, 31725, -5619, -16643, -22243,
    5490, -32608, -27323, 6974, 19704, -724, 3542, 24464, -16596, 14500, 27863, -27643, -15381, 9152, 3449, -18590,
    -11164, 7881, 27824, 23208, -28216, 6355, -28457, 107, -1802, -4008, 29180, -16017, 10172, 2281, -30659, -14731,
    -15532, 13732, 30682, 26027, -3573, 8125, 4063, 3941, 23595, 8252, 18228, 6161, -14150, -5850, 12070, -27464,
    17585, 29966, -10288, -27312, 7720, 2221, 26781, -814, 384, -13392, 13000, 23889, 3699, 2251, 15048, -1179,
    -23020, 8740, -31915, -3077, 14376, 15511, -20249, -18929, -21649, 9129, -23618, -757, -5955, -30846, -7773,
    13434, 4802, 20968, 16861, 22788, 30274, 4407, 16505, -20680, 15544, -30036, -25073, -29159, 23138, 20034,
    24223, 12773, 23345, 7039, 24129, -28560, -8883, -31355, -25361, 7952, 9353, -23833, -7002, 16457
};

/* Original C abs() implementation */
static uint32_t int_abs(int32_t x)
{
    return abs(x);
}

/* Bitwise abs() implementation */
static uint32_t bitwise_abs(int32_t x)
{
    int32_t mask = x >> 31;
    return (x ^ mask) - mask;
}

/* Original C fabs() implementation */
static uint32_t float_abs(int32_t x)
{
    return (int32_t) fabs((float) x);
}

/* Branch-based abs() implementation */
static uint32_t branch_abs(int32_t x)
{
    return (x < 0) ? -x : x;
}

static uint32_t _benchmark_abs_fn(uint32_t(*abs_fn) (int32_t))
{
    watch_date_time_t dt = watch_rtc_get_date_time();
    uint32_t start_ts = watch_utility_date_time_to_unix_time(dt, 0);

    volatile uint32_t result = 0;
    for (uint32_t i = 0; i < TEST_ITERATIONS; i++) {
        for (uint16_t j = 0; j < TEST_NUMBERS; j++) {
            result += abs_fn(test_numbers[j]);
        }
    }

    dt = watch_rtc_get_date_time();
    uint32_t end_ts = watch_utility_date_time_to_unix_time(dt, 0);
    return end_ts - start_ts;
}

/* Plain l2 norm */
static uint32_t plain_l2_norm(int32_t *x)
{
    return sqrt(x[0] * x[0] + x[1] * x[1] + x[2] * x[2]);
}

/* Plain l1 norm */
static uint32_t plain_l1_norm(int32_t *x)
{
    return abs(x[0]) + abs(x[1]) + abs(x[2]);
}

/* Approximate l2 norm */
static uint32_t approx_l2_norm(int32_t *x)
{
    /* Absolute values */
    uint32_t ax = abs(x[0]);
    uint32_t ay = abs(x[1]);
    uint32_t az = abs(x[2]);

    /* *INDENT-OFF* */
    /* Sort values: ax >= ay >= az */
    if (ax < ay) { uint32_t t = ax; ax = ay; ay = t; }
    if (ay < az) { uint32_t t = ay; ay = az; az = t; }
    if (ax < ay) { uint32_t t = ax; ax = ay; ay = t; }
    /* *INDENT-ON* */

    /* Approximate sqrt(x^2 + y^2 + z^2) */
    /* alpha ≈ 0.9375 (15/16), beta ≈ 0.375 (3/8) */
    return ax + ((15 * ay) >> 4) + ((3 * az) >> 3);
}

static uint32_t _benchmark_norm_fn(uint32_t(*norm_fn) (int32_t *))
{
    watch_date_time_t dt = watch_rtc_get_date_time();
    uint32_t start_ts = watch_utility_date_time_to_unix_time(dt, 0);

    volatile uint32_t result = 0;
    for (uint32_t i = 0; i < TEST_ITERATIONS; i++) {
        for (uint32_t j = 0; j < TEST_NUMBERS - 3; j++) {
            result += norm_fn(test_numbers + j);
        }
    }

    dt = watch_rtc_get_date_time();
    uint32_t end_ts = watch_utility_date_time_to_unix_time(dt, 0);
    return end_ts - start_ts;
}

static void _benchmark_abs() {
    printf("Benchmarking abs (%dx%d)\n", TEST_NUMBERS, TEST_ITERATIONS);
    printf("  int_abs(): %lu s\n", _benchmark_abs_fn(int_abs));
    printf("  bitwise_abs(): %lu s\n", _benchmark_abs_fn(bitwise_abs));
    printf("  float_abs(): %lu s\n", _benchmark_abs_fn(float_abs));
    printf("  branch_abs(): %lu s\n", _benchmark_abs_fn(branch_abs));
}

static void _benchmark_norm() {
    printf("Benchmarking norm (%dx%d)\n", TEST_NUMBERS, TEST_ITERATIONS);
    printf("  plain_l2_norm(): %lu s\n", _benchmark_norm_fn(plain_l2_norm));
    printf("  approx_l2_norm(): %lu s\n", _benchmark_norm_fn(approx_l2_norm));
    printf("  plain_l1_norm(): %lu s\n", _benchmark_norm_fn(plain_l1_norm));
}
