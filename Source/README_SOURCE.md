# Aufake3D v0.8.16 — source guide

The current code is under `Engine/` (COM/WaveOut/mixer/HRTF/geometry),
`Alice2011_NameFix_v089/` (pinned Miles proxy), `NameFix_Tests/` and
`SDK_Method_Conformance_v081/` (ABI tests). Historical engine READMEs and
hotfix commentary are in `../Docs/History/Engine_Notes/`; they are archival,
**not current setup instructions**.

Begin with `../Docs/DEVELOPER_INDEX.md`, `../Docs/SOURCE_ARCHITECTURE.md`,
`../Docs/COM_ABI_AND_LIFETIMES.md`, and `../Docs/WAVEOUT_WORKER_CONTRACT.md`.
Run `python3 scripts/build_engine.py` from the repo root to compile Win32 PE32
core DLLs. Run `python3 Source/Alice2011_NameFix_v089/build_proxy_from_export_map.py
--output ./dist/miles-repro` separately to rebuild the vendor-free proxy.

No original Miles DLL, retail game, VorpalFix binary or original Aureal SDK
implementation is intended to be included. The project-derived source may be
published under MIT only with appropriate rights-holder approval; generated
KEMAR data have independent attribution requirements.
