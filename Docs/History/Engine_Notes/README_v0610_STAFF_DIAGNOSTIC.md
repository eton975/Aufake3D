# A3D v0.6.10 — Opt-in Eye Staff / quiet weapon-sound diagnostic (Windows & Wine)

This **diagnostic candidate** investigates missing or very quiet Jabberwock's Eye Staff charging sounds in both Alice games during enemy-heavy audio. It is **not yet a repair** and does **not require identical combat situations to be reproduced**.

## Installation

Back up your existing v0.6.9 game directory first. From this archive copy the corresponding `Alice2000` or `Alice2011-VorpalFix` folder files beside the **existing legally installed game**. No retail game assets are included. Normal `RUN_A3D_WINDOWS.cmd` and `RUN_A3D_WINE.sh` profiles remain unchanged.

Run `RUN_A3D_STAFF_DIAGNOSTIC_WINDOWS.cmd` or `RUN_A3D_STAFF_DIAGNOSTIC_WINE.sh` in the appropriate game folder. Continue playing naturally; you need not artificially trigger the same encounter twice. **Exit the game normally**, which exports the last 4096 source/limiter observations to `a3d-v0610-staff-alice20xx-windows.log` (or `-wine.log`). The main A3D logging mechanism has a **hard 1 MiB per-process limit**; records are stored in RAM during play and exported on normal mixer shutdown. The first 4096 observations are not pinned, so it is better to exit reasonably soon after a rare event, or older event history may be overwritten.

If you *happen* to hear a bad charging sound, optionally switch to Windows and double-click `MARK_STAFF_BAD_WINDOWS.cmd` (or execute `MARK_STAFF_BAD_WINE.sh` on Linux). If you hear a clear, normal one, optionally mark GOOD. These markers are aids, not prerequisites; the logs retain source, gain and limiter measurements automatically. Switching focus can itself change timing, so mark approximate observations only and do not attempt perfect reproducibility.

Run `python3 ANALYSE_STAFF_LOG.py <name_of_log.log>` to see voice creation/rejection events, PCM fingerprints, limiter reduction, and nearby activity around any optional markers. Python 3 is required only for analysis, **not for game playback**. You can also upload the log for interpretation.

## What is recorded

- Creation, playback, preserved/restarted playback, stops and releases of source IDs.
- Waveform-buffer prefix fingerprints (FNV-1a) to correlate recurring sound sources. Fingerprints are approximate and **do not identify a game asset or prove it was audible**.
- Gain and priority changes at the A3D source API; rejected mixer allocations.
- Periodic in-memory summaries of concurrently active voices, limiter envelope and clipping-event increments.
- Optional GOOD/BAD markers and active-source snapshot at marker time.

**Known limitations:** A sound can be obscured because of game-side Miles voice stealing before reaching this A3D API; the wrapper cannot see a Play that never happened. Mixer limiter reduction can coincide with quiet playback but does not, by itself, establish causation. The report requires normal mixer shutdown; a process crash or forced kill loses buffered events. The ring only retains the last 4096 events. The diagnostic DLL adds some CPU bookkeeping, so compare audio quality with v0.6.9 if stutter occurs.

## Preserved audio settings

- Alice 2000: snapshot HRTF, 6 × 256 (32ms).
- Alice 2011: legacy renderer, 6 × 256 (32ms); game/VorpalFix FPS defaults unchanged; opt-in 144 FPS launcher preserved.
- Quake III 1.17: snapshot renderer, 6 × 256 (32ms), unchanged.
- HRTF 48 taps, master gain 5.0, peak limiter; no changes to game sound-voice priority or DSP.

Default launchers still disable diagnostic logging. This v0.6.10 build is for information gathering, not for unattended release distribution.
