# Verification

- Built 32-bit PE/i386 `a3dapi.dll` with Clang/lld-link using existing scripts.
- Preserved Hotfix 1's optional second output pointer lock behaviour.
- Passed 58 source/tools tests, 15 portable installer tests, 9 drop-in tests, and 7 Alice 2011 tests (89 Python tests total), plus build-time PE32 checks.
- These tests do not execute Wine nor reproduce actual Quake III streaming; audible results remain experimental.
- `A3D_WAVEOUT_QUEUE_HEADERS` caps in-flight WaveOut submissions; it does not guarantee an OS audio latency or correct Quake III's playback cursor under every configuration.
