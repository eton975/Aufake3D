# Aufake3D v0.9.0 — AU8830 renderer development candidate

**Source-first development candidate**, with no tracked precompiled PE32 EXEs or DLLs.
The local build generates a separate **experimental** Windows runtime ZIP. The
v0.9.0 engine adds a contributor-derived 56-tap AU8830 HRTF path and is **not**
yet certified by in-game testing or hardware sample comparisons. Original Miles
DLLs, game executables and assets are not distributed.

## New to Aufake3D? Install without compiling

Start with [START_HERE.txt](START_HERE.txt) and the
[beginner-friendly Windows guide](Docs/EASY_INSTALL_WINDOWS.md), also available as
[a printable four-page PDF](Docs/Aufake3D_v0.8.18_Quick_Start.pdf).
Use the **compiled runtime ZIP** and copy the contents of the matching
`Game_Kits/<game>/COPY_TO_GAME_FOLDER/` into the game's existing directory.
Alice 2011 requires preservation of the genuine Miles DLL first.

The Windows Alice launchers seed A3D2 **once in the saved configuration**
and then respect in-game provider changes. They do not force A3D2 on the command
line. This initial-default seeder is pending real-game verification.

## Build locally — Windows 10/11 or Linux

Run **`BUILD_WINDOWS.cmd`** (double-click) or **`./BUILD_LINUX.sh`**.
The scripts compile the PE32 core, game bridges, Miles proxy and helpers,
run applicable tests, and assemble a local ZIP with six game kits. Unreal and Half-Life integrations are
experimental, and the Return to Castle Wolfenstein kit is **probe-only**; game
compatibility is not established by the presence of DLLs.
See [the one-click build guide](Docs/ONE_CLICK_BUILD.md). No old binary ZIP is needed.

See [v0.9.0 development notes](RELEASE_NOTES_V090.md), [v0.8.16 build fixes](RELEASE_NOTES_V0816.md), and
[GitHub merge provenance](Docs/GITHUB_SOURCE_INTEGRATION_V0816.md).

## Entry points

- [Developer documentation](Docs/DEVELOPER_INDEX.md) and
  [architecture map](Docs/SOURCE_ARCHITECTURE.md).
- [How to compile](BUILDING.md) the PE32 A3D core and the separate vendor-free
  331-export Miles proxy.
- [COM ABI](Docs/COM_ABI_AND_LIFETIMES.md),
  [WaveOut worker](Docs/WAVEOUT_WORKER_CONTRACT.md),
  [PCM/spatial processing](Docs/PCM_AND_SPATIAL_PIPELINE.md),
  [geometry/HRTF](Docs/GEOMETRY_AND_HRTF.md).
- [Contributor guidelines](CONTRIBUTING.md), [licensing scope](LICENSE_SCOPE.md),
  and [security notes](SECURITY_RELEASE_REVIEW.md).

```bash
python3 -m unittest discover -s tests -v
python3 scripts/build_engine.py
python3 Source/Alice2011_NameFix_v089/build_proxy_from_export_map.py --output ./dist/miles-repro
```

The compiler outputs Windows x86 binaries, not native Linux `.so` files. Do
not publish compiled legacy process-modifying launcher executables as
malware-cleared: independent review is still outstanding. The existing MIT
licence requires confirmation of the relevant rights holders and preservation
of KEMAR dataset attribution. A3D 3.0 is not fully implemented.

## Component-level security findings (documentation update)

VirusTotal reported individual detections on several components of the earlier full RC. The optional prebuilt `a3d-selftest.exe` has been removed from the full package; no working game DLLs or bridges were altered. **Neither package is antivirus-cleared.** Read [Docs/SECURITY_REVIEW_V0814_RC1.md](Docs/SECURITY_REVIEW_V0814_RC1.md) for exact hashes, limitations and further review.

## AU8830 hardware-derived HRTF / CPU performance

The 56-tap Vortex 2 filter table is included for local evaluation. See
[AU8830 HRTF modes](Docs/AU8830_HRTF_PERFORMANCE_MODES.md) and
[game compatibility status](Docs/GAME_COMPATIBILITY_V090.md).
`A3D_HRTF_MODE=fast` is the normal default; both `fast` and `reference`
now use measured 64-sample HRTF/ITD smoothing and per-ear input delay
before the 56-tap FIR. `legacy` restores the original renderer.
**No bit-exact claim or new game gameplay pass is made.**

