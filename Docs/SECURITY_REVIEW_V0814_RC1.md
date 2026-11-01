# v0.8.14-RC1 — Component-level VirusTotal review (security documentation revision 1)

**Status: NOT antivirus-cleared. Do not infer safety from build reproducibility or a lower detection count.**

This is a documentation and packaging revision of the **same v0.8.14-RC1 runtime**.
The universal audio core, Miles proxy, game launchers and executable manifests have **not been patched, repacked, obfuscated or modified**. The only binary removal is the **optional** `Extras/Diagnostics/a3d-selftest.exe`.

## Source of the findings

A user supplied the VirusTotal detection and Relations / Bundled Files reports for the original full archive (SHA-256 `026e1ce48aa266ff2ad76d99b1ac25645703d251601b21968deb8edacb13e32a`). It showed **13/68** detection vendors for the ZIP. Individual-file results reported in that snapshot were:

| SHA-256 (short) | Component, not necessarily unique installed location | Reported detections | Treatment |
|---|---|---:|---|
| `ffa19e714ca8...` | `Extras/Diagnostics/a3d-selftest.exe` | **5/71** | Removed the *prebuilt copy* from the full runtime distribution; source/build retained |
| `2e6f500e8d86...` | `a3dapi.dll` (universal renderer, multiple identical kit copies) | **2/70** | Retained byte-identically; reproducibility documented; needs individual security review |
| `1d978e28dce2...` | `Source/Engine/portable/build_legacy_probe.sh` | **1/61** | Retained as readable source build script; inspect directly |
| `8bc83f25b228...` | `mss32.dll` (Alice 2011 proxy, duplicated in `SndDrivers`) | **1/71** | Retained byte-identically because essential to existing installation; source/export map included; needs rights/security review |
| `9291fd3e74eb...` | `a3d.dll` (universal compatibility frontend, multiple identical kit copies) | **1/71** | Retained byte-identically; reproducibility documented; needs individual security review |

The user-copied hashes and screenshot provide **point-in-time results**, not independent verification of all archive members. Other threat-engine results may change or be correlated through shared signatures. The detected shell script is a build helper, not a Windows runtime DLL.

## Why the optional executable was excluded

`a3d-selftest.exe` is an ABI/COM diagnostic, **not a game requirement**. The source remains at `Source/Engine/win32/selftest.c`, with its compilation steps in `Source/Engine/windows-build-recipe.json`. Developers can generate a fresh local copy with `python3 scripts/build_engine.py`; its build output stays outside the release's ready-to-copy game kits. No installer or game kit requires `Extras/Diagnostics/a3d-selftest.exe`.

Removing this optional file does **not** establish that the overall archive, the other binaries, or freshly built copies are malware-free. No attempt was made to change binary signatures simply to evade a detector.

## Higher-scrutiny executable helpers retained in the full package

- `Game_Kits/Alice_2000/COPY_TO_GAME_FOLDER/alice-a3d-bridge.exe` — child-process creation and memory modification for game-local compatibility; not necessary for Alice 2011.
- `Game_Kits/Half_Life_1011/COPY_TO_GAME_FOLDER/halflife-a3d-alpha.exe` — experimental and not verified for the intended retail build.
- `Extras/Experimental/quake3-a3d-native.exe`, `unreal-a3d-alpha.exe`, `a3d-launch.exe` — experimental/non-default tools. Review the source before use; not claimed universally compatible.

Process modification may resemble malware behaviour and may be unsuitable for online multiplayer or anti-cheat protected games. Do not disable security software in order to run these. For the normal Quake III profile, the optional native launcher is not required.

## Security and provenance verification still required

1. Check individual rebuilt PE binaries (particularly core and Miles proxy) and record vendor verdicts with each SHA-256, not just the ZIP-level result.
2. Review the source-to-binary hashes and static imports in `Docs/BINARY_ORIGINS.json`, `Docs/BINARY_IMPORT_AUDIT.json`, and `Docs/BINARY_PROVENANCE.md`. Static imports alone cannot exclude dynamic loading or harmful behaviour.
3. Exercise launchers in an isolated, disposable Windows VM and check process creation, disk changes, registry, and network activity. Do not assume a successful audio test constitutes malware clearance.
4. Resolve MIT rights-holder approval, dataset notices, and Miles proxy legal/provenance questions separately from security scanning.
5. Retest the archived file SHA-256; the **new ZIP has a different digest** due to removed diagnostic and updated documentation, not because the runtime DLLs changed.

**Publication status:** developer/public-testing candidate; no independent scan of this revised archive was performed here. The source-only GitHub package is a separate, lower-risk distribution, not an AV certificate.
