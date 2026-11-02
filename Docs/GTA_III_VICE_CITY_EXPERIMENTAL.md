# GTA III and Vice City: experimental Aufake3D v0.9.x integration

**Not officially supported or gameplay-verified yet.** GTA III was reported mostly
functional by an external v0.8.x tester; no reproducible validation log exists.
Both original PC games use Miles Sound System and expose A3D 1.x/2.0 providers.

1. Make a **separate test installation** of an original PC edition; record EXE,
   original `mss32.dll` and original `mss/mssa3d2.m3d` SHA-256 plus game version.
2. **Never replace original `mss32.dll` or `.m3d` providers with Alice's Miles
   proxy.** These new kits do not contain a Miles proxy or a game executable.
3. Check for pre-existing `a3d.dll`, `a3dapi.dll` or `gta3.exe.manifest` /
   `gta-vc.exe.manifest`; back them up first. Avoid overwriting unknown manifests.
4. Copy the *contents* of the matching `Game_Kits/GTA_III/COPY_TO_GAME_FOLDER/`
   or `Game_Kits/GTA_Vice_City/COPY_TO_GAME_FOLDER/` beside the original EXE.
5. Run `RUN_AUFAKE3D_WINDOWS.cmd` or `RUN_AUFAKE3D_WINE.sh`. In game choose
   authentic **A3D 2.0** if present; do not relabel another provider.
6. Verify **actual A3D COM calls and active voice rendering**, not merely a
   selectable sound provider. Compare listener rotation, left/right/front/back,
   weapon/explosion/vehicle sounds, radio/dialogue continuity and heavy CPU load.
7. To roll back, restore backed-up files and remove the added launchers/manifest;
   original Miles and game files must remain untouched.

The launcher defaults to `reference` 56-tap (override with `A3D_HRTF_MODE=fast`
or `legacy`), the normal 6×256/48-kHz WaveOut queue and master gain 5.0.
The manifest is experimental: app-local COM activation can depend on how the
original executable and audio providers load DLLs. If the game does not make
A3D API calls, this kit is a **negative probe**, not a working integration.

Use `python Tools/scan_game_a3d_markers.py <game directory>` for a read-only
static marker report; marker presence cannot prove that the runtime used A3D.
