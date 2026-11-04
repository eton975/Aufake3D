# Documentation — Aufake3D v0.9.2

**New here? Start with the [main GitHub README](../README.md).** This folder is organised by what you want to do, not by past version numbers.

**Compiled binaries and distributable ZIPs are written to `dist/` in the repository root after building.** The source tree and GitHub's automatic source-code ZIP do **not** contain ready-to-install DLLs.

| Task | Read this |
|---|---|
| Install into an existing Windows game or Wine setup | **[Installation](INSTALLATION.md)** |
| Set up original retail Descent 3 (experimental) | **[Descent 3 retail kit](DESCENT3_PUBLIC_RELEASE.md)** |
| Build Windows PE binaries on Windows/Debian/Ubuntu | **[Build and release](BUILD_AND_RELEASE.md)** |
| Determine what's tested versus exploratory | **[Compatibility](COMPATIBILITY.md)** |
| Fix missing audio, failed builds or suspect DLL loads | **[Troubleshooting](TROUBLESHOOTING.md)** |
| Understand code and contribute | **[Developer index](DEVELOPER_INDEX.md)** |
| See changes since 0.8.x | **[Consolidated changelog](../CHANGELOG.md)** |
| Look up older release notes or outdated instructions | **[History index](HISTORY_INDEX.md)** |

## Quick output locator

```text
dist/core/a3d.dll
dist/core/a3dapi.dll
dist/Aufake3D_v0.9.2_Local_Runtime.zip
dist/Aufake3D_v0.9.2_Descent3_Experimental_Win32.zip
dist/REPRODUCIBILITY_VERIFIED.json                  if the local gate passes
dist/DESCENT3_PUBLIC_RELEASE_SHA256.json             ZIP checksum sidecar
dist/descent3/                                        optional developer-only probe
```

The *game-folder Descent 3 ZIP* is different from the developer-only files in `dist/descent3/`. The five-platform comparison certificate is produced by CI, not by a single local build. Check the actual certificate before publishing any package as reproducible across hosts.

## Reading technical docs

The developer index groups living subsystem contracts (COM ABI, WaveOut, PCM, HRTF, game adapters and security). These documents are intentionally separate where implementation details matter. Old hotfix logs already live in `Docs/History/Engine_Notes/`; other superseded release material is being consolidated into neighbouring history directories. History is useful for archaeology but **not** current setup advice.
