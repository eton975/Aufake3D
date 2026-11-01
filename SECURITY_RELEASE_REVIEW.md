# Security release review — 0.8.13 (source repository)

## Evidence and decision

The *prior* Full Monty ZIP (`1941490ad9e3c61723b68478958ffc4fd5aa05397fcb5f0b2c8f6d0c2b33ba3f`) showed **15/65** VirusTotal engine detections. The user's VirusTotal Bundled Files screenshot showed:

| Original bundled file | Screenshot verdict | Treatment here |
|---|---:|---|
| `Game_Kits/Half_Life_1011/COPY_TO_GAME_FOLDER/halflife-a3d-alpha.exe` | 13/71 | Prebuilt EXE excluded; original experimental source retained |
| `Extras/Experimental/quake3-a3d-native.exe` | 9/71 | Prebuilt EXE excluded; source retained |
| `Game_Kits/Alice_2000/COPY_TO_GAME_FOLDER/alice-a3d-bridge.exe` | 7/71 | Prebuilt EXE excluded; source retained |
| `Extras/Utilities/a3d-regfree-survey.exe` | 4/71 | Prebuilt EXE excluded |
| `Extras/Utilities/a3d-direct.exe` | 3/71 | Prebuilt EXE excluded; source retained |
| `Game_Kits/Quake_III_117/COPY_TO_GAME_FOLDER/a3d.dll` | 1/71 | Core rebuilt and retained **only in separate minimal binary ZIP** |

The historical helpers use process creation and, in some profiles, `VirtualAllocEx`, `WriteProcessMemory`, and related APIs. Such capabilities justify higher scrutiny but are **not proof of malicious code or false positives**. Independent per-file scan, dynamic sandbox testing and provenance resolution have *not* been completed.

## Core audio DLLs

The core source builds with a pinned Windows x86 Clang/LLD recipe. Previously verified hashes:
- `a3d.dll`: `9291fd3e74eb43b129d1ff9713f979b6f9f25723f78300c8f4b2ed8e5bbeccd0`
- `a3dapi.dll`: `2e6f500e8d86b641d702f21cbfa2662f6327e15c794af7c07745c24cba8e8db2`

Static PE import inspection (`llvm-objdump -p`) found `KERNEL32.dll` as the import library for the two core files, without import entries for remote-process injection, networking or persistence APIs in that inspection. Static inspection cannot prove security or rule out dynamically resolved calls. **We have not submitted the new ZIPs to VirusTotal**; prior detection scores do not transfer to new archives.

## Alice 2011 Miles adapter

This source archive intentionally has **no** prebuilt `mss32.dll`. Since the earlier review, the adapter has been **reproduced byte-for-byte** from the Aufake3D proxy source plus `MILES_EXPORT_SURFACE_331.json` (331 exported names/ordinals), **without the original Miles DLL at build time**. The separately packaged full-runtime candidate contains this rebuilt proxy. The legitimate original Miles DLL is still required when running the game; its redistribution is not authorised by Aufake3D. Byte reproduction does not establish antivirus safety, copyright ownership or redistribution permission.

## Limitations and public release recommendation

*Source:* suitable as a review candidate **after rights holders confirm MIT licensing and KEMAR attribution**, and GitHub CI passes in a fresh checkout. *Minimal runtime:* suitable for isolated review and per-file AV submissions, but **not a complete user-friendly game release**. The newer full-runtime candidate is separately packaged, includes rebuilt helpers/proxy, and still awaits independent component-level security review. The older original helper executables remain withheld; freshly rebuilt helpers in the separate full-runtime candidate still require security and gameplay review. There is no claim of antivirus clearance or conclusive malware absence.

## v0.8.14-RC1 component-level follow-up

See [Docs/SECURITY_REVIEW_V0814_RC1.md](Docs/SECURITY_REVIEW_V0814_RC1.md). The full binary revision omits the optional prebuilt self-test; this source-only repository contains no PE binaries, but is not a guarantee of safety.
