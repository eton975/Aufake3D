# Build and release Aufake3D v0.9.2

**All distributable binaries and ZIP build artifacts are generated under `dist/` at the repository root.** A newly cloned source checkout does not include compiled DLLs. Both supported host build paths produce **32-bit Windows PE** files, not Linux `.so` libraries.

## 1. One-click build

On **Debian 13 / Ubuntu**, from the repository root:

```bash
./BUILD_LINUX.sh
```

On **Windows 10/11**, double-click `BUILD_WINDOWS.cmd` (or run it in a terminal). These entry points start `scripts/build_pinned.py`, which prepares the prescribed pinned toolchain before invoking `scripts/build.py`. **Prefer these launchers** for any reproducibility claim; a direct invocation of `scripts/build.py` with an unrelated system Clang is not equivalent.

Reference build inputs include **LLVM/Clang+LLD 19.1.7**, **Python 3.13.7** on CI and pinned/download-verified toolchain distributions. The CI Python bootstrap uses pinned `uv`. The environment may require system libraries, CMake/Ninja and a host compiler for optional/required native acoustics tests. Windows C++ mock/acoustics tests may require matching Visual Studio 2022 Build Tools and Windows SDK libraries. Read the error output rather than mixing compiler versions.

To check the current environment without running the entire compilation, use the pinned builder's documented doctor mode (or, if the pinned environment is already active, `python scripts/build.py --doctor`).

## 2. Where exactly is the output?

```text
dist/
  core/a3d.dll
  core/a3dapi.dll
  miles-local/mss32.dll
  Aufake3D_v0.9.2_Local_Runtime.zip
  Aufake3D_v0.9.2_Descent3_Experimental_Win32.zip
  REPRODUCIBILITY_VERIFIED.json           successful local check only
  DESCENT3_PUBLIC_RELEASE_SHA256.json     ZIP checksums
  descent3/                                optional probe/standalone adapter target
```

Other development build intermediates may be generated in `Source/Engine/`, but **look in `dist/` for actual release packages**. `dist/core` contains the identical universal renderer used in the normal runtime and Descent 3 retail ZIP, not separate per-game DLL implementations.

A general runtime ZIP contains `Game_Kits/.../COPY_TO_GAME_FOLDER` trees. The **separate** Descent 3 ZIP contains a ready-to-copy folder with two universal DLLs, a README and checksums. It must not contain proprietary retail game files or the experimental standalone probe/adapter `.obj`.

## 3. Run checks

Standalone regression tests (these do not themselves replace the full build):

```bash
python3 -m unittest discover -s tests -v
```

A default packaged build must run the normal local release gate, which builds the current source and **two independent clean copies** on the same host/toolchain. It compares the **complete raw runtime ZIP**, **complete raw Descent 3 ZIP** and generated PE files byte-for-byte. Only a successful run writes `dist/REPRODUCIBILITY_VERIFIED.json`. An error, mismatch, or explicit `--skip-repro-check` is **not release certification**.

To validate an existing local report:

```bash
python3 scripts/verify_reproducible.py --check-report
```

The public Descent 3 ZIP packager is `scripts/package_descent3_release.py`; the regular build calls it automatically. It uses fixed ZIP member order, timestamps and metadata, `ZIP_STORED` (avoids cross-host DEFLATE differences), verifies DLL PE32/x86 type, and records SHA-256 externally. Do not manually recompress the ZIP after verification.

## 4. Cross-platform release certificate

The CI workflow `.github/workflows/source-ci.yml` requires **five independent target environments**:

1. Windows Server 2022
2. Ubuntu 24.04
3. Ubuntu 26.04
4. Ubuntu 26.10
5. Debian 13 (digest-pinned container with verified distro identity)

Each builds the same committed source, verifies local deterministic outputs and publishes evidence. The separate matrix jobs fail if any target is absent or if **source hashes, generated PE bytes, raw runtime ZIP bytes or raw Descent 3 ZIP bytes** differ. The relevant reports are `CROSS_PLATFORM_REPRODUCIBILITY_VERIFIED.json` and `DESCENT3_PUBLIC_RELEASE_VERIFIED.json`. **A local report is not a five-host certificate, and a CI workflow definition is not proof a particular run passed.** Inspect the actual run and reports before publication.

The pinned inputs and exact verification code are documented in [cross-platform reproducibility](CROSS_PLATFORM_REPRODUCIBILITY.md). The experimental developer-only Descent 3 probe/adapter has a separate reproducibility scope; it is **not** the public retail-game ZIP.

## 5. Before creating a GitHub release

1. Review changed and untracked files: `git status --short --branch` and `git diff --check`. Ensure new scripts/tests/docs are staged; `git add -u` alone misses new files.
2. Commit all intended sources. CI certification requires the **exact commit** and a clean checkout; a dirty local working tree cannot obtain a valid cross-OS certificate.
3. Run the pinned build and regression tests. Inspect warnings, native-test skips, DLL provenance and security/licence review. Failed tests and skipped mandatory checks cannot be treated as passes.
4. `git fetch origin main`; verify that your local history includes `origin/main`; then `git push --dry-run origin HEAD:main`. Never force-push to conceal divergence.
5. Push the intended commit, inspect all five CI jobs, download and check the generated certificate. **Only then** attach the **verified** runtime and separate experimental Descent 3 ZIP to a GitHub v0.9.2 release, along with accurate release notes.
6. Name the Descent 3 asset **experimental** and state that DLL loading/audio dependency were observed but HRTF, occlusion and geometry remain unconfirmed. Reproducibility is not antivirus clearance or gameplay verification.

For installation see [Installation](INSTALLATION.md); for current changes see [CHANGELOG](../CHANGELOG.md); for failures see [Troubleshooting](TROUBLESHOOTING.md).
