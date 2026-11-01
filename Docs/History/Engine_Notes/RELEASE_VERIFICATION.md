# v0.6.0 consolidated release verification

- This source is derived from the Hotfix 10 sources, not the abandoned Hotfix 8 one-shot tail branch.
- The distributed Win32 `a3dapi.dll` is exactly the user-tested Hotfix 10 binary; its SHA-256 is `45ec13448cc4fc728c3fe99c375f9589ddc3341c8c10ea8d84580866a569bd73`.
- Full build checks are **offline**. They do not run game executables, VorpalFix or Wine.
- User reported Quake III 1.17 Demo 1 completion with Hotfix 10 and superb perceived audio when `A3D_GEOMETRY_RETRACE_BLOCKS=4`, `A3D_REVERB_WET=0.14`.
- Earlier classic Alice bridge has established functionality, but complete Alice2000 + v0.6.0 final DSP has not been recently regression-tested by the user.
- Exact-hash Alice2011/VorpalFix bridge is still experimental for in-game functionality.
- For each game: game executables, original Miles, VorpalFix, PK3 assets are not bundled.
- Rebuilds embed time-dependent PE header timestamp, so rebuilt DLL hashes can differ in timestamp bytes from the archived release binary. Source is the same.
