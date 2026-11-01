#!/usr/bin/env bash
# Reproducible v0.6.0 PE32 build and offline validation.
# Doesn't run Alice, Wine, or install drivers.
set -euo pipefail
cd "$(dirname "$0")"
python3 build_from_recipe.py
# The native launchers require GetThreadContext/ActCtx linker aliases; the
# declarative recipe builds these consistently on Windows and Linux.
cp win32/build/a3dapi.dll portable/bin/
cp win32/build/a3dapi.dll dropin/bin/
cp win32/build/a3d.dll portable/bin/
cp win32/build/a3d-comtest.exe portable/bin/
cp remaster2011/alice-a3d2011-bridge.exe portable/bin/
cp classic2000/alice-a3d-bridge.exe portable/bin/
python3 -m unittest discover -s portable/tests -p 'test_*.py' -q
python3 -m unittest discover -s dropin/tests -p 'test_*.py' -q
python3 -m unittest discover -s remaster2011/tests -p 'test_*.py' -q
python3 -m unittest discover -s tools -p 'test_*.py' -q
gcc -O2 -std=c11 -w win32/test_fast24_native.c -lm -o /tmp/a3d_v060_fast24_test
/tmp/a3d_v060_fast24_test
gcc -std=c11 -O2 -ffunction-sections -fdata-sections -Wl,--gc-sections -Wno-attributes \
 remaster2011/tests/test_selector_stub.c -o /tmp/a3d_v060_selector_test
/tmp/a3d_v060_selector_test
gcc -O2 -std=c11 -w win32/test_voice128_native.c -lm -o /tmp/a3d_v060_voice128_test
/tmp/a3d_v060_voice128_test
printf 'All runnable OFFLINE tests passed. This script does not validate games under Wine.\n'
gcc -O2 -std=c11 -w win32/test_geometry_cache_hf9_native.c -lm -o /tmp/a3d_v060_geom_cache_hf9_test
/tmp/a3d_v060_geom_cache_hf9_test

# Regression for Quake III 1.17 sentinel-pointer crash: IA3dList::Call must
# return polygons executed, NOT S_OK (0). Also validates quads vs triangles.
gcc -O2 -std=c11 -w win32/test_list_polygon_count_hf10_native.c -lm -o /tmp/a3d_v060_hf10_list_test
/tmp/a3d_v060_hf10_list_test

# v0.6.2 bounded worker snapshot must render bit-for-bit like full PCM.
gcc -O2 -std=c11 -w win32/test_snapshot_pcm_native.c -lm -o /tmp/a3d_v062_snapshot_pcm_test
/tmp/a3d_v062_snapshot_pcm_test
