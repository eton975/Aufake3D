# Unofficial Aureal A3D v0.6.12 — Alice Weapon Clarity (experimental)

**Purpose:** Improve audibility of recognisable weapon sounds during dense enemy audio, using a shared, conservatively gated sidechain. This is an experimental A/B build, not yet a verified fix for all weapons or scenes. It is based on the v0.6.11 diagnostic evidence from both Alice 2000 and Alice 2011. No original game content is supplied.

## What's different

- **Alice 2000 and Alice 2011** default launchers set `A3D_WEAPON_CLARITY=1`, unless the environment already defines it. Quake III 1.17 sets it to `0`; its existing audio configuration is not changed.
- A metadata-only set of **15 distinct known 4KiB source-buffer FNV-1a signatures** for **14 confidently identified weapon sample names**, including two validated `staff_charge1.wav` buffer variants, is generated from the user's v0.6.11 diagnostic reports. These are **not** copies of the game samples. It is a conservative signature list; unmatched weapons are left unchanged. Source-buffer rewrites or different game releases may cause nonmatches. No runtime FFT/matched filtering or raw PCM capture is needed.
- In the shared PCM spatial renderer, confidently recognised weapon sources are separated into a protected bus **after spatialisation**. With **4+ active voices** and an audible protected source, competing non-weapon effects are ducked smoothly, no more than about **3.7 dB**, without directly increasing weapon amplitude or bypassing HRTF/occlusion. Attack ~6ms and recovery ~180ms; inactive or unrecognised sources do not trigger it.
- The existing stereo-linked 0.95-peak limiter is retained. Only when clarity is enabled, its recovery increment doubles to shorten audible pumping, while attack, clipping ceiling, spatial imaging and the default `A3D_MASTER_GAIN=5.0` remain unchanged.
- `RUN_A3D_ORIGINAL_MIX_WINDOWS.cmd` and `RUN_A3D_ORIGINAL_MIX_WINE.sh` explicitly disable clarity, returning to **the v0.6.11 mixing algorithm** with the same DLL. The normal `RUN_A3D_144FPS_*` Alice 2011 launchers still work and inherit the experimental clarity default; VorpalFix still manages the default FPS cap.

## Audio configurations preserved

| Game | Renderer | WaveOut queue | Clarity by default |
| --- | --- | --- | --- |
| Alice 2000 | Snapshot | 6 x 256 = 32ms | Experimental ON |
| Alice 2011 + VorpalFix | Legacy | 6 x 256 = 32ms | Experimental ON |
| Quake III v1.17 | Snapshot | 6 x 256 = 32ms | OFF |

All use the existing 48-tap HRTF, normal WaveOut worker thread priority, shared binaries, bounded optional logging, and 5.0 master gain. Neither Alice game EXE nor Miles/VorpalFix installation is replaced.

## Quickstart

1. **Back up** your functioning v0.6.9/v0.6.11 DLLs and game directory before installing, especially Alice 2011's original VorpalFix `winmm.dll`.
2. Install the appropriate `Alice2000` or `Alice2011-VorpalFix` files into the legally installed game folder. The original EXE, Miles provider and VorpalFix (2011) must already be present.
3. Launch `RUN_A3D_WINDOWS.cmd` (or `RUN_A3D_WINE.sh`). Play normally.
4. If any weapon sounds unnatural or become harder to hear, launch `RUN_A3D_ORIGINAL_MIX_WINDOWS.cmd` (Wine equivalent) to compare exactly the earlier mixing behaviour. **No replacement DLL required.**
5. Optional: set `A3D_LOG=1` when launching to produce the usual bounded log. `A3D_WEAPON_CAPTURE` and staff diagnostics are **off by default**.

## Constraints / what is not demonstrated

- Real Windows gameplay with v0.6.12 and Debian 13/Wine sound output are **not** verified by offline tests. The only game tests so far are on earlier builds. Do not treat this as an established cure until it sounds right in both Alice titles.
- The signature matcher can only protect samples already recognised during the two historical sessions. **14 of 100 archive sound names** have confident signatures; others need future additions. It does not automatically classify all game sounds as weapons.
- When background effects cause strong peak limiting, ducking should reduce competition and sometimes reduce limiter suppression. It does not guarantee a particular weapon will be audible at all times or override game-side voice stealing.
- Original game assets are never distributed and no user's diagnostic PCM is included.

## Engineering test commands

```sh
bash win32/build.sh
python3 -m unittest discover -s tools -p 'test_*.py' -q
gcc -std=c11 -O2 win32/test_clarity_v0612_native.c -o /tmp/a3d-clarity-test && /tmp/a3d-clarity-test
```

The native clarity test verifies bypass bit-for-bit in one synthetic scene, ducking bounds, quiet-scene bypass, and output saturation. It does not substitute for Windows/Wine integration tests.
