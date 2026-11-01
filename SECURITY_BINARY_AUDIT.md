# v0.8.13 — Evidence-based binary security and publication review

**Status:** Technical source-release review completed; antivirus clearance and rights-holder licensing approval **not completed**. Do not republish the old all-in-one ZIP as a trusted binary release.

## Original archive inventory

- Previous GitHub Full Monty ZIP SHA-256: `1941490ad9e3c61723b68478958ffc4fd5aa05397fcb5f0b2c8f6d0c2b33ba3f`.
- Static file inventory: **40** PE DLL/EXE occurrences with **24** unique SHA-256 hashes, including duplicates and older binaries under the historical source tree.
- The public **source-only** package includes **zero** prebuilt `.exe`/`.dll`/PE/ELF files. Original source for the experimental adapters is included for review but not installed or run by the normal build.
- The separate minimal core package contains **only two** 32-bit Windows DLLs, matching clean source build hashes. It omits the Miles `mss32.dll` proxy, legacy EXEs and all proprietary vendor files.

## VirusTotal findings (user-supplied screenshots)

Prior ZIP: **15/65** security engines flagged it, including `SwPatch` and `PE04CAN` labels. An engine verdict is neither proof of infection nor certification of a false positive. The following individual bundled files were displayed:

| Previous bundled file | Engines | Selected imported capabilities |
|---|---:|---|
| `Game_Kits/Half_Life_1011/COPY_TO_GAME_FOLDER/halflife-a3d-alpha.exe` | 13/71 | No selected process manipulation imports |
| `Extras/Experimental/quake3-a3d-native.exe` | 9/71 | No selected process manipulation imports |
| `Game_Kits/Alice_2000/COPY_TO_GAME_FOLDER/alice-a3d-bridge.exe` | 7/71 | No selected process manipulation imports |
| `Extras/Utilities/a3d-regfree-survey.exe` | 4/71 | `LoadLibrary`/`GetProcAddress` or COM-related calls |
| `Extras/Utilities/a3d-direct.exe` | 3/71 | No selected process manipulation imports |
| `Game_Kits/Quake_III_117/COPY_TO_GAME_FOLDER/a3d.dll` | 1/71 | No selected process manipulation imports |

## Static PE import observations

For the original legacy Alice 2000, Quake III and Half-Life launchers, `llvm-objdump -p` confirms direct imports of suspended-process launch/memory operations such as `CreateProcessA`, `VirtualAllocEx`, `WriteProcessMemory`, `ReadProcessMemory` and/or `SetThreadContext`/`ResumeThread`. This functionality explains **why deeper review is necessary**, but does not establish that the files are malicious. The original `a3d-direct.exe` imports `CreateProcessA` without the selected process-injection calls. The duplicated `a3d-regfree-survey.exe` imports from `OLE32.dll` and `KERNEL32.dll`.

The original Alice 2011 `mss32.dll` adapter imports from `kernel32.dll` and `ole32.dll`, and dynamically loads/resolves other functions. It is withheld **as a prebuilt binary from this source ZIP**, but an exact rebuild now exists using only the published 331-export map and Aufake3D source. Independent antivirus assessment and redistribution-rights review remain necessary; the original Miles DLL is still required at runtime.

The two core DLLs import `KERNEL32.dll` in the inspected build. Reproducible build checks match:

- `a3d.dll`: `9291fd3e74eb43b129d1ff9713f979b6f9f25723f78300c8f4b2ed8e5bbeccd0`
- `a3dapi.dll`: `2e6f500e8d86b641d702f21cbfa2662f6327e15c794af7c07745c24cba8e8db2`

**Limitations:** This is a static import/reproducibility review, not dynamic sandboxing, independent antivirus analysis, or malware certification. Imports do not reveal all dynamically loaded functionality; source-build provenance does not itself prove code safety. No new public ZIP here has been submitted to VirusTotal by this review.

## Public release decision

1. **Source:** ready for GitHub *technical preflight* after publisher confirms legal entitlement to MIT-license the independently written portions, and preserves separate KEMAR/acoustics terms. Include `SECURITY_RELEASE_REVIEW.md` and this file.
2. **Minimal binaries:** suitable for individual DLL antivirus scanning and expert review. **Not a turnkey Alice 2011 product** without the withheld Miles name-fix proxy. Do not claim all games work by copying only two DLLs.
3. **Legacy helpers:** the full-runtime review candidate now includes rebuilt executables, but the source-only repository contains none. Rebuilt executables still require individual security assessment and gameplay testing, particularly the memory-modification bridges.
4. **Full runtime candidate:** preserve the published component-specific hashes and provenance, run component-level security checks and Windows/Wine gameplay tests before claiming public release readiness. Do not use cosmetic obfuscation or AV-evasion techniques to improve detection scores.

### Machine-readable inventory

`SECURITY_PREVIOUS_BINARIES.json` records all 40 original PE paths, hashes, sizes and inspected imports. These binary files themselves **are not included in the source repository**.
