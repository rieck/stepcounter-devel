#!/bin/sh
# Calibrate all algorithms on each recording set and write the results
# to recordings/<set>.yml. Progress bars go to stderr (terminal), so
# only the result blocks land in the .yml files.

for i in l1-12hz-bw2 l2-12hz-bw2 l2-25hz-bw2 l2-25hz-bw4 ; do
    echo "$i"
    ./calibrate.py -c 50000 -d "recordings/$i" all > "recordings/$i.yml"
done
