# Aureal A3D software compatibility wrapper v0.6.9 — unified three-game candidate

**Status:** PE32 binaries and offline Windows/Wine launcher tests are built and verified. The same 6×256 audio settings have been user-tested on Windows: Alice 2000 in v0.6.6, and Alice 2011 and Quake III in v0.6.8 (the latter via the optional 32ms test launcher). This freshly rebuilt v0.6.9 distribution itself has not yet been tested in retail gameplay. Debian 13/Wine gameplay is still unverified. All three games must be tested on the intended machines before calling this production-stable.

## Architecture: one shared engine

One `win32/a3dapi.c`/`win32/a3d.dll` engine, 48-tap HRTF, spatial geometry, WaveOut queue, snapshot option, limiter and source codebase. Game-specific activation bridges and runtime launch profiles are maintained separately, but **there are not three independently maintained DSP engines**. Both shared DLLs are byte-identical across the three distribution folders. Authoritative settings reside in `config/game_profiles_v069.json`, with generated launchers from `tools/generate_launchers_v069.py`.

## Game audio defaults

| Game | Renderer | Header configuration | Nominal queue capacity | Validation |
|---|---|---|---|---|
| Alice 2000 | Off-lock snapshots | **6 × 256**, fixed | **32 ms** | Previously user-tested clean on Windows (tower2, hedge1, hedge2) |
| Alice 2011 + VorpalFix 4.2.1 | Legacy | **6 × 256**, fixed | **32 ms** | User-reported working great under Windows v0.6.8 |
| Quake III Arena 1.17 | Off-lock snapshots | **6 × 256**, fixed | **32 ms** | User-tested Windows v0.6.8 via optional launcher; no stutter reported |

All three use `A3D_MASTER_GAIN=5.0`, `A3D_HRTF_TAPS=48`, peak limiting and opt-in-only logging. The audio thread priority is left at each existing profile's value (0); no unproven scheduling changes were introduced. The `A3D_WAVEOUT_SUBBLOCKS` variable selects frames per header: value 1 is 256, value 2 is 512. The configurations above are nominal application-side queue capacities, not measured physical-endpoint latency.

**Alice 2011 audio fallback:** `RUN_A3D_4x512_FALLBACK_WINDOWS.cmd` / `RUN_A3D_4x512_FALLBACK_WINE.sh` selects the previously smooth 4×512 (42.7 ms) profile while retaining the same legacy DSP renderer. It does not change FPS. If the new 6×256 default crackles, use this fallback.

**Alice 2011 frame-rate policy:** `RUN_A3D_WINDOWS.cmd` and `RUN_A3D_WINE.sh` deliberately do **not** pass a `com_maxfps` override. They defer to the user's VorpalFix/game configuration and monitor/VSync settings. `RUN_A3D_144FPS_WINDOWS.cmd` and `RUN_A3D_144FPS_WINE.sh` explicitly add `+set com_maxfps 144` for systems where that override is desired. This optional FPS profile is independent of the WaveOut buffer profile.

**Quake III default is now 6×256.** This exactly matches the v0.6.8 `RUN_A3D_32MS_TEST_*` audio settings that the user reported working smoothly. The earlier 3×512 profile remains available as `RUN_A3D_3x512_FALLBACK_WINDOWS.cmd` / `RUN_A3D_3x512_FALLBACK_WINE.sh`; the older 32ms test launcher name is retained as an alias of the new default.

## Installation (Windows / Linux Wine)

1. Make a complete backup of the three known-working game directories, particularly A3D DLLs and launcher scripts.
2. Extract the package's `Alice2000/`, `Alice2011-VorpalFix/` or `QuakeIII-117/` folder **contents** next to the respective original `alice.exe` or `quake3.exe`. Do not replace the original executables, game files, VorpalFix `winmm.dll`, Miles provider DLL or other assets.
3. Run `RUN_A3D_WINDOWS.cmd` on Windows or `RUN_A3D_WINE.sh` with Wine. Alice 2011 has independent audio-fallback and optional 144 FPS launchers. Quake III has a 3×512 fallback launcher if needed.
4. For Debian 13, read `DEBIAN13_WINE.md`, run `DEBIAN13_PREFLIGHT.sh` and `DEBIAN13_ABI_SMOKE.sh` from the extracted distribution root; then test the *actual game*. Game files are not bundled.

Quake III requires matched genuine 1.17 PK3 data. Alice 2011 additionally requires VorpalFix's `winmm.dll` and `SndDrivers/mssa3d2.m3d`, and the exact original executable revision expected by the version-checked in-memory A3D2 bridge. File-name case matters under Linux (see Debian guide).

## Diagnostics and rollback

Normal launchers set `A3D_LOG=0`, producing no A3D diagnostic log. `RUN_A3D_DIAGNOSTIC_*` explicitly enables logging; the main writer is capped at **1 MiB per process**, with a separate legacy shim cap. No continuous disk logging in normal operation. Logs are not switchable live from within the game; turn on before launch.

`KnownGoodReferences/` contains launcher references only, **not replacement DLLs**; the previous game backups are required for complete binary rollback. The Alice 2011 `4x512` fallback launcher already works with the v0.6.9 DLL, unless a deeper DLL regression is discovered.

## Build/verification

```bash
bash win32/build.sh
python3 tools/package_v069.py
python3 -m unittest discover -s tools -p 'test_*.py' -q
bash DEBIAN13_PREFLIGHT.sh
bash DEBIAN13_ABI_SMOKE.sh
```

The last two require a real Debian 13 host with Wine configured. Tests in the build environment validate PE32/i386 compilation, package configuration and Bash Wine command plumbing **without actually running Wine or retail games**. Debian 13 end-to-end game compatibility remains an acceptance test.

This is an unofficial preservation/research project, not endorsed by Aureal or the game developers.
