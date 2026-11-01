# A3D v0.6.12 final release

Use the matching folder in Binaries for each game. Copy its contents beside the original game executable, then follow WINDOWS_SETUP.md or LINUX_WINE_SETUP.md. Source is optional for playing. No game executables, game audio, Miles drivers or VorpalFix binaries are supplied.

This unofficial software A3D implementation uses one shared 32-bit Windows engine. It is not a bit-exact Aureal hardware emulator. The release preserves the v0.6.12 weapon-clarity algorithm; “final” describes packaging, documentation and build verification, not certified Linux compatibility.

| Target | Renderer | Queue at 48 kHz | HRTF | Gain | Clarity |
|---|---|---|---|---|---|
| Alice 2000 | Snapshot | 6 × 256 frames | 48 taps | 5.0 | On |
| Alice 2011 + VorpalFix | Legacy | 6 × 256 frames | 48 taps | 5.0 | On |
| Quake III Arena 1.17 | Snapshot | 6 × 256 frames | 48 taps | 5.0 | Off |

The queue holds 32 ms of application audio. This is not measured speaker latency. Normal launchers default to logs off, latency trace off, fixed buffering and normal worker priority. Existing environment overrides are respected: start from a fresh terminal without A3D overrides to test release defaults. Capture and staff diagnostics are opt-in only.

Alice 2011's normal launcher leaves the FPS setting to VorpalFix. Its separate 144FPS launcher passes +set com_maxfps 144. Both Alice folders include ORIGINAL_MIX launchers, which force clarity off using the same DLL.

Clarity recognises 15 exact source-buffer fingerprints for 14 known weapon names, including two Eye Staff charge variants. Spatialisation remains active. With at least four active voices and an audible recognised weapon, competing audio smoothly falls by at most about 3.7 dB. Limiter recovery is faster when clarity is on. Unrecognised sounds cannot trigger protection. This is a conservative heuristic, not universal weapon recognition.

Read VERIFICATION.md for results and limits. Real Linux gameplay and sound have not been verified in this release session. The user reported improved weapon clarity in the preceding v0.6.12 build.

Integrity: MANIFEST.json lists file sizes and SHA-256 hashes; SHA256SUMS.txt covers every payload file and the manifest. The checksum file itself is excluded to avoid a circular hash. Top-level ZIP checksums are supplied separately. These are integrity checks, not signed provenance.
