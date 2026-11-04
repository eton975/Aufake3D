# Reproducible source and release verification

## Toolchain and baseline

The public build produces **32-bit Windows PE**, not Linux native `.so`.
The same DLLs may be loaded through Wine with appropriate native overrides.
Use Python 3, Clang targeting `i686-pc-windows-msvc`, LLD and CMake for the
independent acoustic library. The exact 39-step recipe is in
`Source/Engine/windows-build-recipe.json`. Build from the root:

```bash
python3 scripts/build_engine.py
python3 -m unittest discover -s tests -v
cmake -S Source/Engine/acoustics -B build/acoustics -G Ninja
cmake --build build/acoustics
ctest --test-dir build/acoustics --output-on-failure
```

A frozen release requires extra checks:

```bash
python3 -m unittest discover -s release_tests -v
python3 Tools/verify_release.py
python3 Tools/verify_git_checkout.py
```

The above verifier tools are distributed with the **full** package; the
source-only edition has its own source-focused verifier. See `BUILDING.md` for
an exact workflow for the package in hand.

## Audio binary identity

The **v0.8.14-RC1** build deliberately retains the exact v0.8.13 working core
binaries: no audio logic or DllMain/COM exports were changed. This edition's
updates are source comments, docs, installer metadata and packaging.
Compile the engine and compare the output hashes against `CORE_BINARY_HASHES.json`
(in the source repository) or `Universal_Core/` (full release). A comment-only
code change must not alter the PE output; if it does, halt publication and
investigate toolchain or build-step differences.

## Build the vendor-free Miles forwarding proxy

```bash
python3 Source/Alice2011_NameFix_v089/build_proxy_from_export_map.py \
  --output ./dist/miles-repro
```

This uses the included 331-export map and **does not package or generate** the
original proprietary Miles DLL. Its output is a bridge DLL and still requires
a legitimately obtained compatible game DLL at runtime. Compare against the
pinned proxy hash before use. Do not use historical private-vendor build steps
as the default GitHub workflow.

## CI, release assets and provenance

- GitHub source ZIP: no prebuilt Windows binaries; test from a fresh **Git
  clone** because Git ignores, line endings and packaging can differ.
- Full runtime ZIP: separately checksum all file entries, all core copies,
  the Miles proxy and the ready-to-copy game kits; check installer rollback.
- Preserve `LICENSE`, `LICENSE_SCOPE.md`, `THIRD_PARTY_NOTICES.md` and
  provenance documentation. The current MIT grant must be approved by the
  actual rights holder; code review is not legal approval.
- Source reproducibility and benign-looking imports are **not** antivirus
  clearance. Legacy memory-writing adapters require separate security review.
- Never claim gameplay tests you did not run. Alice 2011 Windows is the only
  user-confirmed good-playback profile for this exact audio core.
