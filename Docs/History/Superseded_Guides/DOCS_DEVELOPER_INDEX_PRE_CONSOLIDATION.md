# Developer index — Aufake3D v0.9.2

**New here? Read [the documentation landing page](README.md) first.**
It explains how to build, install, and — importantly — **where the compiled
DLLs and distributable ZIP files are stored (`dist/`)**.

## Find documentation by task

| Task | Guide |
|---|---|
| Install the compiled release | [EASY_INSTALL_WINDOWS.md](EASY_INSTALL_WINDOWS.md) |
| One-click local builds (Windows/Debian/Ubuntu) | [ONE_CLICK_BUILD.md](ONE_CLICK_BUILD.md) |
| Find `dist/` artifacts, verify and publish | [BUILD_AND_RELEASE.md](BUILD_AND_RELEASE.md) |
| Download/install experimental retail Descent 3 DLLs | [DESCENT3_PUBLIC_RELEASE.md](DESCENT3_PUBLIC_RELEASE.md) |
| Diagnose or source-integrate Descent 3 | [DESCENT3_A3D_API_PROBE.md](DESCENT3_A3D_API_PROBE.md) and [source-engine adapter](../Integrations/Descent3_Source/README.md) |
| Five-OS reproducibility requirements | [CROSS_PLATFORM_REPRODUCIBILITY.md](CROSS_PLATFORM_REPRODUCIBILITY.md) |
| Source tree and component boundaries | [SOURCE_ARCHITECTURE.md](SOURCE_ARCHITECTURE.md) |
| COM object interfaces and lifetimes | [COM_ABI_AND_LIFETIMES.md](COM_ABI_AND_LIFETIMES.md) |
| Worker/queue and polling | [WAVEOUT_WORKER_CONTRACT.md](WAVEOUT_WORKER_CONTRACT.md) |
| PCM source processing | [PCM_AND_SPATIAL_PIPELINE.md](PCM_AND_SPATIAL_PIPELINE.md) |
| Geometry/HRTF pipeline | [GEOMETRY_AND_HRTF.md](GEOMETRY_AND_HRTF.md) |
| Miles and provider selection | [MILES_PROXY_AND_GAMES.md](MILES_PROXY_AND_GAMES.md) |
| Source symbol guide | [SOURCE_FUNCTION_GUIDE.md](SOURCE_FUNCTION_GUIDE.md) |
| Game compatibility and unverified targets | [COMPATIBILITY_PLAN.md](COMPATIBILITY_PLAN.md) |
| License/redistribution and security | [LICENSING_AUDIT.md](LICENSING_AUDIT.md), [BINARY_COMPONENTS_AND_SECURITY.md](BINARY_COMPONENTS_AND_SECURITY.md) |
| Historical experiments, old RC instructions | [HISTORY_INDEX.md](HISTORY_INDEX.md) |

## Important limits

The experimental Descent 3 DLL kit uses the **same universal audio DLLs** as
the other game kits; it must not create a separate rendering-engine fork. The
optional `.obj` and synthetic `.exe` under `dist/descent3/` are **developer
experiments**, not files to copy into a retail Descent 3 game folder.

A deterministic ZIP, matching SHA-256 certificates, or successful DLL loading
does not prove a game is fully compatible, geometrically accurate or
antivirus-cleared. Do not promote experimental results to fully supported
without targeted testing.
