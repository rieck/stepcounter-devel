/*
 * Runtime benchmark for step-detection algorithms.
 *
 * Compares the per-sample cost of three streaming step detectors:
 *
 *   - threshold_bound8   rieck/second-movement (stepcounter_face),
 *                        step_counter_face.c::_detect_steps
 *   - espruino           voloved/second-movement PR #191
 *                        (COUNT_STEPS_USE_ESPRUINO): DC-removal EMA +
 *                        7-tap FIR + activity gate + peak + state machine
 *   - threshold_bound_n  generalization of bound8 requiring a streak of N
 *                        consecutive rhythmic steps
 *
 * All three are fed the SAME magnitude stream (a walking-like signal,
 * ~1 g baseline with periodic peaks) and each applies its own internal
 * scaling exactly as on the watch, so the comparison is apples-to-apples
 * on identical input.
 *
 * Portable timing via clock_gettime(CLOCK_MONOTONIC); the detector
 * functions themselves are plain integer C and drop straight into the
 * watch's math_bench.c harness (swap the timer for watch_rtc_*).
 *
 * Build:  cc -O2 -o step_bench step_bench.c -lm
 *
 * Copyright (c) 2025 Konrad Rieck. MIT License, EXCEPT for the espruino
 * detector below (the espruino_* functions and their constants), which is a
 * port of Espruino's libs/misc/stepcount.c, Copyright (c) 2021 Gordon
 * Williams <gw@pur3.co.uk>, and is licensed under the Mozilla Public
 * License, v. 2.0. Because that MPL-2.0 code is combined into this file, the
 * file as a whole is distributed under the terms of the MPL-2.0; see the
 * per-section notice below and LICENSE.MPL for details.
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this file,
 * You can obtain one at http://mozilla.org/MPL/2.0/.
 */

#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define TEST_SAMPLES    200
#define TEST_ITERATIONS 100000   /* repeat the stream very often */
#define TEST_TRIALS     11       /* trials per detector; median reported */

/* Walking-like acceleration magnitude stream (positive, ~8192 == 1 g,
 * sharp peaks ~30000 roughly every 12 samples). */
static const uint32_t mag_stream[TEST_SAMPLES] = {
    8446, 10656, 22106, 30551, 22362, 10792, 8020, 7934, 8546, 7896, 8484, 8550,
    8350, 10631, 22685, 30224, 22113, 10571, 7887, 8015, 8030, 8309, 8408, 7819,
    8366, 10745, 22814, 30457, 22799, 11100, 8221, 8017, 8251, 8395, 8076, 7798,
    8569, 10704, 22795, 30224, 22429, 10826, 7951, 8012, 8573, 8136, 7896, 7886,
    8181, 10640, 22448, 30144, 22699, 10812, 7836, 8539, 8262, 8341, 7919, 8179,
    7872, 11106, 22381, 30435, 22714, 10912, 8383, 7988, 8513, 7863, 7838, 8469,
    8025, 11332, 22377, 29873, 22319, 10645, 8181, 8076, 8256, 8442, 8165, 7958,
    8171, 10905, 22295, 30478, 22354, 11260, 8491, 8455, 7865, 8415, 8442, 7967,
    8338, 11287, 22331, 29959, 22554, 10930, 8068, 8447, 8496, 8362, 8016, 8493,
    8124, 11327, 22875, 29849, 22315, 10574, 8115, 8202, 8066, 7859, 8008, 8372,
    8527, 10864, 22298, 30463, 22592, 10947, 8450, 8261, 7938, 8063, 7934, 8044,
    8554, 11115, 22632, 30061, 22845, 11139, 8230, 8389, 8200, 8162, 8016, 7933,
    8313, 11047, 22174, 30565, 22129, 10654, 7948, 8434, 7955, 8488, 8224, 8402,
    7857, 10935, 22471, 30402, 22560, 11083, 8049, 8358, 7803, 8488, 8530, 7909,
    8490, 11090, 22849, 30065, 22868, 11198, 8140, 7906, 8092, 8237, 7953, 8256,
    7795, 11280, 22817, 30061, 22593, 11322, 7974, 8311, 7900, 8432, 8097, 8446,
    8311, 11164, 22284, 29948, 22463, 11322, 7957, 8344,
};

