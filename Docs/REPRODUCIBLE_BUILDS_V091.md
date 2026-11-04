# v0.9.1: mandatory reproducibility gate (development candidate)

Every normal packaged `python scripts/build.py`, `BUILD_WINDOWS.cmd`, and
`BUILD_LINUX.sh` build now replays the compilation and packaging in **two
independent clean source copies**, then compares **all generated Win32 PE
executables/DLLs and the complete ZIP** byte-for-byte against the user's build.
An exception or mismatch aborts the command; no verification report is issued.

Only after all three outputs match is `dist/REPRODUCIBILITY_VERIFIED.json`
created, recording the exact complete-ZIP SHA-256 and individual PE hashes.
That report is kept **outside** the ZIP to avoid changing the archive after
verification. A prior report is deleted before the build starts; a changed
archive or executable fails `python scripts/verify_reproducible.py --check-report`.
GitHub Actions must run `--check-report` before uploading artifacts.

The normal build invokes full source and acoustics tests when supported;
the two replay builds skip duplicating test execution, but use the same
source and toolchain. These are **same-machine, same-toolchain** checks.
Cross-host, cross-toolchain or cross-OS bit identity is **not guaranteed** until
compiler/linker/SDK/archive environments are pinned and outputs compared.

`--skip-repro-check` is an explicit UNVERIFIED development-only escape hatch,
used by the recursive replay subprocess; builds made with it must not be
published as reproducible. `--no-package` also means no verified release.

This is a source and packaging milestone, **not** proof of A3D 2.0/3.0
acoustic completeness, real Vortex 2 driver compatibility, or gameplay support.
Original retail game files and proprietary SDK DLLs are not included.

## v0.9.2 Windows/Linux CI certification (separate gate)

The build now has a mandatory GitHub Actions cross-platform comparison job
using exact LLVM/Python versions and deterministic uncompressed ZIP entries.
It compares actual runtime ZIP bytes and per-PE hashes before issuing a
separate cross-OS certificate. A local three-build report is **not** a
cross-platform certificate. Full details: `Docs/CROSS_PLATFORM_REPRODUCIBILITY.md`.
