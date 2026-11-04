# Aufake3D v0.8.18 — provider selection and 6×256 buffer release candidate

## Alice 2011 / VorpalFix

- Integrated the existing game-version-specific, signature-checked **RAM-only A3D2 selector bridge** in the normal Windows and experimental Wine game kit. It changes only suspended *child* memory, not `alice.exe` on disk.
- Disabled the `unknown` Miles alias in the default launcher. That alias had caused Alice to reopen A3D2 when switching from Dolby to Miles 2D.
- Added the source-built `alice-a3d2011-native.exe` to the packaged game kit; the launcher temporarily creates `alice.exe.manifest` from the app-local A3D manifest and removes it on normal exit. It refuses to overwrite an existing file. **Back up your installation before testing.** A forcibly closed launcher may leave a temporary manifest requiring manual removal.
- In real Windows user gameplay, the isolated native RAM selector reproduced successful Miles 2D → A3D2 → Dolby → Miles 2D → A3D2, confirmed by provider handles `0x08`, `0x04`, `0x05`, `0x08`, `0x04`. The integrated default launcher and Wine remain to be validated.

## Audio queue

- Alice 2000, Alice 2011 and Quake III 1.17 default to **six 256-frame WaveOut headers**, i.e. 1536 frames / 48 kHz = **32 ms** nominal queue duration.
- `A3D_WAVEOUT_QUEUE_HEADERS=6` and `A3D_WAVEOUT_SUBBLOCKS=1` are launcher defaults. `A3D_MASTER_GAIN=5.0`, HRTF and DSP are unchanged.

## Builds and status

- The active version is `0.8.18` in source build, runtime ZIP, installer receipts, kit map, and GitHub Actions artifact path.
- Linux build and source tests should pass on the local build host; Windows CI and in-game testing of this integrated package are required before a production release.
- The Alice 2011 bridge supports only the tested executable signature; unsupported variants fail closed. No proprietary game executable or Miles DLL is bundled.
