# Quake III Arena 1.17 immediate A3D crash — v0.6.0 hotfix 1 engineering report

The source binary is the exact user-supplied `quake3(2).exe` with SHA256
`2d4eed8b1223a3d79fb4c8b273651674751783afaca2774f3a5f076d58ae7123`.

The Wine exception records EIP 0x00431087, EDI 0x1138 and ECX 0x800.
At this site `mov dword ptr [edi+ecx*2-4],edx` writes to 0x2134; this is
Quake III's 16-bit stereo PCM paint loop. It is not a DLL code location.

Path identified by original executable disassembly:

  0x447d20: A3D-specific SNDDMA_BeginPainting; calls 0x4020c0
  0x4020c0: `IA3dSource::Lock`, vtable slot 11, with (source,0,wave_size,
             &primary_ptr, &primary_len, NULL, NULL, 0)
  0x4020ef..0x402115: wrapper ignores underlying negative HRESULT and
             returns 0 (success) regardless.
  0x447dc0: caller trusts the output pointer and stores it as dma.buffer.
  0x431110..0x4311d4: mixer writes via dma.buffer, crashing at 0x431087.

Original v0.6.0 source (`win32/source_probe.inc`, `sr_lock`):

  if (!a || !an || !b || !bn) return E_POINTER;

This refuses Quake's legitimate single-region Lock and leaves primary pointer
uninitialized. Fix allows NULL second-region outputs if the write does not
wrap and maintains an error for wrapped locks that require those outputs.

Build validation: PE32/i386 `a3dapi.dll` compiled with Clang+lld-link; legacy
and both Alice selector binaries unchanged in the portable release. All
82 existing/new offline Python regression tests and native selector stub
passed. `a3d-quake3-lock-test.exe` is a dedicated Windows COM probe compiled
against exact Quake III 1.17 Lock and Unlock ABI. Actual execution under Wine
or retail game playback is **not** claimed: no Wine available in build environment.

This hotfix is still tagged **v0.6.0** internally because it is an additive
API correctness patch to the existing build; release ZIP names carry
`Quake3_Lock_Hotfix1` to distinguish its binaries from previous v0.6.0.

The old v0.6.0 installer has hash-protected uninstall records. Always uninstall
the original using its own receipt/installer before installing the hotfix.
No modifications to stock `quake3.exe` or game files are needed.
