# A3D v0.7.3-dev — generic, per-user COM activation experiment

This is a **development milestone**, not a guarantee that every A3D game will work. It introduces a conventional **user-authorised, reversible, Windows COM registration** method, supplementing the existing manifest-only drop-in route. It does **not** inject or patch a game process. The same `a3dapi.dll` is shared across all COM clients using the Aureal CLSID if they support its implementation.

## What changed, and why

Some original 32-bit A3D 2.x clients call `CoCreateInstance({92FA2C24-253C-11D2-90FB-006008A1F441},...)`. When a game's embedded manifest overrides `game.exe.manifest`, a conventional `CreateProcess` launcher does not cause registration-free COM to activate our `a3dapi.dll`. Microsoft documents this precedence. The standard runtime can now optionally **register the same DLL for the current user (32-bit COM view)**. This is normal documented Windows COM installation, not memory manipulation. The procedure requires a deliberate user action; there is **no background auto-registration**.

## Which files and installation location?

- Standard direct audio runtime (unchanged): `a3d.dll`, `a3dapi.dll`, `a3d-direct.exe`, `a3d-abi-survey.exe`.
- **Optional setup utility:** `a3d-com-user.exe` (7 KiB, x86 PE32, imports only ordinary Win32 registry and file APIs). It needs to sit **beside `a3dapi.dll`**.
- Keep the DLL and helper in a **permanent folder** outside the game's installation, for example `C:\A3D-Generic`. Do not move/remove the folder while registered. One registration points to **one exact DLL path** and can be reused by multiple 32-bit games using COM.
- Existing launchers, source port audio loaders, and Miles provider files are **not** included with games and are not automatically configured.

## Windows 10/11 — controlled activation (32-bit COM only)

1. Extract the Standard Runtime and optional `a3d-com-user.exe` into a permanent user-controlled folder.
2. Open a terminal in that folder. Optional read-only check: `a3d-com-user.exe --status` (exit code 0 means this folder owns a per-user registration).
3. **Explicitly authorise** the registration: `a3d-com-user.exe --install`. Do not run as administrator. This edits **only** your current user COM class registration for the A3D2 CLSID, using the 32-bit view.
4. If an A3D class is already registered for the user or machine, the installer **refuses to overwrite it**. This is deliberate; investigate old drivers before making any changes. It does not delete or replace existing vendor registrations.
5. Run `a3d-abi-survey.exe` (or the included script) in a context without its own manifest redirect to verify COM; then stage an offline game candidate using `tools/stage_safe_candidate_v072.py`. Use any game-specific settings/profile as necessary. The survey checks ABI, not real game audio.
6. Before deleting or moving the DLL, run `a3d-com-user.exe --remove` **from the original folder**. It checks an ownership marker, the exact DLL location, and unexpected registry values before removing the owned registration. It does not remove machine-wide registration.

For **portable manifest-only** testing, **do not install COM registration**. Continue with the transparent `a3d-direct.exe`, app-local DLLs and external `game.exe.manifest` where that method works.

## Debian 13 / Ubuntu / Fedora / Arch under Wine

`a3d-com-user.exe` is a **Windows x86** program; run it inside the same Wine prefix that runs the Windows game. Do not use Linux's system registry. From its folder:

```sh
wine ./a3d-com-user.exe --status
wine ./a3d-com-user.exe --install
wine ./a3d-abi-survey.exe
# Later, before deleting or moving installed DLLs:
wine ./a3d-com-user.exe --remove
```

Use a **dedicated test Wine prefix** to avoid collisions with unrelated A3D applications. Modern Wine builds may use WoW64; do not assume `WINEARCH=win32` works. Keep normal Windows activation context/DLL overrides as appropriate for each game. No Wine runtime is present in the package-building host, so actual Wine COM activation is unverified.

## Security, AV and multiplayer

- The **Standard Runtime** retains exactly the existing four safe-audited PE32 DLLs/executables, with no memory-modifying bridge. `a3d-com-user.exe` is **separately optional** because it writes the current user's registry after explicit consent.
- This changes COM registration for the current user while installed and could affect other 32-bit programs relying on this CLSID. The installer refuses to clobber existing keys; only one A3D COM server can be installed in that user/bitness view at once.
- **No guarantee** of Google Drive or antivirus acceptance, malware-free certification, public-server permission, or anti-cheat ban immunity. Do not use on anti-cheat-protected multiplayer servers unless authorised.
- The old process-memory activation bridge stays a **separate offline/explicitly authorised** development tool. No bypass or evasion is attempted.
- Registration still cannot override every custom loader or an embedded manifest specifying a different COM binding. The game must genuinely request the supported A3D CLSID.

## Current API fidelity and compatibility limits

- **A3D 2.0 COM:** existing software renderer, supported COM class factory and known-good game-specific source behaviours; optional per-user activation is new.
- **A3D 1.x:** full DirectSound interception is not implemented. Some legacy exports are approximated, not universal support.
- **A3D 3.x:** extension coverage incomplete. Detecting game dependencies is not emulation.
- **Alice 2000/2011, Quake III 1.17:** existing known-working game-specific launchers remain the regression baseline, with 6×256 (32ms), 48-tap HRTF, gain 5.0, limiter, Alice weapon clarity and VorpalFix settings **unchanged**. No claim that the new COM installation method replaces their working bridges without actual testing.
- **Half-Life and other titles:** game-dependent validation still required.

## Building, auditing, and testing

From source root (Linux host with Clang/lld-link and Python 3):

```sh
bash win32/build.sh
python3 tools/build_generic_v071.py
bash win32/build_generic_probe.sh
python3 tools/build_user_com_v073.py
python3 tools/security_audit_v072.py runtime-v072
python3 -m unittest discover -s tools -p 'test_user_com_v073.py' -q
python3 -m unittest discover -s tools -p 'test_security_v072.py' -q
python3 -m unittest discover -s tools -p 'test_generic_v071.py' -q
```

Before running focused tests from the **standalone source ZIP**, create `runtime-v072/` and `runtime-v073/` by extracting the four unchanged PE32 files from the Standard Runtime into each folder; add the built helper to `runtime-v073/`. (The separately distributed source ZIP intentionally excludes compiled binaries.) The three focused suites then test import safety, current source behavior and clean staging. The historical broad suite can be run from the original full development workspace, which still contains old deployment fixtures.

Imported Win32 functions are audited by `test_user_com_v073.py`. This static audit **does not execute Windows COM** or test modern antivirus/anti-cheat recognition. In the original complete workspace, **127** existing and new tests passed; from a clean source extraction the **17** focused tests passed after rebuilding and restoring runtime binaries to the expected fixture folders.

## Next tests that actually establish compatibility

1. Windows 10/11 **32-bit** `CoCreateInstance` using a dedicated **manifest-free** test executable, before/after `--install` and after `--remove`.
2. The same three-phase test under Debian 13 Wine, then Ubuntu/Fedora/Arch Wine where feasible.
3. One new real A3D 2.0 game that did not previously use our game-specific bridge. Confirm it selects A3D and produces actual HRTF spatial sound, not merely that the EXE launches.
4. Separately implement and test A3D 1.x DirectSound and A3D 3.x extensions. No proxy/original DLL impersonation or unapproved anti-cheat work.