/* ================================================================= *
 *  1) threshold_bound8  (step_counter_face.c::_detect_steps)
 * ================================================================= */

#define B8_THRESHOLD 100
#define B8_MIN_STEP  10
#define B8_MAX_STEP  20

typedef struct {
    uint32_t steps;
    uint32_t subticks;
    uint32_t last_steps[2];
} bound8_state_t;

static void bound8_init(bound8_state_t *s)
{
    s->steps = 0;
    s->subticks = 0;
    s->last_steps[0] = 0;
    s->last_steps[1] = 0;
}

/* One sample, mirroring the goto-based control flow of the face. */
static void bound8_sample(bound8_state_t *s, uint32_t mag)
{
    /* Clamp to 16 bits and scale down to 8 bits */
    mag = (mag > 0xffff) ? 0xffff : mag;
    mag >>= 8;

    if (mag > B8_THRESHOLD) {
        if (s->subticks - s->last_steps[0] < B8_MIN_STEP)
            goto skip;
        s->steps++;
        s->last_steps[1] = s->last_steps[0];
        s->last_steps[0] = s->subticks;
    }

    if (s->subticks - s->last_steps[0] <= B8_MAX_STEP)
        goto skip;
    if (s->last_steps[0] - s->last_steps[1] <= B8_MAX_STEP)
        goto skip;

    s->steps--;
    s->last_steps[0] = s->last_steps[1];

  skip:
    s->subticks += 1;
}

/* ================================================================= *
 *  2) espruino  (count_steps.c::count_steps_espruino_sample)
 *
 *  Ported from Espruino's libs/misc/stepcount.c (via voloved/second-
 *  movement PR #191), Copyright (c) 2021 Gordon Williams <gw@pur3.co.uk>.
 *  This C port Copyright (c) 2026 Konrad Rieck. Licensed under the Mozilla
 *  Public License, v. 2.0 -- see the file header and LICENSE.MPL. This
 *  section is MPL-covered, not MIT.
 * ================================================================= */

#define ACCELFILTER_TAP_NUM 7
#define NSAMPLE             12   /* DC-removal EMA alpha = 1/NSAMPLE */
#define T_MIN_STEP          4
#define T_MAX_STEP          16
#define X_STEPS             6
#define RAW_THRESHOLD       15
#define N_ACTIVE_SAMPLES    3

static const int8_t esp_taps[ACCELFILTER_TAP_NUM] = {
    -11, -15, 44, 68, 44, -15, -11
};

typedef enum {
    S_STILL = 0, S_STEP_1 = 1, S_STEP_22N = 2, S_STEPPING = 3
} StepState;

typedef struct {
    int8_t   fir_hist[ACCELFILTER_TAP_NUM];
    unsigned fir_last;
    int      dc_total;
    int16_t  accFiltered;
    int16_t  accFilteredHist[2];
    StepState stepState;
    unsigned char holdSteps;
    unsigned char stepLength;
    int      active_sample_count;
    int      gate_open;
    uint32_t steps;
} espruino_state_t;

static void espruino_init(espruino_state_t *s)
{
    for (int i = 0; i < ACCELFILTER_TAP_NUM; i++)
        s->fir_hist[i] = 0;
    s->fir_last = 0;
    s->dc_total = 8192 * NSAMPLE;
    s->accFiltered = 0;
    s->accFilteredHist[0] = 0;
    s->accFilteredHist[1] = 0;
    s->stepState = S_STILL;
    s->holdSteps = 0;
    s->stepLength = 0;
    s->active_sample_count = 0;
    s->gate_open = 0;
    s->steps = 0;
}

static int espruino_had_step(espruino_state_t *s)
{
    switch (s->stepState) {
    case S_STILL:
        s->stepState = S_STEP_1; s->holdSteps = 1; return 0;
    case S_STEP_1:
        s->holdSteps = 1;
        if (s->stepLength <= T_MAX_STEP && s->stepLength >= T_MIN_STEP) {
            s->stepState = S_STEP_22N; s->holdSteps = 2;
        }
        return 0;
    case S_STEP_22N:
        if (s->stepLength <= T_MAX_STEP && s->stepLength >= T_MIN_STEP) {
            s->holdSteps++;
            if (s->holdSteps >= X_STEPS) { s->stepState = S_STEPPING; return X_STEPS; }
        } else {
            s->stepState = S_STEP_1;
        }
        return 0;
    case S_STEPPING:
        if (s->stepLength <= T_MAX_STEP && s->stepLength >= T_MIN_STEP)
            return 1;
        s->stepState = S_STEP_1;
        return 0;
    }
    return 0;
}

