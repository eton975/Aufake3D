# A3D 2.0 v0.4.6 — gain troubleshooting build

No changes to Alice executable, provider-selection bridge, or original Miles modules.
This diagnostic release retains the v0.4.5 post-spatial boost and linked limiter.

Changes:
- Read `A3D_MASTER_GAIN` at first mixer initialization, even if the game omits `IA3d4.Init`.
- Accept `A3D_MASTER_GAIN` between `0.1` and `5.0` (prior accepted range `0.5`–`2.5`; out-of-range settings silently reverted to 1.5).
- Record requested environment value and effective gain in `a3d-game-*.log` (`x1000` units).
- Track limiter-active frames and peak-limiting events for potential loudness masking.

**Does not automatically prove a fix:** if the environment isn't present in the Windows process, the wrong DLL is loaded, or the output limiter is engaged constantly, a gain change may still be inaudible. The logs are intended to isolate the cause.

## Test
With game closed and existing `a3dapi.dll` backed up, replace only that DLL. Run the working bridge launcher **from the same terminal** with:

```
A3D_MASTER_GAIN=0.2 bash ./run_wine.sh "$HOME/Games/ALICE/alice-a3d-bridge.exe"
```

Play an identifiable in-game A3D sound, exit, inspect latest `~/Games/ALICE/a3d-game-*.log` for `A3D.MasterGain.*`, `IA3dSource.Play`, and `A3D.Mixer.*`.
Then restart the game with `A3D_MASTER_GAIN=3.0` and compare the identical sound. Lower system/headphone volume BEFORE the latter test.

The sound must become substantially different **if the code path and environment variable are effective and the limiter is not holding the peaks down**.

Rollback: restore previous `a3dapi.dll`; do not overwrite `alice.exe`, the bridge, or SndDrivers files.
