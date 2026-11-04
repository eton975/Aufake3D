# Easy Windows installation — v0.9.2

**Use the [current installation guide](INSTALLATION.md).** This compatibility entry point is retained because older releases and runtime packaging refer to this filename. The full guide has clear steps for Alice (2000), Alice (2011)/VorpalFix 4.2.1, Quake III Arena 1.17, other experimental kits and retail Descent 3.

1. Obtain a **compiled** ZIP from a verified [GitHub Release](https://github.com/eton975/Aufake3D/releases), or build it. Locally generated release ZIPs and DLLs are in **`dist/`** at the repository root; GitHub's **Source code (zip)** is not a binary installer.
2. Back up your complete game directory and start with low volume (`A3D_MASTER_GAIN=5.0` is the documented default).
3. Copy the **contents** of the selected `Game_Kits/<game>/COPY_TO_GAME_FOLDER` folder beside the real game executable; merge, never replace entire `SndDrivers` directories. Use the kit launcher where provided.
4. **Before Alice 2011**, verify the exact executable/original Miles DLL hashes, and save **two copies** of the genuine `SndDrivers/mss32.dll` as `a3d_mss_real.dll`, one next to `alice.exe` and one inside `SndDrivers`. Do not overwrite the sole original Miles DLL.
5. The **retail Descent 3** kit is a *separate experimental ZIP*: `dist/Aufake3D_v0.9.2_Descent3_Experimental_Win32.zip`. See [Descent 3](DESCENT3_PUBLIC_RELEASE.md).

If the game is silent or the provider is not available, see [Troubleshooting](TROUBLESHOOTING.md). The prior v0.8.18 detailed guide is preserved in [history](HISTORY_INDEX.md).
