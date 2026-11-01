# v0.6.1 Maximum non-clipping master gain deployment

The 32-bit PE `a3dapi.dll` in v0.6.1 *already* used master gain 5.0 by default in `win32/stream_core.h`, `win32/stream_winmm.inc`, and `win32/a3dapi.c`. All launchers in `profiles/` are now changed from explicit `1.0` to explicit `5.0` by default, with an environment override still supported.

The stereo-linked sample-peak limiter in `win32/stream_core.h` uses an approximately 0.95 full-scale ceiling. This prevents digital sample saturation in the software mixer's output but is **not** a true-peak / lookahead / analog SPL limiter. Heavy limiting may cause audible pumping, coloration or reduced dynamics. These changes have not been auditioned on Windows or Wine.

The DLLs are unchanged from the previous candidate; no unnecessary renderer-code change or untested rebuild was made. See `profiles/` for six corrected launchers and `tools/test_max_gain_profiles.py` / `tools/test_max_gain_nonclip_native.c` for offline tests.

For native Windows: set `A3D_MASTER_GAIN=1.0` before executing `RUN_A3D_WINDOWS.cmd` if a quieter setting is desired.
For Linux/Wine: `A3D_MASTER_GAIN=1.0 bash RUN_A3D_WINE.sh`.

Always reduce physical headphone/speaker volume before starting at maximum gain.

Rebuild everything with `python3 build_from_recipe.py`. The Windows loader timestamp may vary between link invocations; binary code and data remain identical in a verified v0.6.1 rebuild. Run `bash TEST_MAX_GAIN_OFFLINE.sh` for the new gain tests. Running the whole legacy tools suite from an unbuilt source extraction may require the bundled prebuilt Quake III lock-test probe in `win32/build/`.
