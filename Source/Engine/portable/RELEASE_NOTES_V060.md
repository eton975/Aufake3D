# A3D Portable v0.6.0 — Alice 2011 Remaster + VorpalFix 4.2.1 compatibility candidate

**Status: experimental v0.6.0; offline tests passed, real-game testing pending.**
It would be inaccurate to describe this as fully debugged or gameplay-tested
in American McGee's Alice (2011). A complete 2011 retail installation and
Wine/Proton runtime are not available in the build environment.

## Why this release exists

The uploaded 2011 remaster `alice.exe` (1,668,472 bytes; SHA256
`08bcbe4b549633b24c90a1ab36bf516bd8873432c68b37248c98ee4225506e50`)
uses a modified version of the original Miles game-sound selector. It offers
`a3d` -> `Aureal A3D Interactive`, but its executable does **not** recognise the
`a3d2` setting. The bundled 2011 `mssa3d2.m3d` does advertise the real A3D2
provider `Aureal A3D 2.0 (TM)` and references `a3dapi.dll` and the A3D2 COM
interfaces. That is what we are trying to access with our software engine.

The new **RAM-only remaster selector bridge** runs as a separate small EXE,
starts the adjacent untouched `alice.exe` suspended, checks byte signatures,
and adds the `a3d2` selector **only in its child process memory**. All other
sound drivers keep their original selection behavior. This binary works only
with the exact supplied 2011 executable; the installer refuses other hashes.

Unlike the 2000 Alice bridge, the 2011 bridge has different code addresses,
register usage, and provider-buffer handling. Do not substitute them.

The existing v0.5.0 COM/IA3d4 measured-HRTF software renderer is **retained**.
Its source and compiled DLL are rebuilt for this 0.6.0 package; actual
2011-game playback, reflections, and reliability are not yet validated.

## Compatibility and original files

The user's supplied VorpalFix 4.2.1 `winmm.dll` exactly matches the
`winmm.dll` inside the user-supplied `VorpalFix.zip`. The separately provided
`VorpalFix.ini` differs from the ZIP default and **must be preserved**.
The original VorpalFix `winmm.dll` is never overwritten, proxied, replaced,
or bundled with this release. Nor are the commercial original Alice EXE, Miles
M3D providers, or PK3 assets redistributed here.

## Install/test in a COPY of your working remastered Alice

1. Back up or duplicate the **2011 remaster** installation containing
   `alice.exe`, VorpalFix 4.2.1 (`winmm.dll`, `VorpalFix.ini`, its PK3s), and
   original `SndDrivers/mss32.dll`, `SndDrivers/mssa3d2.m3d`.
2. Extract the **portable release** and run the inspector from its directory:

```sh
python3 a3d_port.py inspect "$HOME/Games/Alice2011/bin/alice.exe" --profile alice2011
python3 ../remaster2011/verify_alice2011.py "$HOME/Games/Alice2011/bin/alice.exe" # source archive only
```

3. Install into the test COPY, without overwriting game or VorpalFix files:

```sh
python3 a3d_port.py install "$HOME/Games/Alice2011/bin/alice.exe" --profile alice2011 --mode com
python3 a3d_port.py verify "$HOME/Games/Alice2011/bin/alice.exe"
```

4. Start the game through the remaster bridge **using your existing Wine prefix**:

```sh
bash ./run_alice2011_wine.sh "$HOME/Games/Alice2011/bin/alice.exe" +set s_milesdriver a3d2
```

This launcher appends `winmm=n,b` to `WINEDLLOVERRIDES` to ensure VorpalFix
runs under Wine/Proton. You may set `WINEPREFIX` beforehand to your already
working game prefix. `A3D_PROBE_LOG` points to `a3d-portable.log` by default.
Do not launch the legacy 2000 `alice-a3d-bridge.exe` for the 2011 remaster.

If an existing config reverts the driver, from the developer console set
`s_milesdriver` to `a3d2`, save the setting, and restart via the new bridge.
The exact 2011 in-game control/console behavior still needs runtime validation.

**Turn headphone volume down for first test:** the v0.5 renderer's default
`A3D_MASTER_GAIN` remains 5.0 per prior preference. For a lower-gain trial,
run `A3D_MASTER_GAIN=0.5 bash ./run_alice2011_wine.sh ...`.

5. Obtain the Wine output, `a3d-portable.log`, console provider name,
   information about whether sources actually move binaurally, any crashes.
   Do not infer a successful spatial emulation merely from COM creation.

6. If you want to remove this release safely:

```sh
python3 a3d_port.py uninstall "$HOME/Games/Alice2011/bin/alice.exe"
```

Uninstall checks hashes and does not remove user-owned VorpalFix files,
original audio providers, game assets, configuration, or executable.

## Scope: what has and has not been established

| Item | v0.6.0 state |
| --- | --- |
| 2011 EXE architecture, SHA, selector disassembly | Inspected against uploaded binary |
| Original Miles A3D2 provider name/API marker | Inspected in submitted M3D |
| VorpalFix 4.2.1 DLL match | Byte-for-byte matched user ZIP |
| 2011 RAM-only A3D2 selector bridge | Built, static signature-checked, stub unit-tested |
| Generic installer, safe uninstall, original file preservation | Offline tested |
| Portable Win32 A3D1/A3D2 DLL build | Successful; 32-bit PE output validated |
| Actual 2011 retail gameplay under Wine/Proton | **NOT TESTED** |
| VorpalFix hook interactions, startup order | **NOT RUNTIME TESTED** |
| 2011 game PCM spatial processing and acoustics | **NOT RUNTIME TESTED** |
| A3D 3.0 IA3d5 support | Not implemented |

For the complete reverse-engineered selector details, build instructions, and
stub test source, see `remaster2011/BUILD_AND_TEST.md` in the source release.

## Where to go next

On the user's real 2011/VorpalFix/Wine installation, validate: (1) does the
remaster start with the bridge, (2) Miles opens the A3D2 provider, (3) actual
sample buffers start playing, (4) listener and per-source positions update,
(5) play through menus, FMVs, 3D gameplay, save/load, and exit, (6) use
A/B headphone listening to confirm true position cues and reasonable CPU load.
Any failure requires a real Wine log and instrumentation, not a claim of
finished or debugged compatibility.

**Licensing:** original renderer code MIT; see LICENSE and original upstream
attributions in source. VorpalFix is separately maintained GPL software and
not included in our ZIP; all trademarks belong to their owners.
