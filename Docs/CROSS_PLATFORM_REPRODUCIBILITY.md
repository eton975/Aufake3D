# Windows/Linux byte-for-byte reproducibility gate (Aufake3D v0.9.2)

The project has **two different verification scopes**. A local `BUILD_WINDOWS.cmd`
(or `BUILD_LINUX.sh`) runs the existing **three-build, same-host/same-toolchain**
verification, writes `dist/REPRODUCIBILITY_VERIFIED.json`, and **does not**
claim that another operating system's binaries have the same hashes.

The `.github/workflows/source-ci.yml` gate is mandatory for five targets:
`windows-2022`, `ubuntu-24.04`, `ubuntu-26.04` (native hosted VM),
`ubuntu-26.10` (pinned Ubuntu container), and `debian-13` (pinned official
Debian 13 container). Both containers run on hosted Ubuntu VMs, but the
verifier authenticates their actual userspace via `/etc/os-release`; neither
an Ubuntu host nor a mislabeled container may impersonate Debian 13. The
container image OCI digests are fixed in the workflow.

The independent release gate:

1. Builds the **same checkout** on `windows-2022`, `ubuntu-24.04`,
   `ubuntu-26.04`, the pinned Ubuntu 26.10 container, and the pinned Debian 13
   container, running the existing local verification and tests in every build environment.
2. All five builds use byte-identical **LLVM/Clang+LLD 19.1.7** inputs.
   Windows and Ubuntu use the pinned upstream installer action commit
   (`ebc0426251bc40c7cd31162802432c68818ab8f0`). Debian 13 uses
   the much smaller checksum-pinned compiler with identical CI bytes.
   The Python interpreter is pinned to **3.13.7**. On Windows, the workflow
   uses `actions/setup-python`; on all four Linux builds and the final
   comparison job it uses pinned `astral-sh/setup-uv` (v9.0.0 at a full commit
   SHA) installing pinned `uv` 0.10.0 and the exact managed CPython 3.13.7.
   This avoids `setup-python`'s missing Ubuntu 26.04/26.10 archive entries.
   `scripts/ci_install_pinned_python.sh` verifies the interpreter's three-part
   version, activates it in `GITHUB_PATH`, and installs it under `RUNNER_TEMP`,
   outside the checkout. No system-Python or version-3.13 floating fallback is
   permitted. `setup-python` is still used on Windows, where the exact archive
   exists. The emitter checks that
   the `clang` and `lld-link` executables really identify as 19.1.7 before producing
   build evidence. CI has fixed `PYTHONHASHSEED` and `SOURCE_DATE_EPOCH`.
   The LLVM installer is explicitly directed to `${{ runner.temp }}/aufake3d-llvm`
   on every CI target, **outside the Git checkout**; this avoids copying a
   several-gigabyte toolchain into the two clean rebuild directories. The
   reproducibility verifier additionally excludes a root-level `llvm/` folder
   when it contains the actual LLVM binaries. The CI environment still uses
   the pinned compiler executable for every build and checks its version.
3. Each runner writes `dist/manifest.json` containing SHA-256 hashes of **all
   git-tracked files as checked out**, all generated PE `.dll` and `.exe` files,
   and all members of the exact final runtime ZIP. It also records the exact
   raw ZIP SHA-256, full Python/LLVM versions, source Git commit, and the local
   verification result. It also stores a second deterministic ZIP of **every
   compiled PE DLL/EXE**, including files not present in the runtime ZIP. All
   target jobs upload the runtime ZIP, raw PE evidence and manifests separately.
4. A final **cross-platform-byte-identity** job downloads all five artifacts,
   validates the manifests against the actual ZIPs, and **fails closed** if
   any tracked file, actual downloaded compiled PE, ZIP entry, archive byte,
   compiler version, Python version, or Git commit differs. The build evidence
   emitter refuses a dirty checkout, preventing an uncommitted source change
   from being mislabeled with a clean Git commit. The CI job also
   checks that all manifests identify **the exact Actions checkout commit**.
   On success only, it writes
   `CROSS_PLATFORM_REPRODUCIBILITY_VERIFIED.json` and publishes it as a
   separate artifact. The success certificate states an exact checked commit
   and runtime SHA-256. Any missing, failed or mismatching Ubuntu or Debian job blocks the certificate.

## LLVM 19.1.7 on Ubuntu 26.04 and 26.10 (v6)

