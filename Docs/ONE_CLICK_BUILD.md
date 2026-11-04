# One-click build — Windows and Linux

**Compiled binaries and ZIP release artifacts are written to `dist/` in the repository root.** A source clone contains no ready-to-install DLLs until you build.

On Debian/Ubuntu, run the repository-root command:

```bash
./BUILD_LINUX.sh
```

On Windows 10/11, double-click **`BUILD_WINDOWS.cmd`**. These invoke the pinned build environment and produce **Windows x86 PE32 DLLs/EXEs**, even when run under Linux; they do not produce native Linux `.so` files.

Use **[Build and release](BUILD_AND_RELEASE.md)** for tools, doctor checks, tests, reproducibility, the five-target CI gate and release publication. For installation of the resulting ZIPs, use [Installation](INSTALLATION.md).

Expected main outputs:

```text
dist/core/a3d.dll
dist/core/a3dapi.dll
dist/Aufake3D_v0.9.2_Local_Runtime.zip
dist/Aufake3D_v0.9.2_Descent3_Experimental_Win32.zip
dist/REPRODUCIBILITY_VERIFIED.json  (only after a passing local gate)
```

The optional `dist/descent3/` developer probe/standalone adapter is *not* the separately packaged, ready-to-copy retail Descent 3 ZIP. Older troubleshooting and toolchain experiments are preserved under [the history index](HISTORY_INDEX.md); they are not current build instructions.
