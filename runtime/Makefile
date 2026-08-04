# Makefile for the runtime benchmarks.
#
# Builds the portable step-detector benchmark (step_bench). It uses only
# the C standard library plus libm, so it compiles on any host toolchain.
#
# Note: math_bench.c is NOT built here -- it targets the SensorWatch
# firmware (watch_rtc_* / watch_utility_* APIs, no main()) and is meant to
# be included in a movement build, not compiled standalone.

CC      ?= cc
CFLAGS  ?= -O2 -Wall
LDLIBS  := -lm

.PHONY: all run clean

all: step_bench

step_bench: step_bench.c
	$(CC) $(CFLAGS) -o $@ $< $(LDLIBS)

run: step_bench
	./step_bench

clean:
	rm -f step_bench
