# Important functions and what to preserve

This is a curated guide to high-risk paths, **not** a generated one-line
restatement of every function. The source itself remains authoritative.

| Function or state | File | Role / review invariant |
|---|---|---|
| `DllGetClassObject`, root QueryInterface functions | `win32/a3dapi.c` | COM activation, GUID and vtable identity; preserve slot order and HRESULTs |
| `logline`, `a3d_log_enabled` | `win32/a3dapi.c` | Opt-in, bounded diagnostics; do not add to realtime worker |
| `sr_lock` / `sr_unlock` | `win32/source_probe.inc` | Game DMA sample publication and lock ownership; reject invalid re-entry |
| `sr_play`, `sr_stop`, `sr_setwavepos` | `win32/source_probe.inc` | Source lifecycle, cursor updates and serial invalidation |
| `lspos`, listener orientation setters | `win32/listener_trace.inc` | Preserve game-provided listener coordinates |
| `g_Begin`, `g_Vertex3f`, transform methods | `win32/geom_trace.inc` | Scene construction/transform semantics; not all features implemented |
| `a3dmix_init`, `a3dmix_add`, `a3dmix_remove` | `win32/stream_core.h` | DSP defaults, 128 bounded voice slots, address-stable source registration |
| `a3dmix_sample_at` | `win32/stream_core.h` | Bounds-check ring and captured-window sample reads |
| `a3dmix_short_sfx_envelope` | `win32/stream_core.h` | Sub-millisecond envelope for eligible short nonlooping sources only |
| `a3dmix_render` | `win32/stream_core.h` | Audio processing, clipping limiter and interleaved output |
| `mix_sample_playback_position` | `win32/stream_winmm.inc` | Advisory WinMM query, position-format validation, never seek |
| `mixer_thread_run` | `win32/stream_winmm.inc` | Header ownership, worker/probe cadence, PCM submission |
| `mix_render_snapshot` | `win32/stream_winmm.inc` | Offline snapshot/commit, source-id & serial stale-commit checks |
| `mixer_shutdown` | `win32/stream_winmm.inc` | Worker join, device/header teardown; avoid lock-wait deadlocks |
| Provider enum/open wrappers + `a3d2_alias` | `Alice2011_NameFix_v089/miles_selection_v089.c` | Genuine A3D2 handle with post-open name-buffer update |
| `build_engine.py`, `build_proxy_from_export_map.py` | `scripts/`, `Alice2011_NameFix_v089/` | Reproducible Win32 core and vendor-free proxy build |
| `install` / `rollback` | `Tools/aufake3d.py` | Guarded game-local copies, checksums and reversible backups |

## Critical coupling

`stream_winmm.inc`, `source_probe.inc` and `listener_trace.inc` share a
translation unit and mutable mixer state; a seemingly local change can create
a cross-thread lifetime race. The WaveOut completion path owns hardware
buffers, while the PCM source lock/unlock path owns game-writable sample data.
Do not conflate these two independent ownership domains.

The nearest practical tests for each area live in `tests/`,
`release_tests/`, `Source/Engine/acoustics/tests/` and the historical
Windows game suites. None replaces an actual Win32 game run.
