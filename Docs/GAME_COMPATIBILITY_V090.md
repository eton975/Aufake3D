# v0.9.0: game support and tests (truthful status)

**The presence of a game kit is not proof of game audio compatibility.**

| Game | Current status | Evidence and validation needed |
|---|---|---|
| Alice 2000 (retail) | Existing A3D2 integration; new 56-tap engine experimental | Re-test A3D2/Miles/Dolby cycling and tower2/hedge1/hedge2 with 6×256; no on-disk EXE patch |
| Alice 2011 (VorpalFix) | Provider-switch bridge previously gameplay-validated in v0.8.18; 56-tap engine experimental | Re-test Miles→A3D2→Dolby→Miles→A3D2, animation/dialogue timing and output stability |
| Quake III Arena 1.17 | Existing tested 32-bit A3D2 integration; 56-tap engine experimental | Use matching 1.17 PK3s; verify combat-heavy scenes and no voice drops |
| GTA III (original PC) | **Experimental A3D 1/2 probe, NOT verified** | Keep original Miles runtime/provider files; verify A3D2 calls, spatial audio and performance in-game. Prior third-party v0.8.x report is preliminary. |
| GTA Vice City (original PC) | **Experimental A3D 1/2 probe, NOT verified** | Verify genuine original-game Miles A3D2 provider, 3D sound, and no regressions. |
| GTA San Andreas (original PC) | **Research only; native A3D unproven** | Investigate DirectSound3D/EAX 4.0 separately; A3D DLL drop-ins alone are not sufficient. |
| Half-Life 1.x | **Not game-tested with v0.9.0**; existing 1.0.1.1 alpha kit | Check A3D activation in console, play a controlled stereo sweep/occlusion scene, capture logs and compare with legacy; no claim of fully tested HL support |
| Unreal (1998, classic) | **New experimental A3D probe kit**, not gameplay validated | Copy to original `System` directory beside `Unreal.exe`; enable Advanced Options→Audio→Use3dHardware, restart the game, verify COM/A3D calls and audible effects |
| Return to Castle Wolfenstein (2001) | **Exploratory only. A3D API use not established** | Investigate whether the retail executable actually calls Aureal A3D. If not, simply adding A3D DLLs cannot enable A3D; requires a genuine sound-backend adapter. No claims of supported A3D audio. |

The original Unreal documentation explicitly lists `Use3dHardware` for Aureal:
https://www.mogelpower.de/manuals/Unreal_Manual_C_Englisch.pdf

The RtCW readme discusses ordinary sound quality but does not establish A3D support:
https://www.rtcw.hu/dl/RtCW-Manual/Readme/readme.htm

## Controlled real-game pass/fail protocol

For each actual 32-bit executable and edition, record SHA-256, OS/Wine version,
launch command, HRTF mode, game-reported sound provider, A3D log start/stop,
subjective left/right/front/back/occlusion, queue empty events, dialogue sync,
and any glitches. Never label a platform or game "tested" without an observed
run using its original licensed game files.

In particular, Half-Life should be run with its existing alpha profile with
`s_eax 0` and `s_a3d 1` and checked for *actual* A3D API activity. Optionally
compare the `s_geometry` options, avoiding claims of Wavetracing without geometry
calls. Valve GoldSrc releases differ substantially; do not generalize a pass
from one executable to all versions or Steam generations.

See [GTA experimental kit guide](GTA_III_VICE_CITY_EXPERIMENTAL.md).
