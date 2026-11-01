# v0.7.2-dev — Safer-by-default generic distribution (2026-11-01)

**Scope:** packaging, launcher selection, security audit, honest compatibility
reporting, not a change to A3D synthesis, game-specific profiles, or anti-cheat.

## Changes since v0.7.1

- The normal runtime contains exactly four PE32 files: `a3dapi.dll`, `a3d.dll`,
  `a3d-direct.exe`, and `a3d-abi-survey.exe`.
- `a3d-launch.exe` moved to a physically separate **Legacy Offline Bridge** ZIP.
- New `stage_safe_candidate_v072.py` stages only standard files, never modifies
  a game directory or registry and documents existing-filename conflicts.
- Static `security_audit_v072.py` inspects imports in each runtime PE, rejects
  selected remote modification and injection APIs, malformed files, and unexpected
  binaries. Its report is included, with SHA-256 hashes and clear limitations.
- Updated beginner Windows and Debian/Linux Wine procedures; separate source
  and runtime archives, no bundled proprietary game assets, deterministic ZIP
  timestamps, checksums, regression tests and source-build documentation.
- External game.exe manifests may be ignored, particularly if the game embeds
  its own manifest. Normal launch does **not** guarantee A3D2 activation.

## Verified / not verified

- Verified: Python audit and tests; clean-source Clang/LLD builds; normal
  launcher has no banned remote-process API imports; standalone kit stages
  without modifying game files; ZIP hashes/CRCs checked; Bash syntax.
- Not verified: Google Drive upload clearance, any vendor's malware verdict,
  anti-cheat acceptance, Quake III multiplayer, live Windows game audio or
  Debian 13/Wine gameplay with this new packaging.
- Do not interpret non-invasive activation as proof of anti-cheat safety.
