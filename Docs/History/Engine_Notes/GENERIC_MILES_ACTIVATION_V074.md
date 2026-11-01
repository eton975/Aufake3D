# A3D v0.7.4-dev — registration-free Miles/A3D2 activation research

**Status:** Experimental development build. Compiles and passes structural tests; **not yet verified in Alice 2011, Windows COM, or Wine gameplay**. The original working Alice 2000/2011, Quake III and Half-Life profiles are preserved; no audio-rendering changes.

## Why v0.7.4 exists

The Alice 2011 evidence is unusually specific:

- Independent `a3d-abi-survey.exe` succeeds at `IA3d4` / A3D2 COM creation.
- `a3d-com-user.exe --status` says the per-user A3D COM class is registered.
- The real game reports that A3D2 cannot initialise, even with `+set s_milesdriver a3d2`.
- ProcMon shows `SndDrivers\\mss32.dll`, `SndDrivers\\mssa3d2.m3d`, and VorpalFix `winmm.dll` successfully loaded; the A3D DLL did not load during that captured session.
- That suggests *selection/provider opening* may fail before the A3D COM server is used. It does NOT establish whether the provider attempted COM and failed on another path.

The v0.7.3 registry helper is not an acceptable final user-experience. This release investigates two explicit, **registration-free** techniques without patching any original game executable.

## Part 1 — app-local, no-registry COM survey (ready to test)

The standard runtime contains:

- `a3dapi.dll` / `a3d.dll` — unchanged, known audio engine, copied from pinned v0.7.3 runtime.
- `a3d-direct.exe` — ordinary process launcher, does not inject into game memory.
- `a3d-abi-survey.exe` — existing ordinary ABI probe.
- `a3d-regfree-survey.exe` + `a3d-regfree-survey.exe.manifest` — standalone copy of the ABI survey, with a **matching external app manifest** pointing to the local `a3dapi.dll` COM class.

Open a console in the extracted runtime and run `a3d-regfree-survey.exe` (Windows) or `wine a3d-regfree-survey.exe` (Debian 13 or another Wine distribution). `IA3d4: YES` establishes this test executable can activate the local COM server. **If you still have A3D per-user registration installed, success alone does not establish registration-free activation** because Windows could fall back to that registration. To isolate reg-free COM, remove the *owned* registration using the original v0.7.3 helper from its original folder (`a3d-com-user.exe --remove`) only after reviewing its ownership check. This must be a voluntary user action. Do not delete registry values manually.

The test app manifest can work when an application's embedded manifest does not supersede it; it does **not** automatically solve Alice's manifest/provider selection problem.

## Part 2 — experimental app-local Miles proxy (build against YOUR owned MSS32)

For Miles 5/6-era titles such as Alice, this is a **diagnostic and activation adapter** rather than a new Miles sound engine. It is not a ready-made replacement for an arbitrary vendor `mss32.dll`.

The package includes `v074/miles_com_adapter.c` and a builder `tools/build_miles_adapter_v074.py` that:

1. Parses a user-owned **32-bit** original `mss32.dll` export table; rejects malformed, forwarded, unnamed, ambiguous or unsupported export patterns.
2. Creates an exported `mss32.dll` proxy tailored to *that exact file*, preserving the original named ordinals.
3. Forwards unrelated original exports to a byte-identical copy named `a3d_mss_real.dll` in a **new isolated output directory**.
4. Intercepts only Miles provider enumeration and `AIL_open_3D_provider` calls.
5. Creates an activation context around `AIL_open_3D_provider` from the adjacent `a3d-miles-local.manifest`, which maps the A3D2 CLSID to local `a3dapi.dll` without registry writes.
6. Optionally writes bounded `a3d-v074-miles.log` when `A3D_MILES_TRACE=1` is set (64 KiB cap; no logging otherwise).

**Important limitations:** If the game never selects/opens the provider, the proxy cannot force it to do so. If the original Miles DLL calls provider-open functions internally rather than through its public exports, the proxy may not intercept those calls. Renaming a vendor DLL can break self-references or RIB interfaces; this is why v0.7.4 remains **experimental and offline-only** until game-specific verification. It is **not anti-cheat certified** or guaranteed acceptable to multiplayer servers. Never substitute this proxy into a live/anti-cheat multiplayer install without explicit permission.

