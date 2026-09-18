#!/usr/bin/env bash
# Public entry point. Run from the subject workspace root; requires Python 3.8+.
# check/recall report evidence drift, not the truth of a recorded conclusion.
set -eu
exec python3 "$(cd -- "$(dirname -- "$0")" && pwd)/icm_records.py" "$@"
