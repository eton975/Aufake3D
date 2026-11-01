# v0.8.14-RC1 full runtime: binary component and security audit

**Status: runnable developer/public-testing candidate, not antivirus-certified and not certified across all four games.**

Earlier full archives had 15/65, and the v0.8.14-RC1 full archive had **13/68**
VirusTotal ZIP-level detections. The latter contained a 5/71-detected optional COM diagnostic,
now excluded as a prebuilt EXE. The still-included A3D core and Miles proxy have received
low-count individual-file detections. See [component-level security review](SECURITY_REVIEW_V0814_RC1.md)
for the exact hashes and interpretation. **This revised archive has NOT been independently
rescanned. Do not describe it as AV-clean.**

## Security boundaries

- The Alice 2000 bridge, optional Quake III native bridge, and Half-Life experimental helper
  launch an adjacent original game and may modify **that child process in memory** to set up
  local COM activation. They never edit the retail EXE on disk. Such behaviour overlaps with
  malware techniques, may trigger AV, and is NOT suitable for anti-cheat protected multiplayer.
- The fixed universal core comprises exactly `a3d.dll` and `a3dapi.dll` (unchanged hashes from
  the user's successful v0.8.12 RC1 / v0.8.14-RC1 Alice 2011 testing).
- The 331-export `mss32.dll` adapter is the exact previously successful v0.8.9 binary,
  independently recompiled byte-for-byte **without requiring a proprietary DLL at build time**.
  The ABI export-name/ordinal list was extracted from the previously shipped proxy, and the
  C/assembly implementation is available under `Source/Alice2011_NameFix_v089/`. The actual
  original **game-owned Miles DLL is required at runtime** as `a3d_mss_real.dll` (in both
  Alice 2011 game root and `SndDrivers`); no vendor DLL is included.
- This proxy reproducibility is a **technical** finding. The legality of distributing an
  export-interface-compatible binary still warrants rights-holder review before broad publication.
- Original Aureal binaries, SDK binaries, original Miles DLLs, game executable/data, and VorpalFix
  are not included.
- No arbitrary system-wide registry writes or executable-on-disk patches are performed by the
  normal kit installation. Game-local installers provide rollback. The process-memory bridges
  should be tested only with lawful local copies of offline games.

## What is actually verified?

Source rebuild of core/proxy/legacy helpers, export hashes and architecture, included game kit
manifests, source tests, and installer/rollback tests in a synthetic sandbox. **Not verified:**
per-file VirusTotal results for this rebuilt package, safe execution on an arbitrary PC,
Windows/Wine integration for all four profiles, or completeness of copyright permissions.

## Game support

| Profile | Installed executables | Confidence |
|---|---|---|
| Alice 2011 / VorpalFix 4.2.1 | game-owned `alice.exe`, rebuilt `mss32.dll` proxy | **Working Windows baseline reported by tester**, original DLL required |
| Alice 2000 | game-owned `alice.exe`, rebuilt `alice-a3d-bridge.exe` | **New bridge binary untested on Windows**; requires exact expected game build |
| Quake III Arena 1.17 | game-owned `quake3.exe` | Previously working on earlier versions; v0.8.14-RC1 retest pending |
| Half-Life 1.0.1.1 | game-owned `hl.exe` plus optional rebuilt `halflife-a3d-alpha.exe` | Experimental; compatibility NOT established |
| Unreal / other titles | optional source-built experimental helpers in Extras | Research-only, no claim of working A3D 3.0 |

The working Alice 2011 original DLL adapter is **not** a replacement for the proprietary
Miles DLL, and the optional process-memory launchers are not required for every game.

## Static import inventory

`Docs/BINARY_IMPORT_AUDIT.json` documents direct PE imports by SHA-256 and clearly
identifies those with child-memory modification APIs. No selected DLL/EXE has a directly
imported Winsock/WinINet/WinHTTP library; **dynamic imports and runtime behavior are not
ruled out** by this observation. This is a reproducibility aid, not malware clearance.

The *fresh rebuilt* Alice 2000, Half-Life and Quake III experimental executable hashes
are different from the older files in the 15/65 VirusTotal ZIP. The old verdict
**does not transfer numerically** to these new binaries; each needs its own scan.

## v0.8.14-RC1 security documentation revision

The optional precompiled `Extras/Diagnostics/a3d-selftest.exe` is removed from the full runtime package. Its source and build recipe remain. This does not alter any installed game kit, the normal executable launchers, the working audio DLLs, or the Miles proxy. See [SECURITY_REVIEW_V0814_RC1.md](SECURITY_REVIEW_V0814_RC1.md) before public binary redistribution.
