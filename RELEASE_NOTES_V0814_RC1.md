# Aufake3D v0.8.14-RC1 — Documentation and maintainability RC

## Changes from v0.8.13

- Replaced outdated top-level build/source introductions with a coordinated
  developer index and detailed guides for COM ABI, PCM/source ownership,
  WinMM worker timing, HRTF/geometry, Miles naming and source reproducibility.
- Added targeted inline contract and concurrency comments to high-risk C
  modules and installer docstrings; no new runtime code paths were introduced.
- Moved 67 legacy engine-era Markdown files to `Docs/History/Engine_Notes/`
  intact and published a history index.
- Updated installer receipts, script labelling and layout metadata for the
  v0.8.14-RC1 package. Existing v0.8.13 scripted installs need rollback
  under their original installer before reinstallation.
- Retained byte-identical v0.8.13 `a3d.dll`, `a3dapi.dll`, pinned 331-export
  Miles name-fix proxy and rebuilt legacy launcher binaries.

## Validated scope

Windows PE32 source cross-build, independent acoustics tests, source tests,
release layout/rollback checks, and Git source-clone verification are part
of packaging validation. The user-tested Alice 2011 audio behaviour is from
v0.8.12 RC1 with the **same runtime hashes**; v0.8.14-RC1 was not separately
run on the user's Windows/Wine machines. A3D 3.0 remains incomplete.

## Security and licence

This is a **binary-review candidate**, not antivirus-cleared. The original
v0.8.13 full archive received VirusTotal heuristic detections on several
process-modifying helpers. Rebuilding executables does not establish they
are safe; review `Docs/BINARY_COMPONENTS_AND_SECURITY.md` before release.
The MIT licence remains subject to ownership/rights-holder approval, with
KEMAR attribution separately documented.

**This source-only edition omits all prebuilt executables/DLLs.**