### How to create a test overlay (on a machine with Python 3, Clang and lld-link)

Do **not** point output at your original game directory. Use a separate, backed-up test installation:

```sh
python3 tools/build_miles_adapter_v074.py \
  --original-mss32 /path/to/your/Alice2011/bin/SndDrivers/mss32.dll \
  --a3dapi /path/to/extracted/Standard_Runtime/a3dapi.dll \
  --validate-only

python3 tools/build_miles_adapter_v074.py \
  --original-mss32 /path/to/your/Alice2011/bin/SndDrivers/mss32.dll \
  --a3dapi /path/to/extracted/Standard_Runtime/a3dapi.dll \
  --output /path/to/a-new/OverlayFolder
```

Review `OverlayFolder/README_TEST_OVERLAY.txt`. In a **separate backup test copy** of `Alice2011/bin/SndDrivers`, save the original `mss32.dll` safely and stage `OverlayFolder/mss32.dll`, `a3d_mss_real.dll`, `a3dapi.dll`, `a3d.dll`, and `a3d-miles-local.manifest`. Nothing is automatically copied to a game folder by the builder. Keep VorpalFix `winmm.dll` in place, leave the original `mssa3d2.m3d` unchanged. Set `A3D_MILES_TRACE=1` and `A3D_LOG=1` in the SAME console used to launch the game. Run the game without the old injected/patching bridge.

If a log is created, inspect the lines `PROVIDER_ENUM`, `PROVIDER_OPEN_BEGIN`, `A3D_LOCAL_ACTCTX_ACTIVE` and `PROVIDER_OPEN_RESULT`. These establish which parts of Miles' normal public API are exercised. `PROVIDER_ENUM` without `PROVIDER_OPEN_BEGIN` suggests game-side selection; a failed activation context suggests a manifest/path error. If no log appears, the proxy may not have loaded, or the game may invoke internal rather than exported Miles functions.

On Windows 10/11 use a normal test installation without multiplayer anti-cheat. On Debian 13/Wine use a dedicated Wine prefix and native DLL overrides as needed for the user's own game DLLs; **real Wine testing has not been performed in the build environment**. Do not copy original proprietary vendor DLLs into shared public ZIPs. The generator creates a private user-specific overlay and is intentionally not auto-run by the game launcher.

### How to roll back

Delete the experimental test copy, or restore the user-owned original `mss32.dll` into the **test copy** after removing the proxy and `a3d_mss_real.dll`. Do not change the registered COM class during proxy testing unless running a carefully controlled separate COM test. Never overwrite the only copy of a game installation.

## Sound quality and compatibility guarantees (unchanged source)

- Alice 2000: snapshot renderer, fixed 6x256 WaveOut 48kHz (32 ms), HRTF 48 taps.
- Alice 2011: legacy renderer, 6x256, VorpalFix's own FPS control by default, optional 144 FPS profile.
- Quake III 1.17: snapshot renderer, 6x256.
- Master gain 5.0, peak limiter, Alice weapon clarity as previously implemented; defaults are **not** modified by this v0.7.4 release.
- A3D 1.x DirectSound full interception and A3D 3.x extensions are **not yet implemented**.

## Build and test

```sh
bash win32/build.sh
bash win32/build_generic_probe.sh
python3 tools/build_generic_v071.py
python3 tools/build_user_com_v073.py
python3 -m unittest discover -s tools -p 'test_*.py' -q
```

`tools/test_miles_adapter_v074.py` creates a synthetic Miles DLL for structural tests and verifies export forwarding, proxy API imports, no game modification, and the registration-free manifest. This is **not proof of running through the original Miles DLL**.

## Distribution, security, malware false positives and anti-cheat

Keep the **Standard Runtime** separate from the **Optional Miles Adapter Kit**. The adapter may be viewed as an altered middleware DLL by anti-cheat and malware heuristics despite its benign goals; no attempt is made to evade detection. Distribute readable source and SHA-256 manifests and request formal false-positive reviews when necessary. Google Drive acceptance and server approval are not asserted. Any future real-game interoperability needs separate, explicit testing.
