# Descent 3 experimental binary build — source-owned, optional

**STATUS: EXPERIMENTAL. Not playable Descent 3 support and not a game DLL.**

This separate opt-in target creates a persistent synthetic Aureal A3D 2.0 COM
probe executable, a **standalone ABI-shim COFF object** of the proposed Descent 3
source adapter, two already-built Aufake3D core DLLs, and a machine-readable
SHA-256 build manifest. No retail Descent 3 files or Aureal proprietary DLLs
are required or modified.

## One-click build

From the **Aufake3D repository root**, first build the main engine once if
`dist/core/a3dapi.dll` or `dist/core/a3d.dll` is missing. Then:

On Debian 13, Ubuntu or another supported Linux x86-64 host:

```sh
./BUILD_DESCENT3_EXPERIMENTAL_LINUX.sh
```

On native Windows 10/11 (double-click or execute):

```cmd
BUILD_DESCENT3_EXPERIMENTAL_WINDOWS.cmd
```

Both launch `scripts/build_descent3_experimental.py`, which **automatically
uses the exact SHA-256-checked LLVM 19.1.7 Clang and LLD tools from
`scripts/build_pinned.py`**, with the existing independent LLVM upstream
fallback. Compiled code targets **Windows x86 PE/COFF**, even on Linux.

This script builds two independent copies of the C++ adapter and requires
byte-for-byte identical `.obj` output. It invokes the existing Descent 3
contract-probe builder, which independently compiles and checks two identical
PE32 executables. Any compiler error or mismatch fails the opt-in build.

To examine only the probe/adapter and omit a missing core DLL, add
`--probe-only` (the executable then cannot run until `a3dapi.dll` is copied
alongside it from a build you trust).

## Generated files

All retained in `dist/descent3/`:

- `a3d-descent3-contract-probe.exe`: 32-bit Windows console application
  testing A3D2 COM activation, geometry and PCM source contracts. **Not the
  Descent 3 game executable.**
- `descent3-aureal-standalone-adapter.obj`: standalone compiler/ABI smoke
  object using `AUFAKE3D_ADAPTER_STANDALONE`; it is **not yet linked against
  the real Descent 3 engine** and cannot simply be copied into a game folder.
- `a3dapi.dll` and `a3d.dll`: copies of your built **Aufake3D** DLLs; not
  official Aureal or Descent 3 DLLs. Their hashes are recorded.
- `EXPERIMENTAL_BUILD_MANIFEST.json`: compiler binary hashes, exact input
  source hashes, output SHA-256, cross-check statuses and explicit unsupported
  claims.
- `README_EXPERIMENTAL.txt` and `RUN_PROBE_WINDOWS.cmd`: how to run the
  opt-in diagnostic and its limitations.

If Wine has 32-bit support, run the synthetic probe on Linux:

```sh
cd dist/descent3
wine ./a3d-descent3-contract-probe.exe
```

It does **not** play sound by default. `--audio` explicitly enables a brief,
moderate-level synthetic tone, and still does not test a real game.

## Certification and safety boundary

This directory is **not** included in the production v0.9.2 runtime ZIP or
game kits. The certified 20-PE inventory explicitly excludes `dist/descent3/`
and the older `dist/experimental-descent3/` optional probe tree; all regular
engine products remain in the strict three-build/cross-host certificate.

The independent two-build probe/object comparison is useful for detecting
instability, but is **not** a replacement for gameplay tests, a certified
Descent 3 adapter integration or the main five-platform CI certificate.

For a genuine source-integrated engine, consult
`Integrations/Descent3_Source/README.md` and its guarded
`install_into_checkout.py`; the actual historical source-engine compilation
must be carried out in an appropriate Descent 3 source checkout with its
own dependencies. No game executable is patched or rebranded.
