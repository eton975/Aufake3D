# Build Aufake3D on Windows or Linux

**One-click build:** `BUILD_WINDOWS.cmd` on Windows 10/11, or
`./BUILD_LINUX.sh` on Linux. Both call the documented cross-platform
orchestrator `scripts/build.py` and assemble the four game kits and all
redistributable auxiliary Win32 EXEs from source. The output is Windows x86
PE32 (not a Linux `.so`). Full instructions: **[Docs/ONE_CLICK_BUILD.md](Docs/ONE_CLICK_BUILD.md)**.

Quick checks:

```bash
python3 scripts/build.py --doctor
python3 scripts/build.py
```

The A3D core needs Python 3.10+, Clang and LLD. Visual Studio Build Tools
are optional for Windows-only native CRT tests; the engine itself does not
use the Microsoft CRT. The build uses source-owned templates and does not
require an older compiled release, original Aureal SDK, game EXE, or vendor
Miles DLL. The latter must still be supplied separately **at game runtime**.

For historical byte-for-byte verification only, add
`--strict-frozen-hashes`. A normal local development build verifies the
331-export Miles ABI but merely warns on a frozen binary SHA mismatch, since
upgrading the LLVM toolchain can change PE output bytes. Passing compile
and unit tests does **not** mean the software was verified in gameplay or
cleared by antivirus. See `Docs/BUILD_AND_RELEASE.md` and licensing notices.
