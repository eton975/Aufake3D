# One-command Windows and Linux build (v0.9.2 reproducibility-gated candidate)

**Windows 10/11:** double-click **`BUILD_WINDOWS.cmd`** in the repository root.
**Linux:** run **`./BUILD_LINUX.sh`** in the repository root.
These launch the same cross-platform Python orchestrator (`scripts/build.py`) and
produce 32-bit **Windows PE** game DLLs and EXEs on both operating systems.
The project does **not** currently build native ELF `.so` libraries for Linux;
Wine loads the Windows binaries. Build scripts never modify original games.

## First-time prerequisite installation

| Host | Essential (for DLLs, game helpers and proxy) | Optional (for all tests) |
|---|---|---|
| Windows 10/11, x64 | Python 3.10+, LLVM Clang and LLD (`clang.exe` and `lld-link.exe` on `PATH`) | Visual Studio 2022 **Build Tools**, Desktop development with C++ and Windows 10 SDK; CMake |
| Debian 13/Ubuntu | Python 3.10+, `clang`, `lld`, `git` | `cmake`, `ninja-build`, a host C++ compiler |

Windows installers: [Python](https://www.python.org/downloads/windows/),
[LLVM](https://github.com/llvm/llvm-project/releases),
[Git](https://git-scm.com/install/windows/),
[Microsoft C++ Build Tools](https://visualstudio.microsoft.com/downloads/).
For Windows, `C:\Program Files\LLVM\bin` typically needs to be included
in the user `PATH`. A x64-host compiler can emit the required x86 DLLs;
**do not install 32-bit Python** simply to compile 32-bit game binaries.

Debian/Ubuntu packages (no Wine or Windows SDK is required for the A3D engine):

```bash
sudo apt update
sudo apt install -y python3 clang lld git cmake ninja-build g++
```

### Windows without a special Developer PowerShell

The main A3D engine uses **freestanding** Windows code and is linked using
project-created import stubs, not the Microsoft CRT. It needs LLVM/Clang/LLD,
not MSVC. The separate *host-native* Miles mock test uses `<stdio.h>` and the
Microsoft CRT. Earlier tests failed with missing `msvcrt.lib` / `oldnames.lib`
because an ordinary PowerShell did not have the MSVC `LIB` search path set.

`tests/test_source_repo.py` now uses `scripts/host_toolchain.py` to discover
x64 MSVC and Windows SDK **header and library** directories (via
`INCLUDE`, `LIB`, `VSINSTALLDIR`, `vswhere`, and typical installation locations),
passing both `-isystem` and `/LIBPATH` explicitly to Clang. There is **no need to manually run Launch-VsDevShell.ps1** when
these tools are installed. If the optional MSVC CRT is absent, the test reports
an explicit `SKIP` rather than a confusing linker failure. To require this
test in automation, use `--require-native-mock`.

### Multiple installed MSVC versions (the v0.9.0 fix)

Windows sometimes has a usable `cl.exe` on PATH from an **incomplete**
older MSVC installation. For example, MSVC 14.31 can supply `cl.exe` but have
only ARM CRT libraries, while MSVC 14.44 also supplies the required x64 CRT.
`cl /Bv` does **not** establish that the matching x64 libraries are installed.

The v0.9.0 builder uses `windows_complete_msvc_toolset()` to find a **single
matching version** containing `Hostx64/x64/cl.exe`, `link.exe`, its own x64
`msvcrt.lib`, `oldnames.lib` and `vcruntime.lib`, plus SDK `ucrt.lib`,
`kernel32.lib` and `stdio.h`. When CMake is installed, it configures the
Visual Studio generator with an explicit toolset (`-T version=<detected>,host=x64`)
and instance path. **It does not need a manually initialized Developer Shell
or any permanent edits to PATH/LIB.** Each MSVC version gets a separate CMake
cache directory under `build/`.

Use `py -3 scripts\build.py --doctor` to display the selected toolset.
Run `py -3 scripts\build.py --require-acoustics` when you want CI-style
**mandatory** C++ tests. With the default one-click build, truly missing
optional C++ prerequisites are reported as *SKIPPED*, never silently *PASSED*.
If CMake starts and a test actually fails, the build exits with an error.

## One-click usage

From Explorer, double-click `BUILD_WINDOWS.cmd` (it leaves a visible console
open with the result). Alternatively use a normal PowerShell:

```powershell
Set-Location 'C:\Dev\Aufake3D'
.\BUILD_WINDOWS.cmd
```

Under Linux:

```bash
./BUILD_LINUX.sh
```

You can run the common driver directly as well:

```bash
python3 scripts/build.py --doctor
python3 scripts/build.py
python3 scripts/build.py --no-acoustics
python3 scripts/build.py --strict-frozen-hashes
```

PowerShell uses `py -3 scripts\build.py --doctor` (or `python scripts\build.py`).

| Option | Meaning |
|---|---|
| `--doctor` | Print dependencies and whether optional native testing is available; do not compile |
| `--no-acoustics` | Skip optional CMake C++ tests; core and runtime still build |
| `--require-acoustics` | Fail if CMake/MSVC C++ acoustics tests cannot run (used by CI) |
| `--no-tests` | Skip Python tests explicitly (not recommended) |
| `--no-package` | Build DLLs and EXEs but skip the ready-to-copy runtime ZIP |
| `--require-native-mock` | Fail if Windows MSVC CRT prerequisites aren't available, rather than skipping that test |
| `--strict-frozen-hashes` | Historical release audit only; fail if core or Miles proxy differs from pinned bytes |

### Reproducible-build release gate (v0.9.1)

Every normal packaged build now builds all PE components and a deterministic runtime
ZIP, then **rebuilds the same source in two independent clean directories**.
All executables, DLLs, and ZIP bytes must match all three builds or the command
fails. On success, `dist/REPRODUCIBILITY_VERIFIED.json` records checksums.
To ensure no files changed since validation, run:

```bash
python3 scripts/verify_reproducible.py --check-report
```

`--skip-repro-check` is a **development-only, explicitly unverified** escape
hatch; it must not be used for release candidates. Extra rebuilds increase
build time. This proves **same-host and same-toolchain** determinism only;
Windows versus Linux byte identity still requires separately controlled and
verified toolchains.

### Results

- `dist/core/a3d.dll` / `dist/core/a3dapi.dll` — universal **PE32/x86** audio core
- `dist/miles-local/mss32.dll` — independently authored 331-export Miles proxy
- `Source/Engine/classic2000/alice-a3d-bridge.exe` — checked Alice 2000 launcher
- The other 39-step recipe outputs, including Half-Life, Quake III and Unreal helpers
- `dist/Aufake3D_v0.9.2_Local_Runtime.zip` — assembled from **source-only**
  launcher/manifests templates in `packaging/Game_Kits/`, not from an old binary ZIP.
  Includes ready-to-copy kits for Alice 2000, Alice 2011, Quake III 1.17 and
  Half-Life, plus universal DLLs, the reversible installer scripts, manual
  installation instructions, diagnostics and experimental utilities.

The packaging program verifies each compiled file is **PE32/x86**, and checks
that the installer-map list is complete. It intentionally excludes the
previously flagged precompiled `a3d-selftest.exe` and proprietary game content.
It generates **new local SHA-256 metadata** for your own build. A locally built
binary is *not* certified safe, verified in-game, or guaranteed byte-identical
with the historical release. Do not publish its artifacts as an official tested
release without independent game testing, licensing and component-level AV review.

### Frozen release versus everyday development

Compiler versions can change PE byte output without changing COM exports.
The 331-export Miles **ABI check always runs**. A frozen reference hash mismatch
is a **warning during normal development** and a hard error under
`--strict-frozen-hashes`. Do not overwrite the known-good Alice 2011 proxy
merely because the new DLL compiled successfully. For the actual game,
`a3d_mss_real.dll` must still be supplied from your legitimately owned game
and is deliberately never included in source or generated releases.

`SOURCE_MANIFEST_SHA256.json` is a snapshot of the repository at this tooling
revision. `Tools/verify_source_manifest.py` exists for frozen snapshot audits,
**not** as a mandatory check on every source edit or PR. The everyday CI
checks source-only provenance, tests, builds and publishes downloadable
artifacts instead. To refresh a frozen snapshot, use
`python3 scripts/update_source_manifest.py` *after* reviewing and committing
all intended source changes. Do not regenerate snapshots merely to silence
an unexpected file change.

### Troubleshooting

- **Clang/LLD not found:** Run `python scripts/build.py --doctor` and add LLVM's
  `bin` folder to `PATH`; start a new terminal.
- **`stdio.h`, `msvcrt.lib`, `oldnames.lib` missing:** Install Visual Studio
  Build Tools and the Windows SDK for the *optional* native mock. No need to
  install these to build the freestanding audio engine. A normal build should
  explicitly skip the optional mock if unavailable.
- **Miles proxy hash mismatch:** Expected with some LLVM versions. The ABI
  check still runs; use `--strict-frozen-hashes` to audit historical releases.
- **Missing game kit file:** The builder fails with its exact template path.
  Do not copy old game-specific DLLs to fill a missing dependency.
- **Windows antivirus flags:** Reproducibility is not malware clearance;
  inspect `Docs/SECURITY_REVIEW_V0814_RC1.md` before distribution.
- **Linux x86 executables don't start natively:** They're PE files; run under
  a suitable Wine installation. Wine is not required to build.

- **CMake selects old MSVC and reports `MSVCRT.lib` / `MSVCRTD.lib`:**
  v0.9.0 automatically chooses the newest *complete* compiler+CRT toolset,
  and isolates the CMake cache by version. Avoid manually mixing a 14.31
  compiler with 14.44 libraries. Check `scripts/build.py --doctor` output.
