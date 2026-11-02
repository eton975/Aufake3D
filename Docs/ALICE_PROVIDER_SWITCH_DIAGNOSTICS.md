# Alice 2000 / 2011 — provider-switch investigation (v0.8.17 diagnostic candidate)

## Known facts and limitations

Alice 2000 and Alice 2011 launchers in v0.8.16 both pass
`+set s_milesdriver a3d2` **on every process launch**. This can override
saved provider choices on the next launch. This is a separate issue from an
in-game change whose menu label updates but whose audio stays spatialized.

The Alice 2000 selector bridge only adds handling for `a3d2`; the normal
`miles`, `dolby`, `a3d`, `eax` and `eax2` cases pass through unchanged. The
Alice 2011 Miles proxy likewise forwards the game's real selected handle.
The A3D engine stops its WaveOut mixer when the COM root is finally released
(or when its Shutdown method is called). **No supplied standalone test yet
proves that the game performs that cleanup during an in-menu switch.**

This candidate deliberately adds **diagnostics, not an unverified forced
shutdown**. Calling `mixer_shutdown()` merely because the menu mentions 2D
could prematurely invalidate still-live A3D source objects, crash the game,
or interfere with the actual Miles provider's lifetime ordering.

## Test on Windows (use a backup/test game installation)

1. Keep the existing working v0.8.16 game configuration and your saved games.
   Only deploy these diagnostic DLLs if built from this candidate source.
2. Open a fresh `cmd.exe`, `cd /d` to the appropriate game's directory, and
   enable bounded diagnostic logging **in the same prompt**:

   ```bat
   set "A3D_LOG=1"
   set "A3D_TRACE_DETAIL=0"
   set "A3D_PROBE_LOG=a3d-switch-probe.log"
   set "A3D_MILES_TRACE=1"
   ```

   The engine log caps output at 1 MiB per process. The Miles proxy trace
   caps itself at 64 KiB and applies to **Alice 2011's proxy profile**;
   Alice 2000's standard bridge doesn't necessarily load this proxy.
3. Run `RUN_AUFAKE3D_WINDOWS.cmd` *from this same prompt*. Start a level with
   a clearly spatialized source, switch `A3D2 -> Miles 2D -> A3D2`, and
   note whether the game needs a sound restart/reload for a change to take
   effect. Repeat for Dolby 2D separately. Do not infer success from the
   menu label alone.
4. For Alice 2011, inspect `SndDrivers\a3d-v074f-miles.log` (proxy location
   may vary with installation layout). Correlate `AIL_OPEN_A3D2_CONFIRMED`,
   `AIL_CLOSE_A3D2_BEGIN`, `AIL_OPEN_2D_CONFIRMED`, and
   `AIL_CLOSE_RETURNED`. **An open with no close can indicate a lifetime
   problem, but logs cannot prove a leak without process-state evidence.**
5. Inspect `a3d-switch-probe.log` (created in the game's current directory,
   unless overridden) for `A3D.Root final external Release`,
   `IA3d4.Shutdown mixer`, and `A3D.Mixer stopped`. If no mixer stop appears,
   check whether the A3D root was actually released before assuming the
   wrapper intentionally forced 3D. If the file does not appear, the DLL may
   not have loaded or logging was not inherited.
6. Repeat with **a clean process launch** and a 2D selector supplied
   directly, instead of opening with forced A3D2:

   Alice 2000:
   ```bat
   alice-a3d-bridge.exe +set s_milesdriver miles
   ```

   Alice 2011:
   ```bat
   alice.exe +set s_milesdriver miles
   ```

   This 2D-only control helps distinguish a live switching failure from an
   A3D2 initialization/launcher override. Restore normal launcher afterward.

## How to interpret results

- **No `AIL_OPEN_2D_CONFIRMED` after changing the 2011 menu:** the game may
  have updated its preference without reopening the sound provider; inspect
  its sound restart behavior before changing A3D runtime internals.
- **2D really opens, but A3D2 is not closed and the mixer keeps running:**
  investigate the game's Miles shutdown ordering, A3D COM references and
  whether the old A3D2 worker is still playing.
- **2D opens and A3D shuts down, yet 3D still seems audible:** differentiate
  conventional Miles 2D positional panning from HRTF; don't diagnose solely
  by ear.
- **Restarting the process resets the preference to A3D2:** the standard
  launchers' explicit `+set s_milesdriver a3d2` is a likely cause.

**Acceptance criteria for a subsequent true v0.8.17 fix:** switch A3D2 ->
Miles 2D -> A3D2 -> Dolby 2D without residual A3D WaveOut output, unwanted
reinitialization, hangs or silent audio, including repeated runs in both Alice
releases. Current mock tests check **handle identity and forwarding only**,
not in-game HRTF disablement.
