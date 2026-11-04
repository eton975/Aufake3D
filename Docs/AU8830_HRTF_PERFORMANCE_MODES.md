# AU8830 56-tap renderer: performance and fidelity (v0.9.0 development candidate)

## Status: experimental, hardware-derived, **not bit-exact**

A contributor-provided Vortex 2 Windows-driver register capture, corrected at
exactly 180 degrees, supplies 217 positions and two **56-tap signed Q15** FIR
filters per position, plus two interaural delay values in units of 1/512 sample.
`data/vortex2_hrtf_grid_15deg_fixed180.csv` is validated and converted into the
source header by `python Tools/generate_vortex2_hrtf.py`. The full table uses
bilinear angular interpolation, with a single top-pole elevation at 90 degrees.
This is a candidate for greater spatial faithfulness, **not a reconstructed
AU8830 board emulator**. See the original reverse-engineering project:
https://github.com/z2k-retro/aureal-vortex2-tools

| `A3D_HRTF_MODE` | Implementation | Intended use |
|---|---|---|
| `fast` (optional override) | Full 56 taps/ear; bilinear target update per block; 64-sample HRTF/ITD tracking; per-ear input ITD before FIR | Normal gameplay; currently matches reference acoustically while optimization is validated |
| `reference` (default in game launchers) | Same 56 taps, ITD and 64-sample coefficient/ITD glides as `fast` | Reference for future *output-preserving* FAST optimizations |
| `legacy` | Previous 24/48/96-tap KEMAR-based renderer (default 48 if selected); unchanged processing path | Rollback and regression testing |
| `bitexact` | **Not implemented**; explicitly warns when logging enabled and uses `reference` | Never claim bit-exact output without digital hardware comparisons |

Set this variable **before** launching a game and restart the game after changing it.
Examples (PowerShell):

```powershell
$env:A3D_HRTF_MODE = 'fast'
.\RUN_AUFAKE3D_WINDOWS.cmd
```

Or use `fast` or `legacy`. The launcher sets `reference` only if the caller has
not defined a mode, so a user override is respected. The HRTF mode is unrelated
to `s_milesdriver`; it must **never** force the game to select A3D2 or retain
A3D2 when the player chooses Miles or Dolby. The original Alice selector bridges
remain in place. Master gain still defaults to 5.0 with a stereo-linked limiter.

### 0.9.0 56-tap acoustic correction candidate

User listening comparisons in Alice 2000 and Quake III 1.17 rated the prior
renderer `legacy` > `reference` > `fast`. A code audit located two concrete
errors: `fast` discarded the measured parameter glide on every 256-frame
block, and both 56-tap modes delayed each ear's **FIR output** instead of
feeding the FIR its delayed mono input. Both are now corrected. A native
moving-source test exercises parameter changes across render blocks and
requires identical `fast`/`reference` PCM. This fixes identifiable DSP
architecture errors, **not** yet the perceptual gap versus `legacy`.

The full 56-tap output, ITD scaling and angular lookup still need comparison
against physical SQ2500/AU8830 output. A result that sounds better is not
proof of hardware accuracy, and a synthetic host-CPU benchmark is not an
FX-6300 or dense-game CPU measurement. All game modes remain user-selectable.

### What we matched and what remains approximate

- Full signed Q15 **coefficient values** and the two-ear ITD target words are
  taken from the corrected CSV; `180°` rows were reconstructed, not captured.
- HRTF/ITD interpolation is **float bilinear**. Input angle conversion uses a
  lightweight atan2 approximation; this has not been checked against the
  historical Aureal driver's exact angle quantization.
- Both 56-tap modes now use `0x147*64/2^21` HRTF tracking and
  `0xC8*64/2^19` ITD tracking per 64 samples. The per-ear ITD is applied
  to source PCM **before** that ear's FIR, matching the chip signal order.
  The **gain and atmospheric two-pole filters
  are still Aufake3D's existing models**, not copied AU8830 registers.
- FIR and fractional delays run as float, ITD uses linear fractional-delay
  interpolation. The AU8830's per-product integer rounding/saturation and
  exact delay-line algorithm have **not** been established. A sample-exact
  claim would be scientifically premature.
- The 6×256, 48-kHz, 32-ms WaveOut queue remains unchanged. Neither mode
  adds audio-thread file I/O or heap allocation.

### Performance-budget philosophy

The renderer performs approximately 112 multiply-accumulates per active voice
per sample for its direct HRTF (two 56-tap filters). At 48 kHz that is about
**5.38 million MACs/voice/second** (excluding input/resampling, reflections,
geometry, ITD, reverb and mixing). FAST and REFERENCE currently have the **same**
convolution and tracking arithmetic, by design: a speed preset must not
remove hardware tracking. SIMD or other optimizations should be introduced
only with a moving-source output-parity test.
The older 48-tap mode performs 96 direct HRTF MACs/sample. SIMD and benchmark
work are appropriate only after verifying that each mode preserves sound.

Do not substitute a made-up bit-exact mode if it performs poorly. First implement
and validate one fixed-point/HW-arithmetic path against recorded AU8830 digital
output, then expose it as a separate, explicitly expensive research option.

### Audio QA needed before release

On the Windows FX-6300 (and Linux/Wine), test at least Alice 2000 tower2/hedge2,
Alice 2011 dialogue plus provider round trips, and Quake III 1.17 dense battle
sounds at `legacy` and `reference`, and verify `fast` matches `reference`
acoustically. Record dropouts, clipping and CPU load,
compare all with `legacy`, and confirm `A3D.Mixer.waveOut.queue_empty_events=0`
where possible. In-game listening and timing are not replaceable by an offline
impulse test.

**Redistribution:** coefficient authorship and public redistribution rights
need to be confirmed with the data contributor before publishing a release
archive containing the table on GitHub. This is not the GPL-2.0 code from the
86Box Vortex reference emulator; this implementation is an independent one.
