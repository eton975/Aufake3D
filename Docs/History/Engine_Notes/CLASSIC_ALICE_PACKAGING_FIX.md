# A3D v0.6.0 Classic Alice 2000 packaging fix

Original v0.6.0 was missing `alice-a3d-bridge.exe`. The corrected
source/binary distribution adds `classic2000/` with commented selector
source and an independently buildable Win32 launcher. The `portable/`
installer profile `alice` now deploys both bridge EXE and manifest when
A3D2 COM support is requested, and `portable/run_alice2000_wine.sh` starts
this launcher without replacing or modifying the original game executable.
The A3D1/A3D2 engine DLLs and 2011 VorpalFix bridge are unchanged.

Use `portable/ALICE2000_QUICKSTART.md`. Test coverage: classic installer
install/verify/uninstall, full collision refusal, EXE-hash integrity,
2011 remaster regression, and original v0.6.0 generic installer tests.
No classic Alice game runtime test was performed in this build container.
