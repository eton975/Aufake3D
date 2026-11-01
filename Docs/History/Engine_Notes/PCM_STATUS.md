# A3D 2.0 source PCM integration: evidence and current limits

## User's Wine-Staging 11.19 test of v0.2.3

The archive `alice-a3d2-miles-wave-20261030T154455Z.tar.gz` confirmed:

- COM preflight exit 0; standalone Miles provider open 0;
- a position-only sample test completed and exited 0;
- a mono 8-bit, 22,050 Hz RIFF/WAV load request returned `SET_WAVE_FILE_RESULT=0` and error `Could not create secondary A3D buffer`;
- the Aureal DLL log included `IA3d4.NewSource => S_OK`, then `SetWaveFormat unsupported` and two `Lock unsupported` calls.

This is conclusive evidence of provider/source creation and an attempted buffer transfer, not successful PCM playback.

## v0.2.4 engineering changes

The A3D2 source object now owns a bounded in-memory PCM buffer. It accepts signed 16-bit and unsigned 8-bit uncompressed PCM (mono or stereo), stores the format, allocates up to 64 MiB, and provides safe circular Lock/Unlock slices with matching pointer/length validation. Full-buffer and from-write-cursor flags follow the preserved A3D 2.x SDK header (`A3D_ENTIREBUFFER=2`, `A3D_FROMWRITECURSOR=1`). It logs format fields, allocated byte count, lock lengths, and a reproducible FNV-1a checksum of the transferred bytes. It releases allocations on `FreeWaveData` and `Release`.

**No playable audio output exists yet.** `IA3dSource::Play` deliberately returns `E_NOTIMPL`. The historical API includes many unimplemented methods, and present geometry modelling is not yet attached to audio rendering.

## Independent checks performed here

- PE32/i386 DLL and diagnostic EXEs compiled using Clang + LLD.
- 27 Python checks passed (source and diagnostic contracts).
- Four acoustics CTest tests passed (including geometry-OBJ obstruction).
- Host-native C source-buffer test passed with ASan/UBSan: allocation, formats, full/wrap locks, mismatched Unlock, release, and size limits.
- Actual Wine/Miles interoperability for v0.2.4 **has not been tested locally** because Wine is unavailable in this environment.

## Next user test, if desired

```bash
bash tools/wine_miles_wave.sh '/home/youruser/Games/Alice/Alice.exe'
```

This runs three separate no-playback processes: `position`, `wave` (8-bit silent PCM), and `wave16` (16-bit silent PCM). It creates `~/alice-a3d2-miles-wave-<timestamp>.tar.gz`. A successful `SET_WAVE_FILE_RESULT` or no reported Miles error means Miles accepted the data, **not** that the program rendered sound. The launcher leaves Alice.exe, the game files, and the AU8830 system driver unchanged.
