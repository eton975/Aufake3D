# v0.8.14-RC1 reproducibility and scope

This RC preserves the successfully tested v0.8.12 RC1/v0.8.13 A3D core and
v0.8.9 Miles proxy **byte-for-byte**. Source changes are commentary and
documentation, not renderer logic or ABI edits.

| Core | SHA-256 |
|---|---|
| `a3d.dll` | `9291fd3e74eb43b129d1ff9713f979b6f9f25723f78300c8f4b2ed8e5bbeccd0` |
| `a3dapi.dll` | `2e6f500e8d86b641d702f21cbfa2662f6327e15c794af7c07745c24cba8e8db2` |

`python3 scripts/build_engine.py` produces these Win32 binaries on the tested
Clang/LLD toolchain. The separate vendor-free export-map builder rebuilds
the pinned `mss32.dll` bridge byte-for-byte with `331` public ABI exports;
**the original game-owned Miles DLL remains a runtime requirement**. A
historical v0.8.11 build mismatch does not affect the current pinned hashes.

Reproducible output hashes establish toolchain equivalence only; they do not
constitute antivirus clearance, a legal opinion or proof of game compatibility.
See [BUILD_AND_RELEASE.md](BUILD_AND_RELEASE.md).
