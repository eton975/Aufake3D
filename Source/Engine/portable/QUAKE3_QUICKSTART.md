# Quake III Arena 1.17 — v0.6.0 FINAL

Only use the genuine 1.17 `quake3.exe` with compatible original PK3 assets. Installing an A3D DLL does not add an A3D backend to later revisions of Quake III.

```bash
a3dctl install q3 /path/to/A3D_v0.6.0_Final_Portable.zip
bash ./run_quake3_117_wine.sh "$HOME/Games/QuakeIII-117-A3D2/quake3.exe"
```

Enable `s_enable_a3d` inside Quake III; use `s_usingA3D` to inspect state. The launcher applies 48-tap HRTF, geometry retrace=4, reverb wet=0.14, 128 voices, 3 WaveOut queue headers and 5.0 master gain. **Turn down system volume before first run.** To reduce gain, prefix the command with `A3D_MASTER_GAIN=0.5`.

User tested this preset successfully in Demo 1 following the Hotfix 10 polygon-list API correction; other game content/configurations need validation.
