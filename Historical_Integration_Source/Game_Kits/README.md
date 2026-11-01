# Ready-to-copy game kits

Open the folder for your game and enter `COPY_TO_GAME_FOLDER/`. Copy **its contents** into
the directory containing your original game executable. If a `SndDrivers` folder appears,
merge its contents into the original game's `SndDrivers` folder (do not replace the entire folder).

| Game | Kit directory | Original executable |
|---|---|---|
| Alice 2000 | `Alice_2000` | `alice.exe` |
| Alice 2011 / VorpalFix 4.2.1 | `Alice_2011_VorpalFix` | `alice.exe` |
| Quake III Arena 1.17 | `Quake_III_117` | `quake3.exe` |
| Half-Life 1.0.1.1 | `Half_Life_1011` | `hl.exe` |

**Alice 2011 is a special case:** before copying the kit, preserve the original
`SndDrivers/mss32.dll` as **both** `a3d_mss_real.dll` in the game root **and**
`SndDrivers/a3d_mss_real.dll`; confirm the matching hashes in [the manual](../Docs/MANUAL_INSTALLATION.md).
The original `mss32.dll`, VorpalFix, and retail games are not included in this release.

**Do not copy the kit folder itself into the game folder.** Copy everything *inside*
`COPY_TO_GAME_FOLDER/` so `a3dapi.dll` sits alongside `alice.exe`, `quake3.exe`, or `hl.exe`.

The two `a3d*.dll` files in each kit are **byte-identical** to the copies in
[`Universal_Core/`](../Universal_Core/). The duplication is intentional: each kit
can be copied directly, and no game requires its own fork of the renderer.

The automatic installers use [`INSTALL_MAP.json`](INSTALL_MAP.json), the same exact
kit contents, and safe rollback receipts. No undocumented per-game files are added.
