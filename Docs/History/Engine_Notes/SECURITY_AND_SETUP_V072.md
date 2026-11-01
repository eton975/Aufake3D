# A3D v0.7.2-dev: transparent runtime and multiplayer-aware distribution

**Development build; not antivirus-cleared, anti-cheat-certified, or a universal A3D emulator.**

This release addresses two separate risks from v0.7.0-alpha:

1. **False-positive malware-policy restrictions:** The old archive combined duplicated binaries with advanced startup/child-memory modification bridges. The **Standard Runtime** now contains *only four* conventional 32-bit files, and each file's imports and checksum can be audited. The opt-in bridge is distributed separately. This may reduce heuristic detections, but **Google Drive and antivirus vendors may still flag a file**. We do not disguise software or bypass scanning.
2. **Multiplayer bans:** The Standard Runtime does not use suspended-child process patching, remote memory APIs or thread-context changes in its launcher, and does not automatically install into game directories. **This is not anti-cheat approval**. A game/server may forbid any replacement DLL, changed audio client, or unapproved third-party software. Do **not** take either runtime onto protected multiplayer servers without their explicit permission.

## What is in each archive

- `A3D_v072_Standard_Runtime.zip` — four PE32/x86 files under `Runtime/`, general-purpose candidate scanner/stager, security audit, fresh instructions and their SHA-256 checksums. **No a3d-launch.exe, injection/bootstrap code or special Half-Life patch launcher.**
- `A3D_v072_Legacy_Offline_Bridge.zip` — the separately isolated v0.7.1 `a3d-launch.exe` and explanation of its **optional, process-memory-changing** activation. For offline/local use or *explicitly authorised* testing only. This is not recommended for protected multiplayer.
- `A3D_v072_Full_Source.zip` — full source of the A3D engine, regular/direct launchers, old optional bridge, scanner, stager, tests, and build/audit scripts. Source files are not automatically executed by extracting them.

## Windows: standard runtime, new candidate game (safe installation procedure)

1. Extract `A3D_v072_Standard_Runtime.zip` to a working folder **outside** the game installation.
2. Use Python 3 to scan an owned, 32-bit Windows game *without modifying it*:
   ```powershell
   py tools\scan_a3d_clients.py "C:\Games\Example\System" --out a3d-scan.json
   ```
3. Stage a new overlay **outside** the game directory:
   ```powershell
   py tools\stage_safe_candidate_v072.py "C:\Games\Example\System" --exe Example.exe --out "C:\A3D-Experiments\Example-overlay"
   ```
4. Inspect the overlay's `INSTALL_PLAN.json`, the checksums and the list of filename conflicts. **Back up any existing game files before manually copying anything.** The tool itself does not edit the original game or register COM globally.
5. For a local/offline trial, copy approved overlay files beside the game's existing EXE (not necessarily its installation root), then run `RUN_A3D_ABI_SURVEY_WINDOWS.cmd` for an ABI/COM sanity check. An ABI survey succeeding does not prove the game will run A3D.
6. In the game, select its supported A3D2 audio backend, if one exists; then launch `RUN_A3D_WINDOWS.cmd`. Diagnostics are off by default; `RUN_A3D_DIAGNOSTIC_WINDOWS.cmd` enables bounded logging.
7. To revert, restore backups and remove *only* files you installed. Never replace proprietary game EXEs.

**COM manifest caveat:** The candidate overlay provides a registration-free COM manifest for `a3dapi.dll` adjacent to the original game EXE. The manifest might not be honoured if the game has an embedded manifest or uses a different COM loading path. `a3d-direct.exe` does only a conventional `CreateProcessA`; it cannot force the child to activate an external manifest. That is an intentional limitation, not a silent fall-through to invasive bootstrap. A3D1 DirectSound and A3D3 extensions are not fully implemented.

## Debian 13, Ubuntu, Fedora and Arch / Wine