static void espruino_sample(espruino_state_t *s, uint32_t accMag)
{
    /* DC-removal EMA */
    s->dc_total += (int) accMag - s->dc_total / NSAMPLE;
    int v = ((int) accMag - s->dc_total / NSAMPLE) >> 5;
    if (v > 127) v = 127;
    if (v < -128) v = -128;

    /* 7-tap FIR */
    s->fir_hist[s->fir_last++] = (int8_t) v;
    if (s->fir_last == ACCELFILTER_TAP_NUM) s->fir_last = 0;
    s->accFilteredHist[0] = s->accFilteredHist[1];
    s->accFilteredHist[1] = s->accFiltered;
    int acc = 0;
    int index = (int) s->fir_last;
    for (int i = 0; i < ACCELFILTER_TAP_NUM; i++) {
        index = index != 0 ? index - 1 : ACCELFILTER_TAP_NUM - 1;
        acc += (int) s->fir_hist[index] * (int) esp_taps[i];
    }
    acc >>= 2;
    if (acc > 32767) acc = 32767;
    if (acc < -32768) acc = 32768;
    s->accFiltered = (int16_t) acc;

    /* Activity gate */
    if (v > RAW_THRESHOLD || v < -RAW_THRESHOLD) {
        if (s->active_sample_count < N_ACTIVE_SAMPLES) s->active_sample_count++;
        if (s->active_sample_count == N_ACTIVE_SAMPLES) s->gate_open = 1;
    } else {
        if (s->active_sample_count > 0) s->active_sample_count--;
        if (s->active_sample_count == 0) s->gate_open = 0;
    }

    if (s->stepLength < 255) s->stepLength++;

    if (s->gate_open &&
        s->accFilteredHist[1] > s->accFilteredHist[0] &&
        s->accFilteredHist[1] > s->accFiltered) {
        s->steps += espruino_had_step(s);
        s->stepLength = 0;
    }
}

/* ================================================================= *
 *  3) threshold_bound_n  (this project's algorithms/threshold-boundn.py)
 * ================================================================= */

#define BN_THRESHOLD 100
#define BN_MIN_STEP  10
#define BN_MAX_STEP  20
#define BN_MIN_STREAK   6

typedef struct {
    int32_t  steps;      /* signed: a short streak is subtracted back out */
    uint32_t index;      /* running sample index */
    uint32_t last_step;
    int32_t  streak_len;
    int      have_step;
} boundn_state_t;

static void boundn_init(boundn_state_t *s)
{
    s->steps = 0;
    s->index = 0;
    s->last_step = 0;
    s->streak_len = 0;
    s->have_step = 0;
}

static void boundn_sample(boundn_state_t *s, uint32_t mag)
{
    mag = (mag > 0xffff) ? 0xffff : mag;
    mag >>= 8;

    if (mag > BN_THRESHOLD) {
        if (!s->have_step || s->index - s->last_step >= BN_MIN_STEP) {
            if (s->have_step && s->index - s->last_step <= BN_MAX_STEP) {
                s->streak_len++;                       /* continues the streak */
            } else {
                if (s->streak_len < BN_MIN_STREAK)        /* drop a short streak */
                    s->steps -= s->streak_len;
                s->streak_len = 1;
            }
            s->steps++;
            s->last_step = s->index;
            s->have_step = 1;
        }
    }
    s->index += 1;
}

/* boundn_sample leaves a trailing streak pending; flush at end of a stream. */
static void boundn_flush(boundn_state_t *s)
{
    if (s->streak_len < BN_MIN_STREAK)
        s->steps -= s->streak_len;
    s->streak_len = 0;
}

/* ================================================================= *
 *  Timing harness
 * ================================================================= */

