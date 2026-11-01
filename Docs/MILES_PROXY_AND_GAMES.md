# Miles adapter, provider identity and game integration

## Alice 2011 v0.8.9 scoped naming adaptation

The original game selector doesn't natively map the string `a3d2` to an A3D2
provider name. The optional app-local `mss32.dll` proxy forwards 331 Miles
exports and wraps only the required selection/activation entrypoints. It
returns a temporary proxy-owned `unknown` string to satisfy the game's
hardcoded lookup, **using the genuine enumerated A3D 2.0 provider handle**.
After a successful Miles provider open, that same proxy-owned buffer becomes
`Aureal A3D 2.0 (TM)` for display. It does not patch the game executable or
swap the provider handle. This is a compatibility translation, not a native
change to the game's selector table.

Source: `Source/Alice2011_NameFix_v089/miles_selection_v089.c`, export surface
`MILES_EXPORT_SURFACE_331.json`, and vendor-free builder
`build_proxy_from_export_map.py`. The original game-owned Miles DLL is *not*
distributed. At runtime, a compatible user-provided original is preserved as
`a3d_mss_real.dll` where required by the installation guide.

## Scope and audit limitations

- The implementation is pinned to a known Alice 2011/VorpalFix+Miles profile;
  Alice 2000 naming is **not confirmed** to follow the same path.
- A printed provider name is insufficient validation. Correlate enumeration
  identity, the handle used in `AIL_open_3D_provider`, successful open and a
  created listener. An independent COM probe is not evidence that Miles
  selected the same provider.
- The vendor-free 331-export map is a set of names/ordinals, not bundled
  proprietary Miles implementation code; redistribution rights and AV review
  are still separate questions from reproducible compilation.
- Some other game kits use legacy in-memory launch adapters. These may call
  remote-process memory APIs and can trigger heuristic AV detections. Label
  them experimental, audit imports, and never imply that a rebuild is
  equivalent to antivirus clearance.

## Supported game profiles, not blanket compatibility claims

| Game | Integration | Status |
|---|---|---|
| Alice 2011 with VorpalFix 4.2.1 | Pinned Miles name/COM adapter | User-reported good Windows playback with unchanged core |
| Alice (2000) | Legacy bridge path | Needs independent A3D2 naming and gameplay verification |
| Quake III Arena 1.17 | Game-local A3D core; optional experimental launcher | Previously worked on earlier builds; current release retest needed |
| Half-Life 1.0.1.1 | Experimental activation/bridge | Not validated end-to-end on current runtime |
| Unreal / Unreal Tournament / Unreal II / Halo PC | Future API identification and adapters | No blanket A3D3 support claimed |

See `Docs/MANUAL_INSTALLATION.md`, `Docs/COMPATIBILITY_PLAN.md` and the
release-security and licensing notes before copying any executable helper.
