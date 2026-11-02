# Aufake3D v0.9.0 byte-for-byte reproducible builds

## Reproducibility standard

For one exact source revision, unchanged source bytes and a **pinned** Clang/LLD
installation, the complete locally generated runtime ZIP and all generated PE32
executables/DLLs should have identical SHA-256 digests when compiled independently
in different directories. This standard is stricter than "the same exports" or
"the same compiler options".

Run the two-clean-tree proof locally:

```sh
python scripts/verify_reproducible.py --self-test
```

The command makes two fresh source copies, builds the same source twice (with
normal tests and optional CMake acoustics disabled **only for the duplicate
builds**), compares every generated `.exe` and `.dll`, and then compares the
**complete** runtime ZIP. It exits nonzero if any byte differs. In ordinary
`BUILD_WINDOWS.cmd`/`BUILD_LINUX.sh` builds, Python and acoustic test suites
still run normally. GitHub CI runs this reproducibility check after its usual
full build, so it is not a replacement for test coverage.

To compare runtime ZIPs generated on different machines:

```sh
python scripts/verify_reproducible.py --compare path/to/windows-runtime.zip path/to/linux-runtime.zip
```

Failures report the differing ZIP entries. Identical inner entries but different
ZIP metadata/compression are also reported as a failure.

## Issues fixed and already controlled

- The Alice 2000 bridge's separate link step previously omitted `/timestamp:0`.
  This allowed its PE header timestamp to change between otherwise identical
  builds, changing the runtime ZIP checksum. The bridge now uses a fixed zero
  timestamp just like the core and Miles proxy.
- The runtime packager sorts paths and explicitly controls ZIP timestamps,
  file permissions, compression mode and member content. It also writes a
  `LOCAL_BUILD_SHA256.json` manifest of every packaged file.
- Repository `.gitattributes` disables Git's implicit text conversion so that
  tracked source files are checked out with the same bytes on Windows and Linux.

## What is **not yet proven**

**Cross-platform reproducibility is not yet guaranteed.** Two installations of
Clang/LLD may emit different bytes when their versions or build flags differ,
even if both succeed and pass tests. Hosted GitHub Actions images can update
LLVM, Python and ZIP/zlib versions without changing the workflow YAML.

Before making Windows/Linux matching hashes a blocking release requirement:

1. Pin **exact** Clang and LLD versions (and distributions) on both platforms;
   record their versions and source revision with released checksums.
2. Ensure the same checkout bytes, architecture, flags, exported ABI and
   generator outputs; rerun clean-tree comparisons across two machines.
3. Compare full ZIP SHA-256 and all component hashes across Windows/Linux.
   Investigate any mismatches rather than updating expected hashes blindly.
4. Verify that an identical binary still passes real-game compatibility and
   the normal CI tests. Reproducible does not mean correct or safe.

CMake acoustics test executables are not currently included in the runtime ZIP.
They require a separate cross-toolchain reproducibility evaluation; the present
checker covers release PE components and the packaged runtime.
