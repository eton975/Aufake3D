# Windows/Linux byte-for-byte reproducibility gate (Aufake3D v0.9.2)

The project has **two different verification scopes**. A local `BUILD_WINDOWS.cmd`
(or `BUILD_LINUX.sh`) runs the existing **three-build, same-host/same-toolchain**
verification, writes `dist/REPRODUCIBILITY_VERIFIED.json`, and **does not**
claim that another operating system's binaries have the same hashes.

The new `.github/workflows/source-ci.yml` has an independent release gate:

1. Builds the **same checkout** on `windows-2022` and `ubuntu-24.04`, running
   the existing local verification and tests on both platforms.
2. Both runners install **LLVM/Clang+LLD 19.1.7** through the same pinned
   third-party installer action commit (`ebc0426251bc40c7cd31162802432c68818ab8f0`).
   The Python interpreter is pinned to **3.13.7**. The emitter checks that
   both `clang` and `lld-link` really identify as 19.1.7 before producing
   build evidence. CI has fixed `PYTHONHASHSEED` and `SOURCE_DATE_EPOCH`.
3. Each runner writes `dist/manifest.json` containing SHA-256 hashes of **all
   git-tracked files as checked out**, all generated PE `.dll` and `.exe` files,
   and all members of the exact final runtime ZIP. It also records the exact
   raw ZIP SHA-256, full Python/LLVM versions, source Git commit, and the local
   verification result. It also stores a second deterministic ZIP of **every
   compiled PE DLL/EXE**, including files not present in the runtime ZIP. Both
   hosts upload the runtime ZIP, raw PE evidence and manifests separately.
4. A third **cross-platform-byte-identity** job downloads both artifacts,
   validates the manifests against the actual ZIPs, and **fails closed** if
   any tracked file, actual downloaded compiled PE, ZIP entry, archive byte,
   compiler version, Python version, or Git commit differs. The build evidence
   emitter refuses a dirty checkout, preventing an uncommitted source change
   from being mislabeled with a clean Git commit. The CI job also
   checks that both manifests identify **the exact Actions checkout commit**.
   On success only, it writes
   `CROSS_PLATFORM_REPRODUCIBILITY_VERIFIED.json` and publishes it as a
   separate artifact. The success certificate states an exact checked commit
   and runtime SHA-256. Any failed matrix job blocks the certificate.

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

To manually compare artifacts from both hosts after their local gates pass:

```sh
python scripts/verify_cross_platform.py emit --llvm 19.1.7 --out dist/manifest.json
```

Place each host's `manifest.json`, `Aufake3D_v0.9.2_Local_Runtime.zip`, and
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
