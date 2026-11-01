# v0.4.0 build evidence

Rebuilt on 31 October 2026 using Clang/LLD targeting Windows 32-bit PE.

- `bash tools/verify_all.sh`: **exit 0**.
- Existing C/C++ DSP, streaming and acoustic tests pass (44 Python, four
  CTest, and native AddressSanitizer/UndefinedBehaviorSanitizer checks).
- New installer/export tests: **9/9 passed**.
- `objdump -p win32/build/a3d.dll` verifies the **five** original `a3d.dll`
  export names and ordinal positions, notably `_A3dCreate@12`, ordinal 6.
- `objdump -p win32/build/a3dapi.dll` verifies `DllGetClassObject` and related
  COM exports. All packaged DLLs and executable self-tests use PE32/i386.
- The installer checks exact executable patch bytes, refuses overwrites,
  retains original game files, and verifies checksums before uninstalling.

**Not tested:** Wine/Windows execution of the registration-free manifest,
Windows PowerShell installer, streaming audio during Alice gameplay, Quake III
A3D behaviour, or original AU8830 audio fidelity. There is no Windows/Wine
runtime installed in the build container. Do not claim playable or matching
original audio until external end-to-end validation succeeds.
