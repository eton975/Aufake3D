# Create a candidate overlay for another A3D game

Requires Python 3; no third-party Python packages. These tools do not modify the installation.

```text
python tools/scan_a3d_clients.py "C:/Games/Example" --out example-evidence.json
python tools/stage_generic_candidate.py "C:/Games/Example" --exe example.exe --out "C:/A3D-test-overlays/Example"
```

Use the directory containing the executable; for Unreal-style layouts this is normally System. Use an ASCII executable basename. The output directory must be new and separate from the game. The source distribution uses its build outputs; the binary distribution's tool uses its Generic-A3D2 payload.

Review INSTALL_PLAN.json. It lists existing DLL/manifest conflicts and their hashes. Before any manual installation, back up those files. The overlay never contains the original executable or game assets. Copy it beside the executable only in a backed-up/test installation, select that game's A3D backend separately, then use its generated normal or diagnostic launcher. Extra game arguments are forwarded unchanged. The generic launcher does not magically enable a disabled game backend.

The Wine equivalent is `bash RUN_A3D_WINE.sh` with the game's established WINEPREFIX. Wrapper logs default off; the diagnostic launcher enables a bounded log. The default 6x256 buffering, 48 taps and gain 5.0 are provisional for new titles. Alice weapon recognition is disabled for generic candidates. A successful COM activation is insufficient: logs must show actual source and spatial updates, and audio still needs a listening/gameplay check.

Legacy A3D1 spatial rendering and A3D3 extension interfaces are not implemented. Generic staging is useful for A3D2 investigation; it does not certify every game on a historical support list. A negative static scan is also not proof that no dynamically loaded backend exists.

## New launcher diagnostics and explicit title compatibility

Diagnostic scripts also enable a separate bounded `a3d-launcher.log`, showing startup stages and child status. See SETUP_CANDIDATES.md for A3D_LAUNCH_LOG and A3D_LAUNCH_LOG_PATH. Normal logs remain off. The generic launcher refuses to target itself; the overlay stager rejects that name before copying payloads.

A3D_HALFLIFE_SPLASH_FIX=1 is an explicit option shared by the launcher implementation for the recognized Half-Life 1.0.1.1 layout only. Do not set it globally for generic candidates: requesting it for an unknown build aborts startup. Generic staging does not turn this option on. It does not enable a game's A3D backend automatically.
