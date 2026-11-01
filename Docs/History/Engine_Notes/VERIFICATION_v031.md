# v0.3.1 verification record (31 October 2026)

## Verified in the build environment

- `bash tools/verify_all.sh` exit code 0.
- The 32-bit `a3dapi.dll` and seven diagnostic Windows executables build using Clang/lld-link as PE/i386 files.
- 44 Python regression tests pass.
- 4 CMake/CTest acoustic-engine tests pass.
- Native sanitizer-tested spatial, binaural, measured-HRTF, streaming-mixer and streaming-scene tests pass.
- The portable 24-source offscreen benchmark (`clang -std=c11 -O2 -Wno-unused-function tools/bench_stream_native.c -o bench && ./bench`) used approximately 0.302 CPU seconds to render 1.60 seconds of 48 kHz audio on this build host, not on an FX-6300 or Wine. This does not establish end-to-end low latency.
- `deliverables/SHA256SUMS.txt` was regenerated after copying the current rebuilt DLL and EXEs into the distribution directory.

## NOT verified

- No Wine or Windows runtime test of the **new streaming mixer** or the new IA3dList interface.
- No successful A3D2 playback inside Alice.exe from this version; earlier Alice startup still selected Miles Fast 2D.
- No completed multi-bounce Aureal Wavetracing or faithful historical room impulse response.
- No registration-free DLL drop-in behaviour on Windows 10/11.
- AU8830 hardware is not used and is not a dependency of this build.

A passed compilation or emulator unit test does not establish compatibility in a real game. Start with the existing isolated Wine prefix when the software reaches the next external validation gate; do not modify physical card drivers.
