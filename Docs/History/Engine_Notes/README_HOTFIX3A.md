# A3D v0.6.0 Hotfix 3a — HRTF 24-tap diagnostic correction

Read `portable/README_FAST24_HF3A.md`. It explains the 24-tap silence,
installation commands and test settings. This change is **not** a claim that
Quake III's remaining stream stuttering has been resolved.

Code changes:
- `win32/hrtf_fast24_window.h` (new 710-direction per-window table)
- `win32/stream_core.h` (24-tap selection and direction-change crossfade)
- `win32/test_fast24_native.c` (offline PCM impulse smoke test)
- `tools/test_fast24_windows.py` (all 710 direction windows verified)

48- and 96-tap modes, WaveOut, COM ABI, both Alice bridges and the installer
behave as before Hotfix 3a (but are rebuilt from this source archive).