The pinned upstream Linux LLVM 19.1.7 release requires the pre-2.14
`libxml2.so.2` ELF ABI. Ubuntu 26.04/26.10 instead use `libxml2.so.16` and
cannot load `lld-link` directly. This is an **LLVM host dependency**, not a
Windows DLL dependency. The CI jobs build the official GNOME libxml2 2.13.9
source archive with its published SHA-256 pin, with ICU/zlib/lzma disabled,
under the runner's temporary directory, then copy the real, verified `.so.2`
shared object into the mounted LLVM installation's private `lib/` directory.
This avoids the different host/container spellings of `runner.temp` across
GitHub job steps. The build exports `LLVM_PATH/lib` on `LD_LIBRARY_PATH`.
No system library is replaced, no
unverified `.so.16`-to-`.so.2` compatibility symlink is used, and no extra
shared object is distributed in any Aufake3D game kit. The script fails
immediately on a source checksum mismatch, unresolved ELF dependency, or if
LLD does not load the checked private library. This workaround is intentionally
not run on Ubuntu 24.04 or Windows.

**Reproducibility stays fail-closed:** the library is a pinned build input,
not a claimed cross-platform result. Every target still must produce the same
compiled PE files and byte-for-byte identical runtime ZIP before the CI
certificate can be issued. The library's locally built ELF bytes themselves
are not an Aufake3D release artifact.

## Why the release ZIP packaging changed

The runtime ZIP uses stored (`ZIP_STORED`) entries rather than zlib-compressed
ones; this intentionally trades a larger download for byte-level independence
from different Windows/Linux zlib versions. Every ZIP member has a fixed
2026-01-01 timestamp and explicitly fixed `create_system=3` and Unix
permissions on **both** platforms. File content, names and order are already
selected deterministically. The repository's existing `.gitattributes`
contains `* -text`, so `git` does **not** silently change checked-out file
line endings between Windows and Linux; the manifest verifies actual file
bytes in any case.

These choices remove predictable host-specific differences; **they do not
pre-assert** that all machine code will match. If LLVM embeds an additional
host detail, CI must fail, show which outputs differ, and be corrected before
claiming cross-platform certification.

## Using the evidence locally

A normal local build continues to verify three independent builds and should
**still** report that cross-OS certification is separate. To cross-certify,
inspect a **successful** `cross-platform-byte-identity` Actions job for the
exact commit and retrieve its `Aufake3D-cross-platform-verified` artifact.
A local build whose SHA-256 matches the certified runtime ZIP hash can then
be compared with that certified artifact. Merely running `BUILD_WINDOWS.cmd`
on one computer can never prove another computer's output.

For a diagnostic *pairwise* comparison (which cannot replace the mandatory five-target certificate):

```sh
python scripts/verify_cross_platform.py emit --llvm 19.1.7 --out dist/manifest.json
```

Place the two hosts' `manifest.json`, `Aufake3D_v0.9.2_Local_Runtime.zip`, and
`Aufake3D_Generated_PE_Evidence.zip` in separate directories,
`verification/windows` and `verification/linux`, then:

```sh
python scripts/verify_cross_platform.py compare --windows verification/windows --linux verification/linux --out verification/CROSS_PLATFORM_REPRODUCIBILITY_VERIFIED.json --expected-commit YOUR_EXACT_GIT_COMMIT_SHA
```

**Scope:** This certifies byte-for-byte Windows PE and runtime ZIP identity
for the named commit under the pinned CI toolchain. It does **not** certify
runtime/gameplay correctness, audio bit-exactness, Vortex 2 hardware
compatibility, security/antivirus acceptability, or identical outputs from
arbitrary compiler versions. Reproducibility is a property of a specified
source revision **and pinned inputs**, not of arbitrary hosts/tools.

A failed manifest-emission or certificate-comparison operation removes its
previous success output, so stale files cannot masquerade as new proof.

## Five-target certification (v4)

The final workflow uses `scripts/verify_matrix_reproducibility.py`, which
requires **all three** Ubuntu targets **and Debian 13**, authenticates each
recorded Linux OS release, reopens every downloaded PE evidence archive, checks
every raw ZIP against the Windows reference, and emits **one consolidated**
certificate only after all five independently built outputs match. A failed
attempt deletes any stale certificate. The Windows job remains the byte identity
reference, not a special renderer implementation.

The pinned local builder's existing v0.9.2 ZIP reference was originally
certified by four CI environments; that historical reference hash is not
silently rewritten. New CI certificates require five independent hosts.

To reproduce the matrix check manually, download the five CI artifacts and run:

```sh
python scripts/verify_matrix_reproducibility.py --windows verification/windows --linux-target ubuntu-24.04=verification/ubuntu-24.04 --linux-target ubuntu-26.04=verification/ubuntu-26.04 --linux-target ubuntu-26.10=verification/ubuntu-26.10 --linux-target debian-13=verification/debian-13 --expected-commit YOUR_GIT_COMMIT_SHA --out verification/CROSS_PLATFORM_REPRODUCIBILITY_VERIFIED.json
```

**This configuration is not itself certification:** CI must pass on all five
real environments before an official checksum-identical release can be claimed.
The digest-pinned 26.10 root filesystem and the pinned compiler/Python versions
constrain the inputs, while the strict output comparison detects any remaining
differences. The runner kernel, build packages and SDK/tool archives are not yet
fully content-addressed; all generated release bytes remain release-blocking.
