# Experimental A3D game-local deployment — 0.4.1

**Status: buildable, not yet proven playable inside Alice or Quake III.** This
package is a testable drop-in candidate, **not** a completed A3D 2.0 emulator.
No retail game, Aureal VxD or proprietary Miles binary is distributed.

## What you get

- `bin/a3dapi.dll` — 32-bit Windows COM A3D2 wrapper with the v0.4.1 real-time
  multivoice renderer, measured KEMAR HRTF convolution, first-order reflections,
  occlusion and approximate late reverb.
- `bin/a3d.dll` — **separate** 32-bit legacy `A3dCreate` compatibility DLL for
  old Quake III builds using the Aureal 1.x/DirectSound ABI. This DLL delegates
  DirectSound creation to the system and is **not** the A3D2 Wavetracing engine.
- `*.exe.manifest` — game-local *attempt* at COM registration-free activation;
  Windows can prioritize an embedded executable manifest instead. Live testing
  on Windows 10/11 and Wine remains essential.
- `install.py` — cross-platform game-local installation and safe uninstall;
  creates separate optionally patched Alice executable, never edits Alice.exe.
- `install_alice_windows.cmd`, `install_quake3_windows.cmd` — Windows 10/11
  PowerShell-backed installers; do not require admin rights or Python.
- `test_regfree_wine.sh` — **fresh-prefix** Wine COM verification that cannot
  silently fall back to COM registration from earlier research tests.

## Debian/Wine install (uses your *own* installed game)

```bash
python3 dropin/install.py --game '/path/to/Alice.exe' --kind alice --patch-alice
bash dropin/test_regfree_wine.sh
bash dropin/run_wine.sh '/path/to/Alice-A3D2.exe'
```

For old Quake III (the actual Quake III Arena executable, **not Alice.exe
renamed**):

```bash
python3 dropin/install.py --game '/path/to/quake3.exe' --kind quake3
bash dropin/run_wine.sh '/path/to/quake3.exe'
```

Note: **A3D support was removed in later Quake III releases and some source
ports**. This cannot be repaired merely by copying a DLL. The Quake III bridge
currently supplies a DirectSound compatibility path, not original Vortex 2
HRTF/Wavetracing. Choose an A3D-enabled game version or a suitable source
port if investigating full Quake III A3D2 separately.

For registration-free testing, `test_regfree_wine.sh` intentionally creates a
new disposable prefix. If the test fails, it does not mean the older registered
Wine research kit was broken. It means the proposed **drop-in** activation path
is not established in that environment.

## Windows 10/11

Drag your **original** Alice.exe onto `install_alice_windows.cmd`. It refuses
existing DLL/manifest names; move existing files to a safe backup yourself.
It creates `Alice-A3D2.exe` and its app-local manifest. Run that new executable.
The original Alice.exe stays unchanged.

For Quake III, drag the old A3D-enabled `quake3.exe` onto
`install_quake3_windows.cmd`.

These scripts do not alter the Windows registry or install a driver. If your
Windows build ignores the sidecar manifest, app-local COM still will not load;
we will need to debug activation on that build. **Do not install the original
Windows 9x drivers on modern Windows.**

## Uninstall on Linux/Python

```bash
python3 dropin/install.py --game '/path/to/Alice.exe' --uninstall
```

The uninstaller removes only files whose SHA-256 matches the installation
record, and aborts if files have changed. A PowerShell install can be reversed
by deleting only its newly created files after verifying none existed earlier.

## Known limitations (critical)

- No gameplay launch has yet verified v0.4.1's real-time mixer or geometry
  lists. The implementation is compiled and offline-tested, not a proven game fix.
- Registration-free COM is unverified under Wine and Windows 10/11.
- The old Quake III `A3dCreate` ABI uses the legacy bridge; it does not expose
  the modern emulator's Wavetracing path.
- Alice's A3D detection patch only applies to the exact recognised bytes; no
  unknown game version is modified.
- Actual A3D2 source/geometry calls and filters need an in-game trace; this
  build will not be bit-identical to Vortex 2 hardware.

Source is available in `win32/`, `acoustics/`, `tools/` and `dropin/` of the full
package under its documented licences. The original drivers are not included.

The Wine game launcher defaults to a **separate**, persistent prefix at
`~/.local/share/a3d-dropin/wineprefix-v040`. This avoids accidentally
activating an older A3D DLL registered in the previous research prefix. Override
only if you explicitly want to test another prefix using `A3D_DROPIN_WINEPREFIX`.

### Optional Windows 10/11 fallback if app-local COM manifests are ignored

`optional_register_windows.ps1` can register **only** the project DLL for the
current user in the 32-bit COM view. Run it explicitly with PowerShell and
`-GameDir 'C:\Path\To\Alice'`. It refuses to replace an existing class
registration and offers `-Unregister` which removes only a matching entry. The
fallback is deliberately **not** run by the normal drop-in installers because
it is no longer registration-free. On Wine, prefer investigating a fresh-prefix
manifest failure first; don't apply Windows registry instructions blindly.

## What changed in 0.4.1

`a3dapi.dll` now uses per-source minimum/maximum distance, optional A3D Doppler, and listener-relative sources in the binaural PCM mixer, with source IDs logged for gameplay tracing. The original game must first **choose the A3D2 Miles provider**; these changes do not force a game that is still selecting Fast 2D into the A3D path. Test only with volume low at first.

**Upgrade caution:** The installer still uses `.a3d-dropin-v040.json` as its safety/ownership record for compatibility with the previous version. Uninstall a prior test build using the matching original installer before installing v0.4.1; it will refuse to overwrite existing DLLs.


See `../portable/README.md` for the new game-neutral v0.5.0 installer.
