# Aufake3D v0.8.13 — source and full binary candidate parity

This **source-only GitHub repository** is the matching source edition for `Aufake3D_v0.8.13_Full_Runtime_Binaries_Rebuilt_Source.zip` (separate distribution). The binary candidate is for developer/public testing, **not independently certified safe**; its rebuilt legacy bridge executables may trigger antivirus heuristics because they change child game process memory.

## Critical build inputs added since the initial source-only ZIP

- `Source/Alice2011_NameFix_v089/MILES_EXPORT_SURFACE_331.json` — proxy export names/ordinals, with no vendor DLL contents.
- `Source/Alice2011_NameFix_v089/build_proxy_from_export_map.py` — standalone Clang/LLD PE32 builder for the exact scoped Miles proxy.
- `Docs/BINARY_ORIGINS.json` — hashes, source origin and status of selected files in the separately distributed full binary candidate.

## Independently reproducible hashes

| File | SHA-256 |
|---|---|
| `a3d.dll` | `9291fd3e74eb43b129d1ff9713f979b6f9f25723f78300c8f4b2ed8e5bbeccd0` |
| `a3dapi.dll` | `2e6f500e8d86b641d702f21cbfa2662f6327e15c794af7c07745c24cba8e8db2` |
| Alice 2011 Aufake3D `mss32.dll` proxy | `8bc83f25b228849693ef187877388f917d7a5e3475f7db5e0cf9fa9b708426b8` |

Build core with `python3 scripts/build_engine.py`; build the proxy with:

```sh
python3 Source/Alice2011_NameFix_v089/build_proxy_from_export_map.py --output build/miles-proxy
```

The proxy build needs Clang/LLD but **no proprietary DLL at build time**. Running Alice 2011 still needs the original legitimate Miles vendor DLL as `a3d_mss_real.dll`. See `BUILDING.md`.

**Scope and cautions:** Original vendor SDKs, Miles DLLs, game executables and VorpalFix files are not in the source package. The use of SDK interface definitions during development is not a clean-room process. Proposed MIT terms remain contingent upon appropriate rights-holder approval; KEMAR measurements have separate attribution terms. Reproducible compilation and static import checks do not amount to AV clearance.
