# Alice 2011: unified AU8830 renderer migration candidate (v0.9.0)

**Status:** built and source-tested; actual game and VorpalFix 4.2.1 playback
with the latest corrected renderer must be verified on Windows 10/11 before
replacing an existing known-good Alice 2011 installation. Wine is experimental.

## What *is* unified

All kits use the **same compiled** `a3d.dll` and `a3dapi.dll`: the 56-tap
AU8830-derived `reference` / `fast` signal paths, optional 48-tap `legacy`,
shared geometry, mixer, limiter and WaveOut queue. The build now refuses to
package any game kit containing a divergent renderer. `UNIFIED_ENGINE_SHA256.json`
in the runtime ZIP records the SHA-256 of the shared files and their copies
in all game kits (including Alice 2011 `SndDrivers/` copies).

The Alice 2011 *test candidate* launcher defaults to `reference` (56-tap),
without changing other games' launcher defaults. For a
controlled fast comparison, start PowerShell in the **test copy** and run:

```powershell
$env:A3D_HRTF_MODE = 'fast'
.\RUN_AUFAKE3D_WINDOWS.cmd
```

To use Reference, start a new PowerShell window with no override and launch
normally; or set `$env:A3D_HRTF_MODE = 'reference'`. The launcher only sets a
default when the variable is absent. Neither mode forces `s_milesdriver`.

## What must remain game-specific (for now)

The unmodified remaster `alice.exe` does not recognize the `a3d2` selector
without a compatibility hook. `alice-a3d2011-native.exe` is a checked,
child-RAM-only selector bridge. It is **not a different audio engine**. The
`mss32.dll` 331-export proxy, app-local COM manifests, and saved original
`SndDrivers/a3d_mss_real.dll` are also required for the specific Miles loader.
Removing them now would reintroduce broken or sticky provider selection.
There is no disk executable patch, forced FPS or `+set s_milesdriver a3d2`.

## Risk-controlled deployment

1. Keep the working Alice 2011 game folder **untouched** and make a separate
   copy for testing (complete original game and VorpalFix files; preserve game
   licenses and ownership).
2. Back up the test copy's DLLs, launch scripts, `SndDrivers` and configs.
3. Copy the `Alice_2011_VorpalFix/COPY_TO_GAME_FOLDER/` kit contents from this
   build's runtime ZIP into **the test copy only**. Do not replace the original
   Miles `a3d_mss_real.dll`. Refer to `Docs/MANUAL_INSTALLATION.md` for required
   original Miles positioning and app-local activation.
4. Check `UNIFIED_ENGINE_SHA256.json` for the two renderer DLL hashes. Select
   A3D2 in-game. Confirm actual stereo positioning and sound levels.
5. Switch **A3D2 -> Miles 2D -> A3D2 -> Dolby -> Miles 2D -> A3D2** without
   restarting; verify game and mixer behavior, using diagnostic logs if needed.
6. Exercise rapid head turns, weapon-heavy scenes and VorpalFix frame-rate
   controls at `reference`, then repeat at `fast`, in separately launched runs.
7. Only promote the candidate if all tests pass without new dropouts, latency,
   incorrect sound-provider choices or performance regressions.

Failure to pass in-game verification means keep the old Alice 2011 folder.
Success here does **not** imply broader A3D 3.0 or game compatibility.