Wine must support running 32-bit Windows binaries. Use your distribution's documented Wine/WoW64 installation and a configured Wine prefix. **Do not assume `WINEARCH=win32` is supported on modern new-WoW64 builds.** In the extracted kit:

```sh
python3 tools/scan_a3d_clients.py "$HOME/Games/Example" --out a3d-scan.json
python3 tools/stage_safe_candidate_v072.py "$HOME/Games/Example" --exe Example.exe --out "$HOME/A3D-Experiments/Example-overlay"
```

Review the overlay and backups, manually install it next to the original Windows EXE, then from that game directory run:

```sh
bash RUN_A3D_ABI_SURVEY_WINE.sh
bash RUN_A3D_WINE.sh
```

The Wine launch script uses the `wine` executable (override with `A3D_WINE_EXECUTABLE`) and native-first `a3dapi`/`a3d` DLL overrides. Availability and acoustic correctness under real Wine are **not validated by the offline build tests**.

## Checking file integrity and imports

- `SHA256SUMS.txt` in each archive lists every other file, with stable paths relative to the archive root.
- `SECURITY_AUDIT_v072.json` lists all imported API symbols and identifies restricted functions. Audit source: `tools/security_audit_v072.py`.
- Re-run the audit locally:
  ```sh
  python3 tools/security_audit_v072.py Runtime --output local-audit.json
  ```
  This rejects unexpected/malformed PE files, incorrect architecture, unexpected binaries, and selected remote-process modification API imports.
- This **cannot** inspect dynamic symbol resolution, detect malware, certify loaded modules at runtime, or establish an anti-cheat whitelist. Source review, signed releases and independent antivirus assessment remain necessary.
- The runtime DLLs retain the original v0.7.0-alpha A3D2 DSP code and were **not re-engineered for this security packaging update**. Rebuilt generic direct launcher is byte-identical to the pinned previous launcher in this environment. Core DLLs can be compiled from the source, but a separate rebuild need not have the same hash as the pinned runtime; do not claim binary reproducibility without an independently verified bit-identical build.

## Malware false-positive review

Google Drive's warning that a file may violate the malware policy does not disclose a specific malicious component. Do **not** hide executables in misleading formats, encrypt them to conceal their contents, or instruct others to disable security controls. For a restricted file you own, use **Share → Request a review**, when available, explaining truthfully that this is an open-source, unsigned legacy-game audio compatibility package. Include the public source location, hashes, and a list of the actual Windows APIs used; note the optional legacy bridge is intentionally **not bundled in the Standard Runtime**. Seek feedback from anti-malware vendors through official false-positive submission processes. A review may not result in reinstatement.

## Multiplayer and deployment policy

- Use the Standard Runtime offline or on a private server where the owner explicitly permits it. Do not assume that passing `sv_pure` in Quake III or a static import audit means compliant multiplayer play.
- Any old legacy bridge (`a3d-launch.exe`), Half-Life in-memory splash workaround or similar modified-process loader is kept only in the separately labelled offline/authorised package.
- Prefer normal engine sound-plugin APIs or officially sanctioned source-port integration when available. Do not attempt to conceal DLL loads or defeat integrity checks.
- Do not promise users that the software is safe from bans; the server/anti-cheat provider determines what is accepted.

## Preserved audio development baseline

- Existing Alice 2000 and Alice 2011 and Quake III profiles: **6×256** WaveOut buffering at 48kHz (32ms nominal), 48-tap HRTF, default **5.0** gain with linked peak limiting; Alice-specific weapon clarity settings and 2011's VorpalFix FPS policy are unchanged in the original game-specific releases.
- **Generic candidate settings:** snapshot/renderer choice still requires verification per game, weapon clarity defaults to OFF and no game is automatically labelled compatible based solely on static detection.
- The v0.7.2 files are distribution/staging changes. They are **not** a new acoustics or A3D1/A3D3 feature implementation.
