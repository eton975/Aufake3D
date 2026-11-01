# Release verification — A3D v0.6.12 final

Built on Windows x86-64, 1 November 2026 (Australia/Sydney). Toolchain: llvm-mingw 20261020 UCRT, Clang/LLD; freestanding i686-pc-windows-msvc targets for release programs. The release uses the source recovered from A3D_v0612_WeaponClarity_AllInOne.zip in the user's Downloads. The former /mnt/data path is unavailable on this host. PROVENANCE.json records the input archive hash.

## Passed

* Rebuilt both shared DLLs, all three game activation bridges, self-test, COM test and Quake III lock probe as PE32 x86. All profile copies have identical shared DLL hashes.
* Repeat builds produced identical SHA-256 hashes for the two DLLs and three bridges after setting linker timestamps to zero. This is same-host reproducibility, not a cross-toolchain guarantee.
* 110 tools regression tests passed, including synthetic weapon recognition, clarity bypass/bounds, snapshot metadata and simulated Wine-launch checks.
* 9 drop-in installer/export tests and 15 portable installer tests passed (134 total Python tests across all three suites).
* 18 native DSP regression programs passed, covering spatial output, HRTF directions, geometry/cache, reflection balance, gain/limiting, streaming and clarity. The Alice snapshot capture parity program covered 864 cases with zero failures.
* Nine Windows ABI smoke executions passed: self-test, registration-free COM and Quake III Lock/Unlock probe in each of three profile directories. No game executable or audio playback was used.
* Every deployed .sh launcher passed Bash syntax checks. Existing regression tests executed normal, original-mix, FPS and buffering launchers with a fake Wine executable, checking arguments, settings and override inheritance. These are launcher simulations, not Wine execution.
* All release ZIPs receive CRC, exact member-set, file-size and SHA-256 verification against their embedded manifests. ZIP-level hashes are published in SHA256SUMS_ZIPS.txt. See ARCHIVE_VERIFICATION.json after packaging for actual counts.

## Scope and remaining limits

No real Wine runtime is available on this Windows host; WSL is not configured as a Linux test environment. No Debian, Ubuntu, Fedora or Arch gameplay, Wine COM loading, Linux audio output or end-to-end latency was verified. Native Windows gameplay was also not rerun for this final packaging. The user reported the preceding v0.6.12 weapon clarity sounded better; that behavior is preserved.

The archived tools/test_pcm_native.c wrapper harness does not compile against the current diagnostics/WinMM worker because its historical OS stubs are incomplete. It is explicitly excluded from run_native_tests.py; its failed exploratory attempt is not counted as a pass. Current source/lock ABI coverage comes from contract checks and rebuilt PE32 ABI programs. The separate acoustics CMake/ctest suite and sanitizers were not run in this session.

The main build emits five unused-helper warnings in the shared engine compilation; native header-based test programs also emit unused-helper warnings. No warnings were hidden or promoted into a claim of a warning-free build.

## Release work

Added source commentary and a source map without changing the audio algorithm, recognition table or game selector logic. Corrected inherited Quake bridge comments. Added the missing lock probe to the common Windows/Python recipe, deterministic linker timestamps, Clang-compatible counter assertions in two tests, and LLVM objdump support in export tests. Rewrote installation/build instructions and updated the current launcher log filenames. Historical source deployments/tools remain as regression fixtures; use only Binaries or Source/deploy-v0612 for installation.

Logs in validation document actual commands/results. SciPy and NumPy are test/analysis prerequisites only. No compiler, Wine, game assets, VorpalFix binary or diagnostics PCM capture is bundled.
