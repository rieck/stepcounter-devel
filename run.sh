#!/bin/sh
# Calibrate all algorithms on the recording set and write the results to
# recordings/<set>.yml. Progress bars go to stderr (terminal), so only the
# result blocks land in the .yml file.
#
# Only l2-25hz-bw4 is calibrated: it is the set carrying the hand-motion
# recordings (dishwasher, dressing, shoe-laces). The other sets are kept for
# reference but no longer tracked, as their results predate both those
# recordings and the current error metric.
#
# Set PYTHON to pick the interpreter; the default resolves from PATH, so on a
# cluster either activate the virtualenv or run e.g.
#
#     PYTHON=/path/to/venv/bin/python ./run.sh

set -e

PYTHON="${PYTHON:-python3}"
MAX_COMBI="${MAX_COMBI:-50000}"

# Fail early with a clear message rather than part-way into the grid search
"$PYTHON" -c 'import numpy, pandas, sklearn, tqdm' || {
    echo "error: $PYTHON is missing dependencies, see pyproject.toml" >&2
    exit 1
}

i=l2-25hz-bw4
echo "$i"

# Write to a temporary file and move it into place only on success, so a
# failed or interrupted run leaves the previous results intact.
"$PYTHON" calibrate.py -c "$MAX_COMBI" -d "recordings/$i" all > "recordings/$i.yml.tmp"
mv "recordings/$i.yml.tmp" "recordings/$i.yml"
