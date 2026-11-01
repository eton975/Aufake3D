# v0.8.11 provenance and build notes

The shared audio core sources remain in `Engine/`; this release ships byte-identical `a3d.dll`/`a3dapi.dll` binaries from the working v0.8.9/v0.8.10 pipeline. The v0.8.9 Miles proxy and complete available implementation source are in `Alice2011_NameFix_v089/`. The original 32-bit vendor Miles DLL/export table is not included; reconstructing the proxy export list requires a **legitimately owned original matching Miles DLL**, as described in `README_SOURCE.md`.

`Tests/test_identity_v0811.py` and `Tools/check_game_identity.py` were added to analyze actual provider trace semantics, detect incorrect handle substitution or cosmetic-only name changes, and record Alice 2000 uncertainty. On Windows there is a parallel read-only PowerShell audit that needs no Python. No new DSP algorithm or A3D 3.0 implementation is claimed in this release.

**Reproducibility:** source disclosure and bit-for-bit reproducibility are distinct. For this frozen build, compare prebuilt binaries with hashes in `RELEASE_FREEZE.json`, then use the upstream build recipes and original compatible SDK/Miles dependencies to build locally as licensing permits. Exact byte-for-byte reproduction has not been independently demonstrated on Windows in this session.
