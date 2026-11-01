# A3D v0.7.1-dev — Generic client discovery and ABI survey

**Development kit, not a general release or promise of A3D 1.x/2.x/3.0 support.**
This is an incremental update to the `v0.7.0-alpha` shared codebase. Existing
Alice 2000, Alice 2011, Quake III and experimental Half-Life behavior is NOT
modified. The `a3dapi.dll`, `a3d.dll` and `a3d-launch.exe` binary payloads here
are copied without change from the v0.7.0-alpha development snapshot.

## What is new

* `a3d-abi-survey.exe`: newly compiled PE32/x86 COM ABI survey. It prints
  whether the legacy `_A3dCreate@12` export exists and probes IA3d,
  IA3d2/IA3d3/IA3d4 and A3D3 extension IIDs. A3D1/2 prefix QI does *not*
  mean legacy A3D1 HRTF is implemented. Expected A3D3 IIDs are rejected.
* `tools/scan_a3d_clients.py`: read-only static client inspection now reports
  generation evidence by A3D1, A3D2 and A3D3, identifies Miles `.m3d`
  modules, and distinguishes a bare A3D API CLSID from a full interface clue.
* `tools/stage_generic_candidate.py`: creates a new separate overlay with
  an ABI-survey launcher, a default low-invasive `a3d-direct.exe` launcher,
  an explicitly opt-in bootstrap launcher, and a raw EXE direct-start experiment,
  separate Wine scripts, and an install-conflicts report. It never modifies the
  supplied game directory. Installation is still manual and opt-in.
* `tools/test_generic_v071.py`: PE32, staging, no-mutation, generation routing
  and unsafe-target rejection tests.

## Quickstart (Python 3, no third-party packages required)

1. Unpack this ZIP in a working folder *not* inside a game directory.
2. Pick an **owned, offline, 32-bit Windows** game with a suspected A3D2 sound backend.
3. Locate the `.exe` directory (e.g., `System` for some Unreal-based titles).
4. Static scan, read-only:

   `python tools/scan_a3d_clients.py "C:/Games/Example/System" --out a3d-scan.json`

5. Create a new, separate overlay:

   `python tools/stage_generic_candidate.py "C:/Games/Example/System" --exe Example.exe --out "C:/A3D-Experiments/Example-overlay"`

6. Read `Example-overlay/INSTALL_PLAN.json` and the conflicting-file hashes.
   **Make backups** before manually copying overlay files adjacent to the game
   executable. No original EXE or game assets are included or patched on disk.
7. On Windows try `RUN_A3D_ABI_SURVEY_WINDOWS.cmd` first. On Linux/Wine use
   `bash RUN_A3D_ABI_SURVEY_WINE.sh`. Success here only verifies DLL/COM wiring.
8. Select the game's A3D sound backend in its own settings. Only then try
   `RUN_A3D_WINDOWS.cmd` or `bash RUN_A3D_WINE.sh` with the supplied Wine prefix.
   Normal diagnostic logging is disabled. `RUN_A3D_DIAGNOSTIC_*` enables bounded logs.
9. The default `RUN_A3D_*` uses **`a3d-direct.exe`**: an ordinary
   child process launch without memory patching. This may fail to enable A3D2
   COM if the game ignores its external manifest. `RUN_A3D_DIRECT_*` is an even
   simpler direct start of the original EXE. `RUN_A3D_BRIDGE_*` is the explicit
   fallback using the suspended-child activation bootstrap, which modifies the
   child process in RAM. No option guarantees anti-cheat acceptance.

## Architectural status

| ABI generation | Current status | Remaining work |
| --- | --- | --- |
| A3D 1.x | `a3d.dll` supports historic A3dCreate/DirectSound fallback; **not** Aureal spatial audio | Implement actual 3D buffer/listener interception and Aureal-compatible DSP |
| A3D 2.x | Shared `a3dapi.dll` COM core implements tested subset of interfaces and WaveOut rendering | Extend method/flag/geometry compatibility, test per engine and Miles provider |
| A3D 3.0 | Unknown/unsupported extension IIDs intentionally rejected | ABI research and correct vtables, extensions, filters, fallback negotiation |

A game can have multiple potential backends. Static PE imports, GUID bytes,
strings and `.m3d` files are evidence but do not establish that an A3D code
path actually executes. No game is added to the confirmed-compatibility list
until activation, real source activity, spatial rendering, audio and gameplay
have been verified. Never advertise anti-cheat bypass or a guaranteed ban-free mode.

## Compatibility and privacy

* No game files are read by the executable ABI survey; the Python scanner is
  read-only and reports file hashes, imports and selected markers.
* The default generic **direct** launcher uses ordinary `CreateProcess` and
  does not write into child memory. The separate `RUN_A3D_BRIDGE_*` mode installs
  an activation context in the game child process and may be flagged by AV.
  The default direct route is less invasive but A3D2 activation is unverified.
* Keep this experimental package to offline games or explicitly authorized
  servers. Do not disable AV/anti-cheat or try to conceal the loader.
* No third-party vendor runtime or game assets are bundled.
* The default shared DSP policy (6x256/32ms at 48k, HRTF 48 taps, master gain
  5.0, linked peak limiter) is preserved. Weapon-clarity is OFF for generic titles.
* Half-Life retail-specific splash workarounds are not selected by generic mode.
* Real Windows/Wine runs of the new survey are not verified in this environment.

## Build and tests

Build the ABI survey and generic direct/bridge launchers (Clang + lld-link):

`bash win32/build_generic_probe.sh`

`python3 tools/build_generic_v071.py`

The script synthesizes **link-time** import libraries from local .def files;
its temporary `*-stub.dll` artifacts must **never be installed or shipped**.

Run the Python regression tests from the full source tree:

`python3 -m unittest discover -s tools -p 'test_*.py' -q`

Existing **audio renderer DLLs** are intentionally unchanged. The generic
launcher EXEs are newly compiled. These improvements are portable tooling
and ABI diagnostics, not an A3D3 implementation.

## Source ZIP note

The curated `Generic_Full_Source` archive can rebuild the core DLL and generic
launchers using the supplied scripts. Run its six `test_generic_v071.py` tests
without the old deployment tree. The full historical 116-test regression suite
requires the complete project workspace (including previous deploy snapshots),
and passed in the development workspace; it is not self-contained in this ZIP.

The generic DLL payload remains the v0.7.0-alpha A3D2 engine. The v0.7.1
work adds launcher, interface survey, static scanning and candidate staging,
**not** a completed A3D1/A3D3 renderer or confirmed support for new games.
