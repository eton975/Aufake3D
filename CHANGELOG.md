# Aufake3D change history

**Current development version: v0.9.2.** This is a summary for readers, not an assertion that a particular GitHub build has passed release certification. The exact original version notes, including limitations and experiment records, are preserved under [Docs/History/Release_Notes/](Docs/History/Release_Notes/).

## v0.9.2 — Descent 3 experiment, RtCW research, reproducible distribution

- Added a retail **Descent 3** experimental A3D path. An unmodified retail `main.exe` was observed loading the app-local `a3dapi.dll`; removing and restoring the two game-local DLLs removed and restored audio without changing the Aureal setup option. Initial listening and stereo comparisons suggest possible directionality. **Spatial accuracy, geometry and general compatibility remain unconfirmed.**
- Added a separate **public Descent 3 ZIP** generated from the existing universal DLLs, not from a forked renderer or a game-specific patched executable. The public kit excludes the standalone `.obj`, synthetic probe `.exe` and proprietary game files. The ZIP is assembled deterministically, with local and cross-host comparison checks.
- Added experimental **Descent 3 source integration and COM contract diagnostics**, kept separate from the retail drop-in route; the source-built engine is not gameplay-validated.
- Added deterministic **RtCW BSP v47 surface extraction** and provenance/validation for acoustics research. This is not an Aureal backend for retail RtCW.
- Expanded source/build verification with pinned **LLVM 19.1.7**, managed **Python 3.13.7** on CI, independent three-build comparisons, a mandatory five-target Windows/Ubuntu/Debian matrix and fail-closed evidence comparisons. The existence of these checks does not mean every proposed build already passed them.
- Reorganised current documentation around the GitHub README, installation, building, compatibility, troubleshooting and developer guides; preserved historical notes separately.

## v0.9.1 — local reproducibility gate

- Introduced default **three-way, byte-for-byte verification** of generated Windows PE binaries and the complete runtime ZIP, with checksum report `dist/REPRODUCIBILITY_VERIFIED.json` only on success.
- Carried forward the shared HRTF renderer and fixed WaveOut timing settings, avoiding gratuitous audio-engine changes while hardening the build.
- Continued experimental compatibility and geometry auditing; a same-host result does not establish cross-operating-system identity.

## v0.9.0 — AU8830 renderer and experimental game kits

- Added a contributor-derived **56-tap AU8830 HRTF** Reference/Fast path alongside the 48-tap Legacy mode, with a single shared engine.
- Extended experimental GTA III/Vice City and other game kits. A generated kit never implies proven original-game A3D activation.
- Improved toolchain selection, native mock checks and source-first packaging.

## v0.8.x — shared core, Alice and Quake III foundations

- Developed original A3D interfaces, audio-thread/WaveOut playback, provider selection and game-local DLL deployment without requiring registry changes in the ordinary path.
- Stabilised the **6 × 256 sample WaveOut queue** on earlier tested Alice and Quake III configurations; diagnosed polling/cursor timing and Alice 2011 provider switching.
- Added the Alice 2011 331-export Miles proxy, original-library preservation requirements, RAM-only selector research and manual Windows/Wine packaging.
- These records describe historical test configurations, **not** a universal v0.9.2 gameplay pass.

## Older development history

For exact chronology, hotfixes and original experimental claims, consult [historical release notes](Docs/HISTORY_INDEX.md) rather than applying old instructions to current binaries. Preserve the game's original DLLs and use the current [installation guide](Docs/INSTALLATION.md).
