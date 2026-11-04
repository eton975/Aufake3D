# v0.9.2b: LLVM installation without deprecated Node.js 20 actions

The four GitHub Actions warnings in the `ubuntu-24.04`, `ubuntu-26.04`,
`windows-2022`, and pinned `ubuntu-26.10` container jobs came from the pinned
`KyleMayes/install-llvm-action@ebc0426251bc40c7cd31162802432c68818ab8f0`
(v2.0.9), whose action metadata specifies `runs.using: node20`.

The two shared workflow installer steps now invoke
`python scripts/ci_install_pinned_llvm.py` after installing Python 3.13.7.
This script calls the project's existing `scripts/build_pinned.py` LLVM
installer, so each target downloads its **official upstream LLVM/Clang+LLD
19.1.7 archive**, verifies its **pinned SHA-256 before extraction**, and adds
its binaries to the GitHub Actions PATH. It publishes `LLVM_PATH` and, on
Linux, `LD_LIBRARY_PATH`. Downloads/extracted files live below `RUNNER_TEMP`,
not inside the Git checkout, to prevent clean rebuilds from copying gigabytes
of compiler files. No Node.js-based third-party LLVM installer remains in the
CI build jobs; this is not a warning-suppression environment variable.

Ubuntu 26.04 and 26.10 retain their dedicated pinned `libxml2.so.2`
compatibility preparation steps. The Debian 13 container retains its existing
checksum-verified LLVM installation. All OS identity checks, pinned Python
checks, compilation, local independent clean rebuilds, generated PE hashes,
and cross-OS byte-identical release gate remain mandatory.

**Validation limit:** Repository-level smoke tests and static workflow checks
can validate the removal and helper's exports. A GitHub Actions run is still
necessary to confirm that all remote compiler downloads, Linux shared-library
compatibility, and cross-platform reproducibility checks actually pass.
