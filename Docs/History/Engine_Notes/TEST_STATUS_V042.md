# v0.4.2 local verification

- `bash win32/build.sh` passed. The rebuilt `a3dapi.dll` is PE32/x86.
- `bash tools/verify_all.sh` passed: compiled DLL and programs, sanitized native
  spatial/binaural/mixer tests, CMake acoustics tests, 45 Python source tests and
  9 installer/binary tests.
- No Wine runtime or American McGee's Alice launch was performed in this environment.
- The implementation is experimental and is not an exact AU8830 emulation.
