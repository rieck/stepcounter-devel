
One run 100 or 90 but actually 96
One run 50 but actually 46

## Hand-motion recordings (2026-08-12)

Sustained hand movement at walking-like amplitude and cadence: dishwasher,
dressing, shoe-laces. Recorded to cover the false-positive case the desk- and
pc-working files miss, where the wrist oscillates near step frequency.

These are counted as non-walking (no "walking" in the filename), but three of
them carry a non-zero label because some real steps were taken during the
activity: dishwasher1 = 14, dishwasher2 = 18, dressing2 = 6.

Two dumps needed repair before parsing; the .b64 files here are the repaired
versions and reparse to the CSVs as they stand:

- shoe-laces1: a stale 19-byte session (empty, accelerometer still powered
  down) preceded the real one in log.scl. Removed.
- dishwasher2: the trailing 0xff marker and step count were missing, since the
  labeling page was left without pressing MODE. Data was complete; the label
  (18) was appended by hand.
