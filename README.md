# Aufake3D v0.8.18 — GitHub source edition (release candidate)

**Source-only package**, with no precompiled PE32 EXEs or DLLs. This source tree merges the latest uploaded GitHub snapshot (commit `0d74797`)
with the one-click build system. It does **not** represent a newly tested full
binary release. The A3D engine and Miles proxy C code are unchanged from the
known-good v0.8.13 baseline. No original Miles DLL or game assets are included.

## Build locally — Windows 10/11 or Linux

Run **`BUILD_WINDOWS.cmd`** (double-click) or **`./BUILD_LINUX.sh`**.
The scripts compile the PE32 core, game bridges, Miles proxy and helpers,
run applicable tests, and assemble a local ZIP with four ready-to-copy game kits.
See [the one-click build guide](Docs/ONE_CLICK_BUILD.md). No old binary ZIP is needed.

See [v0.8.18 release notes](RELEASE_NOTES_V0818.md), [v0.8.16 build fixes](RELEASE_NOTES_V0816.md), and
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
