# American McGee's Alice 2000 — v0.6.0 FINAL

Classic game requires its original Miles `SndDrivers` files. After registering `alice2000` using `--profile alice` and installing from `A3D_v0.6.0_Final_Portable.zip`:

```bash
bash ./run_alice2000_wine.sh "$HOME/Games/ALICE/alice.exe" +set s_milesdriver a3d2
```

The included `alice-a3d-bridge.exe` changes a checked provider selector inside the spawned game's memory only. `alice-a3d2011-bridge.exe` is not interchangeable. Earlier iterations of the classic bridge worked, but this precise consolidated DLL has not been retested in complete classic gameplay. The Quake III tuning parameters are intentionally **not** globally enabled for Alice.
