# Build and develop this snapshot

Version remains 0.7.0-alpha. Build using build_native_windows.ps1 or build_from_recipe.py with Clang/LLD. Run tools/generate_alpha_profiles.py to refresh all five title profiles plus Generic-A3D2, then run_alpha_checks.py and verify_alpha_runtime.py. Native DSP checks are available through run_native_tests.py; the DSP sources are unchanged in this iteration.

Core changes: win32/capability_contract.h, softcaps/hardcaps in a3dapi.c, experimental/launcher_diagnostics.h, game_activation.c and the opt-in halflife_splash_compat.h/signature helper. The signature helper is independent of Windows for boundary testing. tests_v070/test_progress.py additionally builds a synthetic known-layout x86 PE to test the actual child-memory compatibility path, plus unknown-layout refusal, optional logs, configured voice limits and recursion handling.

The experimental launchers remain ANSI/x86 and require an adjacent valid local COM manifest. The bootstrap is inherited from the existing three title bridges. Do not broaden a title-specific byte signature based on a display name alone; acquire and inspect the exact new binary and test the relevant routine first.

Build/test fixtures are project code. Never ship supplied game binaries, vendor DLLs, game assets or private debugger helpers. HALFLIFE_PROGRESS.md distinguishes static inspection, debugger experiment, synthetic Windows tests and missing gameplay validation.
