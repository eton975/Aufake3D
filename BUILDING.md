# Building Aufake3D v0.9.2

**Current complete instructions: [Docs/BUILD_AND_RELEASE.md](Docs/BUILD_AND_RELEASE.md).** This short file remains as a convenient entry point for users who expect `BUILDING.md` at the repository root.

- Windows 10/11: run **`BUILD_WINDOWS.cmd`**.
- Debian 13/Ubuntu: run **`./BUILD_LINUX.sh`**.
- **Find all compiled distributable binaries and ZIPs under `dist/`**, notably `dist/core/a3d.dll`, `dist/core/a3dapi.dll`, `dist/Aufake3D_v0.9.2_Local_Runtime.zip` and `dist/Aufake3D_v0.9.2_Descent3_Experimental_Win32.zip`.
- Both platforms build **Windows x86 PE DLLs/EXEs** (Linux/Wine use), not native Linux `.so` files.
- A local three-build verification report is not a five-platform CI reproducibility certificate. Don't publish artifacts before the required verification has actually passed.
