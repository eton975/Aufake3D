# Build Aufake3D v0.8.14-RC1 from source

From the repository root on a Unix-like system with Python 3, Clang/LLD
supporting `i686-pc-windows-msvc`, plus CMake/Ninja for acoustic tests:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/build_engine.py
python3 Source/Alice2011_NameFix_v089/build_proxy_from_export_map.py --output ./dist/miles-repro
cmake -S Source/Engine/acoustics -B build/acoustics -G Ninja
cmake --build build/acoustics
ctest --test-dir build/acoustics --output-on-failure
```

Core outputs: `dist/core/a3d.dll` and `dist/core/a3dapi.dll` (Win32 PE32).
The Miles proxy builder outputs `mss32.dll` from the published 331-export
interface map, without copying a vendor implementation. To run Alice 2011,
you still need the original, legally owned compatible Miles DLL as described
in the separate full-runtime manual; it is not included here.

Compare built core hashes to `CORE_BINARY_HASHES.json` using the included
source verifier: `python3 Tools/check_core_binary_hashes.py` (after the
build). This RC's source comments must not change the byte-for-byte output.
Run the CMake tests and preserve original KEMAR attribution; see
`Docs/BUILD_AND_RELEASE.md` and `Docs/REPRODUCIBILITY.md`.

The source-only archive does **not** contain `Game_Kits/` or proprietary game
files. For actual installation use the separately reviewed full binary asset.
Reproducibility is not proof of security clearance or game support.
