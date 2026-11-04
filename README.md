# Aufake3D

**An independent, experimental software implementation of Aureal A3D for classic Windows games.**

Aufake3D aims to let games use their **real Aureal A3D audio paths** on modern Windows and Linux/Wine, without installing obsolete Vortex drivers or patching the original game executable. Its shared Win32 x86 audio engine implements A3D interfaces, positional sound, HRTF rendering and developing geometry-related behaviour. Compatibility and fidelity vary by game and are not guaranteed.

> **v0.9.2 — development/experimental release.** The existence of a download or game kit does not certify gameplay, authentic AU8830 fidelity, security or compatibility with every game edition. Back up your games before installing.

## Get the software

For ordinary use, download a **compiled release asset** from [GitHub Releases](https://github.com/eton975/Aufake3D/releases), not GitHub's automatic *Source code (zip)* file. A source checkout does not contain the built DLLs until you compile it.

| Want to… | Use this release file |
|---|---|
| Try a standard game kit | `Aufake3D_v0.9.2_Local_Runtime.zip` |
| Try original retail **Descent 3** | `Aufake3D_v0.9.2_Descent3_Experimental_Win32.zip` (**experimental**) |
| Build or contribute | Clone the source, then follow [Build and release](Docs/BUILD_AND_RELEASE.md) |

**Where are the binaries?** After a successful build, look in **`dist/` at the repository root**:

```text
dist/
├── core/
│   ├── a3d.dll             universal Win32 x86 bridge
│   └── a3dapi.dll          universal A3D COM implementation
├── Aufake3D_v0.9.2_Local_Runtime.zip
├── Aufake3D_v0.9.2_Descent3_Experimental_Win32.zip
├── REPRODUCIBILITY_VERIFIED.json         local three-build evidence, if passed
├── DESCENT3_PUBLIC_RELEASE_SHA256.json   Descent 3 ZIP checksum sidecar
└── descent3/                           optional developer-only probe and object
```

Intermediate object files may be elsewhere, but **distributable build artifacts are in `dist/`**. Build artifacts from GitHub Actions are not automatically published as GitHub Release downloads; maintainers must publish verified assets separately.

## Install in brief

1. **Back up the entire game installation.** Lower speaker/headphone volume before testing; the current default master gain is 5.0 with a limiter.
2. Extract the compiled ZIP. For a standard game, choose its `Game_Kits/<game>/COPY_TO_GAME_FOLDER/` directory and copy **the contents** beside the original game executable. Do not overwrite a game's original executable or delete existing `SndDrivers` folders.
3. Run the supplied `RUN_AUFAKE3D_WINDOWS.cmd` where provided; Wine users can use the appropriate included launcher. Select the game's genuine Aureal A3D option where available.
4. **Alice (2011) is special:** before copying its proxy, preserve **two copies of the genuine original Miles `mss32.dll`** and verify the expected game/DLL hashes. **Do not install its proxy blindly.** Read the [full installation guide](Docs/INSTALLATION.md).

For **Descent 3 retail**, extract its separate ZIP and place the included `a3d.dll` and `a3dapi.dll` beside the original `main.exe`; select **Aureal 3D** in the game's setup. See the [Descent 3 guide](Docs/DESCENT3_PUBLIC_RELEASE.md). This is a retail drop-in experiment, **not** the separate Descent 3 source-engine integration.

## What's new in v0.9.2?

- **Descent 3 retail experiment.** The unmodified game has been observed loading Aufake3D's local `a3dapi.dll` (ProcMon), and an A/B/A test found that sound disappeared when the DLLs were removed and returned when restored. Stereo recordings and listening impressions are promising for spatial audio, **but correct HRTF, occlusion, reflections and general gameplay remain unconfirmed**. Its public, deterministic game-folder ZIP is generated automatically during the normal build.
- **Reproducible release engineering.** The core runtime and Descent 3 ZIP are required to match independent local rebuilds byte-for-byte. The release workflow also requires matching outputs from **Windows Server 2022, Ubuntu 24.04, Ubuntu 26.04, Ubuntu 26.10 and Debian 13**, using pinned toolchains. A passing build or a design requirement alone is **not** proof a specific GitHub release has passed all gates.
- **Return to Castle Wolfenstein research.** A deterministic BSP v47 acoustics/surface exporter records source provenance and candidate geometry. **This does not enable A3D in unmodified RtCW.**
- **Existing engine retained.** The single shared renderer continues the 56-tap AU8830 Reference/Fast and 48-tap Legacy modes, fixed 6 × 256 WaveOut buffering at 48 kHz (~32 ms), and master gain 5.0 default. The original A3D game/provider options are not relabelled to fake compatibility.
- **Clearer documentation.** Current setup, support status, reproducibility and release instructions have dedicated guides; older release notes are archived.

See the [complete change history](CHANGELOG.md).

## Game status: tested paths versus research

| Game | Current scope |
|---|---|
| American McGee's Alice (2000) | Earlier Windows/Wine A3D2 gameplay testing; revalidate with v0.9.2 |
| Alice (2011), VorpalFix 4.2.1 | Version-specific Miles bridge, earlier gameplay/provider tests; retain original Miles DLL |
| Quake III Arena 1.17 | Earlier A3D2/Wine testing with matching 1.17 game data |
| **Descent 3 (retail)** | **Experimental:** DLL load and audio dependence confirmed on one setup; 3D fidelity under investigation |
| Half-Life, Unreal, RtCW, GTA III/Vice City | Experimental/research paths; not broad gameplay-certified support |
| Descent 3 open-source engine | Separate source adapter research; not required for retail drop-in test |

A game kit may be present even where actual Aureal activation is unproven. See [game compatibility](Docs/COMPATIBILITY.md) for details and a test procedure.

## Build from source

On **Debian/Ubuntu**, from a checkout:

```bash
./BUILD_LINUX.sh
```

On **Windows 10/11**, double-click `BUILD_WINDOWS.cmd`. Both build **32-bit Windows PE** DLLs/EXEs; Linux builds are intended for use through Wine, **not native `.so` libraries**. The pinned build scripts handle their toolchain requirements; do not silently substitute a system compiler when validating reproducibility.

**After the build, open `dist/`.** For complete instructions, testing, SHA-256 checks and the five-platform certificate, read [Build and release](Docs/BUILD_AND_RELEASE.md).

## Documentation, safety and licensing

- **Start here:** [Documentation index](Docs/README.md) · [Installation](Docs/INSTALLATION.md) · [Build/release](Docs/BUILD_AND_RELEASE.md) · [Troubleshooting](Docs/TROUBLESHOOTING.md).
- **Engineering:** [Developer guide](Docs/DEVELOPER_INDEX.md) · [Descent 3 research](Docs/DESCENT3_PUBLIC_RELEASE.md).
- **Safety and provenance:** [Security](SECURITY.md) · [Licensing scope](LICENSE_SCOPE.md) · [Third-party notices](THIRD_PARTY_NOTICES.md).
- **Previous releases:** [Changelog](CHANGELOG.md) · [Historical documents](Docs/HISTORY_INDEX.md).

Aufake3D is independent of Aureal and the game publishers. No proprietary game executable, Miles runtime or Aureal driver binaries are supplied. Follow the source-specific licence and redistribution notices; source and binary provenance must be reviewed before publication.
