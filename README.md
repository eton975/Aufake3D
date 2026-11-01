# Aufake3D v0.8.14-RC1 — GitHub source edition

**Source-only package**, with no precompiled PE32 EXEs or DLLs. This source
matches the v0.8.14-RC1 full-binary candidate; comments and documentation
were expanded, but the audio core and Miles proxy behavior is unchanged from
the user-tested v0.8.13 baseline. No original Miles DLL or game assets included.

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
