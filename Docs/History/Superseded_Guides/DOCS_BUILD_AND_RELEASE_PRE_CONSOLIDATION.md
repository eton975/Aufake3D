# Building, finding and publishing Aufake3D v0.9.2

**Start with [Docs/README.md](README.md). The release-ready binaries and
archives are in the repository-root `dist/` directory.** They are generally
not checked into Git, so a clean source checkout does not yet contain them.

## 1. Build locally

Run `BUILD_WINDOWS.cmd` on Windows 10/11, or `./BUILD_LINUX.sh` on Debian/Ubuntu.
These invoke the pinned builder for Python 3.13.7 and LLVM 19.1.7. The output
is Windows x86 PE32 software even when built under Linux.

Default builds compile, test, package, and verify using the current source.
They require two additional independent clean same-toolchain builds. Never
suppress this check for a public release; `--skip-repro-check` is development
only, not certification.

## 2. Find the output files

| Path under the repository root | What it is |
|---|---|
| `dist/core/a3d.dll`, `dist/core/a3dapi.dll` | Shared binary audio engine |
| `dist/Aufake3D_v0.9.2_Local_Runtime.zip` | Full game-kit ZIP |
| `dist/Aufake3D_v0.9.2_Descent3_Experimental_Win32.zip` | Public Descent 3 folder-copy ZIP |
| `dist/DESCENT3_PUBLIC_RELEASE_SHA256.json` | Local Descent 3 checksum report |
| `dist/REPRODUCIBILITY_VERIFIED.json` | Local three-build verification report |
| `dist/descent3/` | **Optional developer-only** Descent 3 probe and adapter (separate build) |

The ZIPs themselves can be sent to users; `dist/` is a *build output folder*,
not something users must create or copy wholesale into a game installation.
The Descent 3 public ZIP is **not** the same as the dev diagnostics folder.

## 3. Verify before release

`python scripts/verify_reproducible.py --check-report` verifies the current
runtime PE and ZIP hashes, including the Descent 3 public package when emitted
by the v0.9.2 builder. The build has already performed the three-build gate
unless the user deliberately chose a development-only bypass.

The mandatory CI workflow `.github/workflows/source-ci.yml` builds separately
on **Windows Server 2022, Ubuntu 24.04, Ubuntu 26.04, Ubuntu 26.10 and
Debian 13**. The base gate verifies PE and runtime identity; the additional
Descent 3 gate verifies its public ZIP and that its DLLs are identical to the
certified universal cores. Both must pass on the *same source commit*.

A certificate attests to **build identity only**. It is not a substitute for
real-game sound quality, A3D2 fidelity, license audit, antivirus testing or
security review. Descent 3 remains experimental.

## 4. Publish to GitHub Releases

The CI job uploads the platform-specific runtime ZIPs, public Descent 3 ZIPs,
PE evidence and two certificates as **workflow artifacts**. Those are **not
automatically GitHub Release downloads**. Once all five checks pass:

1. Use the exact public Descent 3 ZIP from a verified CI platform's artifact,
   not a manually repacked copy.
2. Check that its SHA-256 equals
   `DESCENT3_PUBLIC_RELEASE_VERIFIED.json` → `public_zip_sha256`.
3. Attach it to the GitHub **v0.9.2** release along with the approved regular
   runtime and clear **Experimental** compatibility notes.
4. Link [Descent 3 installation instructions](DESCENT3_PUBLIC_RELEASE.md)
   from the release description. Keep the two certificates with the release
   or in its release evidence, so anyone can check the hashes.

Do not claim a GitHub release exists until the maintainer has actually
published it. The source-first project must not redistribute proprietary
Miles DLLs, Descent 3 executable or game assets.

## Advanced

See [one-click build](ONE_CLICK_BUILD.md),
[cross-platform identity](CROSS_PLATFORM_REPRODUCIBILITY.md),
[developer index](DEVELOPER_INDEX.md), and
[historical build instructions](HISTORY_BUILD_AND_RELEASE_PRE092.md).
