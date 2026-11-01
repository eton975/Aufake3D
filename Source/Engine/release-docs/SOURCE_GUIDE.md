# Unified source and rebuilding

The canonical engine is win32/a3dapi.c plus included .inc/.h units. All games use the same a3dapi.dll and legacy a3d.dll. Game-specific bridges only select activation/provider behavior. The source retains the project's historical tools, deployments and documentation because earlier regression tests reference them. Those are historical fixtures; install only the release's Binaries or Source/deploy-v0612 files. Fresh instructions in release-docs supersede older guides.

## Reading the source

| Unit | Responsibility and invariants |
|---|---|
| win32/a3dapi.c | COM GUIDs, root vtables and lifetime. Preserve ABI slot order and x86 stdcall. |
| win32/source_probe.inc | Source methods, PCM ownership, Lock/Unlock and playback metadata. |
| win32/stream_winmm.inc | One output worker, bounded buffers, snapshot copies and queue policy. |
| win32/stream_core.h | Allocation-free spatial rendering, two clarity buses, reverb and limiter. |
| win32/weapon_signatures_v0612.inc | Exact metadata-only 4 KiB FNV-1a recogniser, 15 signatures. |
| win32/measured_hrtf.h and measured_hrir_data.h | Measured binaural filters and direction selection; preserve supplied attribution/license. |
| win32/acoustic_scene.h, geometry_lists.inc, geom_trace.inc | Bounded geometry, cached paths, obstruction and reflections. |
| win32/staff_diag.inc | Optional bounded captures; normal launch never opts in. |
| native_activation.inc | Registration-free activation scoped to the child process. |
| classic2000, remaster2011, native | Signature-checked x86 launch bridges for the three supported titles. |
| config/game_profiles_v069.json | Shared profile specification; historical filename retained. |

Comments describe data ownership, ABI constraints, rendering order, snapshot boundaries, clarity thresholds and fallback behavior. Headers and included implementation units form the unified implementation; there are no separately maintained per-game audio forks. Historical v0.5.0 commentary headers indicate when comments were introduced, not the current release version.

## Build requirements

Install Python 3, Clang and LLD. Use a recent Clang/LLD supporting i686-pc-windows-msvc and lld-link. No proprietary SDK or original game is needed for the freestanding PE32 build. A host C compiler is needed for native mixer tests; Python NumPy and SciPy are needed only for offline weapon-forensics analysis/tests, not gameplay. Bash is needed for launcher tests (Git Bash works on Windows). Put cc/gcc and Bash on PATH for those checks.

Windows:

```powershell
./build_native_windows.ps1 -ToolchainBin 'C:\path\to\llvm\bin'
```

Windows or Linux:

```text
python build_from_recipe.py --clang /path/to/clang --linker /path/to/lld-link
```

Use python3 on distributions that do not provide python. Both runners consume windows-build-recipe.json. The recipe now includes the Quake III lock ABI probe previously present only in win32/build.sh. It rebuilds both DLLs, three game bridges and diagnostic programs. Copy win32/build/a3dapi.dll and a3d.dll to each deployment, its game bridge from classic2000/remaster2011/native, and rebuilt a3d-selftest.exe, a3d-comtest.exe and a3d-quake3-lock-test.exe to each profile. Keep the supplied manifests beside them.

## Regressions

From Source with NumPy, SciPy and a host C compiler available:

```text
python -m unittest discover -s tools -p "test_*.py" -v
python -m unittest discover -s dropin/tests -p "test_*.py" -v
python -m unittest discover -s portable/tests -p "test_*.py" -v
```

For the real portable clarity mixer: compile win32/test_clarity_v0612_native.c with `cc -std=c11 -O2` and run the result. The synthetic bypass check compares protected metadata off/on while clarity is disabled; it is not an exhaustive equivalence proof. Native tests exercise DSP without an audio device or game.

Review release-docs/VERIFICATION.md and validation logs for exactly what ran here. tools/verify_all.sh is an older broader Linux engineering workflow and requires CMake plus sanitizer support; it is not the recorded Windows release validation command. Generated import-library stub DLLs under build are link-time artifacts and must never be installed as system libraries.

No compiler or Python runtime is bundled. “Self-contained” means all project source, project-generated runtime files, instructions and integrity records are supplied; games, VorpalFix and operating-system build/runtime prerequisites remain external.

Run `python run_native_tests.py` for the portable DSP set and `python verify_release_runtime.py` for the canonical deployment PE/syntax/Windows ABI checks. The native set excludes the archived test_pcm_native.c OS-stub harness; see VERIFICATION.md.
