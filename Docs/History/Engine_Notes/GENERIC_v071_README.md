# A3D v0.7.1 Generic Compatibility Development Kit

**Status: experimental developer tools, NOT a universal A3D 1.x/2.0/3.0 release.**

This increment keeps the existing a3dapi.dll DSP and a3d.dll DirectSound fallback
unchanged, while providing a second, direct Windows launcher, shared safe argument
parsing, a read-only ABI survey, and improved candidate scanning/staging. The older
Alice 2000 / Alice 2011 / Quake III game-specific profiles remain unchanged.

## What is now available

* `a3dapi.dll`: shared A3D 2.x COM software engine (the known existing build).
* `a3d.dll`: historical A3dCreate exports, **DirectSound fallback only**, not A3D1 HRTF.
* `a3d-direct.exe`: a normal Windows `CreateProcessA` launch. Does **not** modify
  child memory, suspend it, inject a bootstrap or modify game files. This may use
  an adjacent external COM manifest if the OS/game honours it. **COM activation
  is not guaranteed** on all game builds. It is not anti-cheat certification.
* `a3d-launch.exe`: existing explicit experimental child-activation bootstrap,
  which DOES modify the launched process memory. Offline or explicitly approved
  use only; don't use on protected multiplayer servers without approval.
* `a3d-abi-survey.exe`: prints the A3D export and QueryInterface responses; no
  proprietary game binaries required. The staged survey script uses the bridge
  in its **own survey process**, not a game process.
* `scan_a3d_clients.py`: read-only static scan. Separates evidence for legacy
  A3D1, A3D2 COM and A3D3 extension IDs and collects Miles .m3d candidates.
* `stage_generic_candidate.py`: prepares a NEW overlay folder, reports
  conflicting existing files, preserves original game files, and supplies
  both direct and bridge launch scripts. It does not enable an A3D backend.

## Windows: stage an unknown 32-bit A3D game

Python 3 is needed for the one-time staging operation, not for running the DLLs.
The game executable must be a 32-bit Windows PE file. Use a backed-up test
installation, not multiplayer/production game folders.

1. In `Generic-A3D2/`, find the DLLs, both launchers and the ABI survey executable.
2. Optionally inspect the game directory with:
   `python tools/scan_a3d_clients.py "C:\\Games\\Example" --out scan.json`
3. Stage in an empty, separate output directory (the command below is run from
   the *root of the toolkit*):
   `python tools/stage_generic_candidate.py "C:\\Games\\Example" --exe Example.exe --out "C:\\A3D-Tests\\Example"`
4. Read `INSTALL_PLAN.json` and `README_CANDIDATE.txt` in that output directory.
   The overlay does not contain the retail game executable or copyrighted data.
5. Back up each file listed under `conflicts_back_up_before_manual_copy`; only
   then copy the overlay contents into a **copy** of the game's executable
   directory. External manifests may conflict with a game's embedded manifest.
6. Set the game's own A3D/audio backend selection, if it has one. Then try
   `RUN_A3D_WINDOWS.cmd` (direct launcher, no bootstrap). Check whether there
   is actual A3D output and audio movement, not just a successful launch.
7. If direct launch does not reach the COM server, the *explicit opt-in*
   `RUN_A3D_BRIDGE_WINDOWS.cmd` uses the existing in-memory activation bootstrap.
   This is not appropriate on anti-cheat protected multiplayer servers without
   permission. `RUN_A3D_DIRECT_WINDOWS.cmd` is an additional raw-exe baseline.
8. Use `RUN_A3D_DIAGNOSTIC_WINDOWS.cmd` only when logs are required. Normal
   launches have logging disabled.

## Debian / Wine

Use an existing working Wine prefix and installed system Wine. Stage with Python
on Linux or Windows. File names are case-sensitive on Linux.

```
python3 tools/scan_a3d_clients.py "$HOME/Games/Example" --out "$HOME/scan.json"
python3 tools/stage_generic_candidate.py "$HOME/Games/Example" --exe Example.exe --out "$HOME/A3D-test-overlay"
```

After backing up files and installing the overlay next to the game executable:

```
bash RUN_A3D_WINE.sh              # direct launch, without bootstrap
bash RUN_A3D_BRIDGE_WINE.sh       # experimental in-memory COM activation
bash RUN_A3D_DIRECT_WINE.sh       # original game EXE, for comparison
```

The scripts preserve `WINEPREFIX`, append local `a3dapi=n,b;a3d=n,b` DLL overrides,
and use `A3D_WINE_EXECUTABLE` if set. Wine and actual games were **not executed**
on this build host. In particular, a direct launcher that starts successfully
may still fail to activate the A3D COM object.

## Current compatibility boundaries

| Client feature | Coverage | Important limitation |
|---|---|---|
| Historical `_A3dCreate@12` | Legacy export & DirectSound creation | Not Aureal A3D1 HRTF/geometry |
| A3D 2.x IA3d3/IA3d4, sources, geometry | Substantial shared software backend | Title-specific assumptions remain |
| IA3d5 / IA3dSource2 / IA3dGeom2 | Not implemented | A3D3-only games cannot be claimed supported |
| New generic launcher | Compiled PE32, static contract verified | Not tested against new retail games |
| Low-invasive direct launcher | No process-memory-writing imports | External COM activation may fail |

The scanner's 'candidate' label is only a static hint. A DLL may use an A3D
interface dynamically with no embedded GUID, and GUID strings may be unreachable.
Windows protected multiplayer servers may ban ANY modified game installation
regardless of how the process was launched. Never represent these binaries as
anti-cheat approved, or try to conceal their behavior from security products.

## Preserved settings

The shared DSP was not changed from v0.7.0-alpha: 48-tap HRTF, gain 5.0, linked
limiter and fixed 6 x 256 frame, 32ms WaveOut default remain. Alice 2000 and
Alice 2011 have their working game-specific snapshot/legacy modes and optional
weapon clarity; Alice 2011 still uses VorpalFix's FPS controls by default.
Game-specific profiles are **not** automatically replaced by this generic kit.

## Build and validation

From an extracted *source* tree with Clang/LLD installed:

```
bash win32/build.sh
bash win32/build_generic_probe.sh
python3 tools/build_generic_v071.py
python3 -m unittest discover -s tools -p 'test_*.py' -q
python3 -m unittest discover -s tests_v070 -p 'test_*.py' -q
```

All Win32 outputs are PE32/i386 and are standalone Windows/Wine binaries. These
cross-build tests establish compilation and ABI structure, not game behavior.
No retail original game assets are distributed by this kit.
