# Game compatibility and test expectations — v0.9.2

**Built DLLs and public ZIPs are generated in the repository root `dist/` folder.** See [Installation](INSTALLATION.md).

**Separate three kinds of evidence:** (1) a game has an installer kit, (2) the real game actually loads Aufake3D and outputs sound, and (3) directional processing, fidelity and stability work correctly. A kit alone proves none of the latter two.

| Game / edition | What has been observed | What remains to verify |
|---|---|---|
| **Alice (2000)** | Earlier genuine A3D2 and stable queue tests in tower2/hedge1/hedge2 | Re-test v0.9.2 for geometry, positional accuracy, provider switching and Windows/Wine parity |
| **Alice (2011), VorpalFix 4.2.1** | Earlier playback/provider tests using the 331-export proxy and periodic WaveOut position polling | Re-test with exact hashes and preserved original Miles DLL; verify switching, dialogue and frame timing |
| **Quake III Arena 1.17** | Earlier A3D2 and Wine testing with matching game data and 6 × 256 queue | Check v0.9.2 under heavy gameplay; don't mix different PK3 versions |
| **Descent 3 retail** | One Windows test: unmodified `main.exe` loaded local `a3dapi.dll` (ProcMon); DLLs absent → no sound, restored → sound. Stereo cues and subjective 3D impression promising. | Controlled rotations, sound-source location, HRTF, occlusion, geometry, multiple levels and platforms. **Experimental.** |
| **Descent 3 open-source engine** | Standalone adapter/COM contract compilation and synthetic probe development | Actual engine linkage/gameplay. Separate from the retail DLL method. |
| **Half-Life 1.0.1.1** | Experimental kit | Confirm authentic A3D provider/API use and gameplay quality |
| **Unreal / Unreal Gold** | Experimental research/kit | Establish valid version and genuine A3D initialization in-game |
| **Return to Castle Wolfenstein** | Deterministic BSP geometry export for research | An actual Aureal sound backend; a BSP exporter or copied DLL alone does **not** enable retail A3D |
| **GTA III / Vice City** | Experimental kit, third-party preliminary GTA III report only | Independently confirm authentic Aureal selection, signal path, playback and stability |
| **GTA San Andreas** | Research only | A3D support not established; cannot assume generic DLLs activate Aureal |

## How to test without overclaiming

1. Record the game's exact edition, executable SHA-256, OS/Wine version and original sound configuration. **Back up the game**.
2. Verify it selected **Aureal** as the real provider. If possible, capture successful `Load Image` events for `a3dapi.dll`/`a3d.dll` (Process Monitor on Windows); a UI label is not sufficient.
3. Compare unchanged game settings **with and without the two game-local DLLs**, restoring them for an A/B/A test. This establishes a dependency, not HRTF accuracy.
4. For spatial tests, hold position near a safe stationary sound source, slowly rotate through 360°, record stereo and compare against the game's ordinary 2D mode. Frequency-dependent channel differences support but do not uniquely prove HRTF processing.
5. Separately test front/back, distance rolloff, walls/occlusion, reflections, streaming/cursor timing and heavy load. Store recordings and bounded diagnostic logs; only claim features actually tested.

The engine's master gain is intentionally high (default `A3D_MASTER_GAIN=5.0`); **start with low playback volume**. For installation see [Installation](INSTALLATION.md), and for current results see the [changelog](../CHANGELOG.md).
