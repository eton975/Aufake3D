# Manual installation — v0.9.2 (Windows / Wine)

The canonical up-to-date instructions are in **[INSTALLATION.md](INSTALLATION.md)**. This filename is retained for compatibility with older package layouts; it is not a separate versioned procedure.

**Before copying anything:** back up the game folder, lower the volume and select the correct edition. Use the *compiled* runtime ZIP from `dist/Aufake3D_v0.9.2_Local_Runtime.zip` or a verified GitHub Release asset. Extract it, enter the relevant `Game_Kits/<game>/COPY_TO_GAME_FOLDER/` folder and copy **the contents** beside the original game executable. Merge nested folders rather than replacing them. Keep original executables, vendor DLLs and configurations intact.

**Alice 2011 exception:** never replace `SndDrivers/mss32.dll` with Aufake3D's Miles proxy until you have verified your original files and saved both genuine `a3d_mss_real.dll` copies (root and `SndDrivers`). See the complete exact-hash procedure in [INSTALLATION.md](INSTALLATION.md).

**Descent 3 retail exception:** use the separate `dist/Aufake3D_v0.9.2_Descent3_Experimental_Win32.zip`, copy the two DLLs beside `main.exe`, and choose Aureal 3D in the game's setup. This remains experimental; see [DESCENT3_PUBLIC_RELEASE.md](DESCENT3_PUBLIC_RELEASE.md).

On Linux, these are **Windows PE** game DLLs, not native `.so` files, and require a suitably configured Wine environment. For rollback, restore your complete original game backup. The older long-form manual guide is preserved in [history](HISTORY_INDEX.md).
