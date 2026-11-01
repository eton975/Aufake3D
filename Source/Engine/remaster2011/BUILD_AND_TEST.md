# Alice 2011/VorpalFix selector bridge — offline engineering notes

The selector bridge is **game-version-specific**. It was written after disassembly
of a 1,668,472-byte `alice.exe` with SHA256
`08bcbe4b549633b24c90a1ab36bf516bd8873432c68b37248c98ee4225506e50`.
PE timestamp May 5, 2011; PE/i386; image base 0x00400000; relocations stripped.

## Original executable call mapping

At 0x00467492 the 2011 selector pushes a pointer to the string `A3D` at
0x005274e4 and calls the normal case-insensitive selector function. Its
original `a3d` case copies `Aureal A3D Interactive` from 0x005274cc into a
32-byte local provider-name buffer at [esp+0x20] and sets class ESI=5. It
has **no `a3d2` string**, although the original `SndDrivers/mssa3d2.m3d`
provider advertises `Aureal A3D 2.0 (TM)`.

The new suspended-child bridge checks the original code bytes, original string
and immediate fallback instruction, then overwrites only the 5-byte PUSH at
0x00467492 **in RAM** with JMP to a private stub. The stub recognises `a3d2`
and replaces the provider-name buffer, sets ESI=5, then jumps to 0x00467546
where the original provider open code continues. For any other name it executes
the original displaced `push 0x005274e4` and jumps to 0x00467497.

The on-disk game EXE, original Miles files, and VorpalFix winmm.dll are never
modified, and no global COM registration is attempted by the installer.

## Build

Requires Clang + lld-link (Win32 PE target) with no proprietary SDK:

```sh
cd remaster2011
bash build.sh
```

The included source is extensively commented. `build.sh` creates the
Win32/i386 `alice-a3d2011-bridge.exe`. The COM renderer is built separately:

```sh
cd win32
bash build.sh
```

## Offline tests

```sh
cd remaster2011
gcc -std=c11 -O2 -ffunction-sections -fdata-sections -Wl,--gc-sections \
  -Wno-attributes tests/test_selector_stub.c -o /tmp/test_selector_stub
/tmp/test_selector_stub
```

`test_selector_stub` actually calls the machine-code generator and asserts
all five conditional exits, provider bytes, class ID and both jump targets.
It **does not execute the Win32 launcher**, prove actual Wine behavior, or
prove that VorpalFix's own startup hooks won't conflict at runtime.

`tests/test_remaster_install.py` tests the real submitted EXE hash in the
sandbox, exact version pinning, safe installation, preserved VorpalFix files,
refusal of unsupported versions, duplicate files and safe uninstall. Set
`A3D_ALICE2011_EXE` to your own original for local runs.

## Known limitations

* There is no Wine/Proton installation or full retail assets available in the
  build environment. No actual 2011 in-game sound success claim is made.
* COM class activation through sidecar EXE manifest remains to be verified on
  the user's Wine prefix, and the v0.5 spatial renderer is not bit-exact A3D.
* There may be VorpalFix hook ordering interactions; collect an exception
  address and full Wine +seh log if startup fails.
* Only the exact submitted 2011 executable build is supported by the selector
  bridge; different EXE hashes must be disassembled and separately validated.
