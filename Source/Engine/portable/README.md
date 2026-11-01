# A3D software wrapper — v0.6.0 consolidated release

**Release baseline: 31 October 2026.** This package consolidates the Hotfix 10 audio core and all three targeted game launchers. The actual `a3dapi.dll` is byte-for-byte identical to Hotfix 10 (`45ec13448cc4fc728c3fe99c375f9589ddc3341c8c10ea8d84580866a569bd73`). The Quake III preset is in its launcher, not an Alice-affecting global DLL default.

| Target | Launch method | Validation |
|---|---|---|
| **Quake III Arena 1.17 (Windows, 2000)** | `quake3.exe` via included `run_quake3_117_wine.sh` | **User-confirmed:** Demo 1 reaches completion after Hotfix 10; 4-block geometry retrace / 0.14 reverb sounds excellent. Other demos and Windows installs not systematically certified. |
| **American McGee's Alice (2000)** | `alice-a3d-bridge.exe` through `run_alice2000_wine.sh` | Previous classic-selector bridge already worked with earlier wrapper releases; consolidated v0.6.0 binary has offline tests, but no new user-confirmed full gameplay regression for this precise final build. |
| **Alice 2011 remaster + VorpalFix 4.2.1** | `alice-a3d2011-bridge.exe` through `run_alice2011_wine.sh` | Built and offline-tested; **actual remaster/VorpalFix playback under Wine remains unverified**. Requires the *exact* Alice remaster executable SHA-256 below and game-provided VorpalFix/Miles files. |

The project is an **unofficial A3D compatibility implementation**, not an original Aureal driver or a bit-exact Vortex 2 emulator. The A3D 1.x `a3d.dll` remains a legacy DirectSound compatibility frontend; the HRTF software renderer is implemented through the A3D 2.x COM `a3dapi.dll` path. Broad A3D 3.0 / IA3d5 or all-game support remains future work.

## Requirements

Python 3, Wine with 32-bit game support, and **your own legal game installations**. Recommended Linux install manager: `a3dctl` v1.1.1 or later. Install independently per game directory, not once globally. No Windows driver installation, no Wine COM registry setup, no on-disk EXE patching. Both Alice bridges change a checked selector in a newly created child process *in RAM only*.

## Install / upgrade

After extracting the **Portable** ZIP to any directory:

```bash
# Register each only once (replace Alice remaster path as appropriate):
a3dctl register q3 "$HOME/Games/QuakeIII-117-A3D2/quake3.exe" --profile quake3
a3dctl register alice2000 "$HOME/Games/ALICE/alice.exe" --profile alice
a3dctl register alice2011 "/path/to/Alice2011/bin/alice.exe" --profile alice2011

# Upgrade the desired game independently, directly from this Portable ZIP:
a3dctl install q3 /path/to/A3D_v0.6.0_Final_Portable.zip
a3dctl install alice2000 /path/to/A3D_v0.6.0_Final_Portable.zip
a3dctl install alice2011 /path/to/A3D_v0.6.0_Final_Portable.zip

a3dctl status q3
```

`a3dctl install ... --no-backup` skips the persistent rollback snapshot if desired. **A normal backup is recommended when upgrading from a known-working Alice installation.** Run `a3dctl rollback <name>` to return to a previous snapshot. The legacy version-specific `a3d_port.py` remains available for clean installs but will reject collisions; **prefer a3dctl** for upgrades.

If your games are already registered, only the three `a3dctl install` commands are needed. Do not register the same directory as multiple profiles: each installation stores a receipt in its game directory.

## Launch Quake III 1.17 — confirmed preset

```bash
bash ./run_quake3_117_wine.sh "$HOME/Games/QuakeIII-117-A3D2/quake3.exe"
```

Preset: `A3D_HRTF_TAPS=48`, `A3D_GEOMETRY_TRACE=1`, `A3D_GEOMETRY_RETRACE_BLOCKS=4`, `A3D_REVERB_WET=0.14`, `A3D_VOICE_LIMIT=128`, `A3D_WAVEOUT_QUEUE_HEADERS=3`, `A3D_WAVEOUT_SUBBLOCKS=2`, `A3D_Q3_DMA_CLOCK=0`, `A3D_MASTER_GAIN=5.0`; game cvars `s_mixahead=0.35`, `s_mixPreStep=0.05`. The launcher allows environment overrides, e.g. `A3D_MASTER_GAIN=0.5 bash ./run_quake3_117_wine.sh ...`. Enable A3D within the genuine Quake III 1.17 game. **Lower physical/headphone volume before testing gain 5.0.**

The release does **not** put these game-specific acoustic settings into the DLL defaults, to avoid changing Alice behaviour. Launching `wine ./quake3.exe` without the preset inherits its environment/default settings instead.

## Launch classic Alice (2000)

```bash
bash ./run_alice2000_wine.sh "$HOME/Games/ALICE/alice.exe" +set s_milesdriver a3d2
```

Use the game's installed `SndDrivers` modules. `alice-a3d-bridge.exe` performs checked, RAM-only sound-provider selector substitution. Do not substitute the Alice 2011 bridge.

## Launch Alice 2011 with VorpalFix 4.2.1

```bash
bash ./run_alice2011_wine.sh "/path/to/Alice2011/bin/alice.exe" +set s_milesdriver a3d2
```

Required unmodified `alice.exe` SHA-256: `08bcbe4b549633b24c90a1ab36bf516bd8873432c68b37248c98ee4225506e50`. In the same directory: existing VorpalFix `winmm.dll`, `VorpalFix.ini`, and `SndDrivers/mss32.dll`, `SndDrivers/mssa3d2.m3d`. The installer **never supplies or replaces** those third-party/game files. It refuses a remaster EXE with an unknown hash. A working selector bridge does not by itself establish real game audio compatibility.

## Build and validation

`bash build_and_test_v060.sh` from the full-source root cross-builds the 32-bit Windows binaries and exercises the Python and native C regression suites, including the Quake III IA3dList polygon-count return fix, geometry cache, 128-voice allocation, 24-tap filter correctness and checked Alice selectors. Rebuilding PE files may result in different time-stamp bytes while the logic remains identical. See `RELEASE_VERIFICATION.md` for precise tested scope and checksums.

Historical hotfix troubleshooting notes are retained in `history/`, but the three current quick-start guides and this README take precedence.

No copyrighted game EXEs, PK3 files, Miles DLLs or VorpalFix binaries are included.
