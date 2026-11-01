# Aureal A3D v0.6.0 — Quake III Arena 1.17 Streaming Hotfix 3

This is an experimental fix for frequent audio dropouts after enabling A3D in Quake III Arena 1.17. This build limits speculative WaveOut submission of game-managed PCM to reduce stale DMA-ring reads. It is NOT confirmed as a cure. For commands and diagnostics, read `QUAKE3_STREAM_HOTFIX3.md` and `portable/QUAKE3_STREAM_HOTFIX3.md`.

If Hotfix 2 is installed, use that version's installer `python3 a3d_port.py uninstall "$HOME/Games/QuakeIII-117-A3D2/quake3.exe"` first. Then use this package's `portable/a3d_port.py` with `--profile quake3 --mode both`. Do not overwrite installed binaries manually; the installer records SHA-256 hashes.

The v0.6.0 core A3D2 sound renderer and both classic/2011 Alice bridges remain present. This build modifies only WaveOut queue scheduling in `stream_winmm.inc`. No original game files or VorpalFix DLLs are included.