static double now_ms(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec * 1000.0 + ts.tv_nsec / 1e6;
}

#define TOTAL_SAMPLES ((double) TEST_SAMPLES * TEST_ITERATIONS)

/* Each bench_* runs TEST_TRIALS trials, filling times[] (ms per trial)
 * and the final step-count sink (to defeat dead-code elimination). */
static void bench_bound8(double *times, uint32_t *sink)
{
    for (int t = 0; t < TEST_TRIALS; t++) {
        bound8_state_t st;
        bound8_init(&st);
        double t0 = now_ms();
        for (uint32_t it = 0; it < TEST_ITERATIONS; it++)
            for (int j = 0; j < TEST_SAMPLES; j++)
                bound8_sample(&st, mag_stream[j]);
        times[t] = now_ms() - t0;
        *sink = st.steps;
    }
}

static void bench_espruino(double *times, uint32_t *sink)
{
    for (int t = 0; t < TEST_TRIALS; t++) {
        espruino_state_t st;
        espruino_init(&st);
        double t0 = now_ms();
        for (uint32_t it = 0; it < TEST_ITERATIONS; it++)
            for (int j = 0; j < TEST_SAMPLES; j++)
                espruino_sample(&st, mag_stream[j] << 1);   /* prod. scaling */
        times[t] = now_ms() - t0;
        *sink = st.steps;
    }
}

static void bench_boundn(double *times, uint32_t *sink)
{
    for (int t = 0; t < TEST_TRIALS; t++) {
        boundn_state_t st;
        boundn_init(&st);
        double t0 = now_ms();
        for (uint32_t it = 0; it < TEST_ITERATIONS; it++)
            for (int j = 0; j < TEST_SAMPLES; j++)
                boundn_sample(&st, mag_stream[j]);
        boundn_flush(&st);
        times[t] = now_ms() - t0;
        *sink = (uint32_t) st.steps;
    }
}

static int cmp_double(const void *a, const void *b)
{
    double d = *(const double *) a - *(const double *) b;
    return (d > 0) - (d < 0);
}

/* Median (robust central estimate) plus mean/min/stddev of the trials. */
static double median_ms(double *times)
{
    qsort(times, TEST_TRIALS, sizeof(double), cmp_double);
    return (TEST_TRIALS & 1)
        ? times[TEST_TRIALS / 2]
        : 0.5 * (times[TEST_TRIALS / 2 - 1] + times[TEST_TRIALS / 2]);
}

static void report(const char *name, double *times, double base_median, uint32_t sink)
{
    double med = median_ms(times);   /* sorts times[] */
    double sum = 0.0;
    for (int t = 0; t < TEST_TRIALS; t++)
        sum += times[t];
    double mean = sum / TEST_TRIALS;
    double var = 0.0;
    for (int t = 0; t < TEST_TRIALS; t++)
        var += (times[t] - mean) * (times[t] - mean);
    double sd = (TEST_TRIALS > 1) ? sqrt(var / (TEST_TRIALS - 1)) : 0.0;
    double ns_per_sample = med * 1e6 / TOTAL_SAMPLES;

    printf("  %-18s median %7.2f ms  (mean %7.2f, min %7.2f, sd %5.2f)  "
           "%5.2f ns/sample  %5.2fx  (steps=%lu)\n",
           name, med, mean, times[0], sd, ns_per_sample,
           med / base_median, (unsigned long) sink);
}

int main(void)
{
    uint32_t s8 = 0, se = 0, sn = 0;
    double t8[TEST_TRIALS], te[TEST_TRIALS], tn[TEST_TRIALS];

    printf("Benchmarking step detectors "
           "(%d samples x %d iter x %d trials; median reported)\n",
           TEST_SAMPLES, TEST_ITERATIONS, TEST_TRIALS);

    bench_boundn(tn, &sn);
    bench_bound8(t8, &s8);
    bench_espruino(te, &se);

    /* boundn median as the 1.00x baseline for the relative column */
    double base = median_ms(tn);   /* sorts tn[]; report() re-sorts harmlessly */

    report("threshold_bound_n", tn, base, sn);
    report("threshold_bound8",  t8, base, s8);
    report("espruino",          te, base, se);

    return 0;
}
