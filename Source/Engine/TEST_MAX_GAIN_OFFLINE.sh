#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$(realpath -- "$0")")"
python3 -m unittest -q tools.test_max_gain_profiles
${CC:-gcc} -O2 -std=c11 -w tools/test_max_gain_nonclip_native.c -lm -o /tmp/a3d_maxgain_test
/tmp/a3d_maxgain_test
