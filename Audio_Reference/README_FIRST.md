# Aufake3D — Alice Five-Way A3D Audio Reference Lab

Kit version: 1.0 (3 November 2026)

## What this compares

| File name (exact) | Game | OS | Audio implementation |
|---|---|---|---|
| `alice2000_windows.wav` | Alice 2000 | Windows 10 | Aufake3D |
| `alice2000_wine.wav` | Alice 2000 | Debian 13 / Wine | Aufake3D |
| `alice2011_windows.wav` | Alice 2011 / VorpalFix 4.2.1 | Windows 10 | Aufake3D |
| `alice2011_wine.wav` | Alice 2011 / VorpalFix 4.2.1 | Debian 13 / Wine | Aufake3D |
| `alice2000_vortex2_win98.wav` | Alice 2000 | Pentium III / Windows 98 SE | **REAL Aureal Vortex 2 (AU8830)** |

The 2000 game has THREE tests: native modern Windows wrapper, Wine wrapper, and a hardware reference on a period machine. The 2011 game has TWO tests: modern Windows and Wine wrappers. TOTAL = FIVE.

**No full game, copyrighted audio, DLLs, hardware drivers, or fake hardware captures are included.**
The Python analysis program runs on Windows 10 or Debian 13, NOT on Windows 98 SE.

## 1 — Install console files

Copy all `.cfg` files in `ALICE_BASE_CFGS` to the *active game's `base` folder* on each test setup. Typical locations:

- Original 2000: `<Alice 2000 game folder>/base/`
- 2011 remaster: `<Alice 2011 game folder>/base/` (often `Alice1/bin/base/`)
- Windows 98: original 2000 game's `base` folder.

Do not replace `config.cfg`, your actual `a3d.dll`, `a3dapi.dll`, the game executable, or any Miles binaries. On 2011, use your existing working VorpalFix setup.

The `.cfg`s only load maps, request demos, and set an optional 60 FPS cap. The 60 FPS setting may be too high for the Pentium III; don't sacrifice stable playback to enforce it.

## 2 — Record TWO reference demos, not FIVE separate ones

We need one recorded 2000 demo to replay on all THREE original-edition machines and a separate 2011 demo for the TWO remaster machines.

### Alice 2000: record ONCE on a known-good 2000 installation

Open the original game's developer console and enter each command separately:

```text
exec a3d5_setup.cfg
exec a3d5_load_hedge1.cfg
```

After `hedge1` finishes loading:

```text
exec a3d5_record_2000.cfg
```

Close the console. For 30-60 seconds, perform a reproducible sound-rich sequence: stand beside a positional emitter, turn slowly 360 degrees, and walk a short fixed route. Stop recording:

```text
exec a3d5_stop.cfg
```

Confirm the actual demo file exists, normally `base/demos/a3d5_2000.dm3`.
If the `record` command is rejected, see **Demo limitations** below. Do NOT pretend the test is deterministic when recording fails.

Copy this ONE `.dm3` file without changing any bytes to:
- Alice 2000 / Windows 10 / Aufake3D
- Alice 2000 / Debian Wine / Aufake3D
- Alice 2000 / Pentium III Windows 98 SE / real Vortex 2

Match the original Alice patch/game assets where possible. Different 2000 executable/demo protocol versions can cause replay to fail.

### Alice 2011: record ONCE on a known-good 2011 installation

Open the restored developer console supplied by VorpalFix; use the same map:

```text
exec a3d5_setup.cfg
exec a3d5_load_hedge1.cfg
```

After loading:

```text
exec a3d5_record_2011.cfg
```

Stop after 30-60 seconds with:

```text
exec a3d5_stop.cfg
```

Confirm that `base/demos/a3d5_2011.dm3` was REALLY created. Copy that one exact file to both 2011 installations (Windows and Wine). **Demo recording and playback on the 2011 remaster are not independently verified.**

If the original 2000 `.dm3` *also* happens to play correctly in 2011, you may choose to reuse it; first verify map, movements, sound events, and timings. Cross-version `.dm3` compatibility has NOT been established by this kit.

## 3 — Play back and record

For the three **original 2000** configurations, first load a different staging level:

```text
exec a3d5_stage.cfg
```

Once `gvillage` loads, start Audacity recording, and then run:

```text
exec a3d5_play_2000.cfg
```

For the two **2011** configurations, use the same staging step, then:

```text
exec a3d5_play_2011.cfg
```

Keep your hands off the controls during playback. Allow the demo to complete. **Verify in each recording that the exact expected sound events are played**, not just the camera positions.

Audacity capture targets:
- 48000 Hz, stereo, lossless unprocessed WAV; 16-bit or 24-bit PCM or float is accepted.
- Windows 10: Stereo Mix input, if working, or another capture with a continuously advancing timeline.
- Debian 13: correct playback-device monitor in PipeWire/PulseAudio.
- Turn OFF automatic gain, normalization, stereo widening, noise reduction, silence trimming, OS Spatial Sound, and unnecessary enhancements.
- Do not export MP3/OGG or edit out silence. Do not independently normalize recordings before analysis.
- Use the same headphone/speaker mode, mixer levels, emulator DLLs, Audio Provider, VorpalFix version/settings, and game/demo assets within each same-edition group.

For software configurations, start with your known-working `A3D_HRTF_MODE=reference`, `A3D_MASTER_GAIN=5.0`, `A3D_WAVEOUT_POSITION_INTERVAL=4`, and on Alice 2011 `A3D_MILES_MODE=activate`. *Ensure these environment variables actually reach the game process*; don't overwrite known-working settings. Keep playback system volume conservatively low (gain 5.0 can be loud).

## 4 — Real Vortex 2 on the Pentium III / Windows 98 SE

**This is the 5th configuration, not an emulator.** Install and use your genuine AU8830 card and original functioning Windows 98 SE Aureal driver. Select the game's native A3D 2.0 or equivalent true Aureal 3D sound provider; make sure the hardware control panel is set to ordinary stereo/headphone output as appropriate and actually accelerates A3D. A game merely playing in stereo is not sufficient proof.

For an accurate capture, route the card's **front stereo line-out** into a **stereo line-level input** on a newer recorder or audio interface connected to Windows 10/Debian. Run Audacity on that modern capture computer. The Pentium III does not need Python or Audacity 4.

Important:
- Use **line-level input**, not a high-gain microphone input. Set capture gain to avoid clipping and leave 6-12 dB headroom during loud effects.
- Check LEFT and RIGHT channels are not swapped, accidentally mono, or mixed through effects.
- Use good cables and avoid ground-loop hum if possible. Start with low output volume.
- Don't send the AU8830's 4-channel rear outputs into the stereo capture unless testing surround as a separate experiment.
- If the native driver allows different sample rates, do NOT assume the Vortex hardware is playing internally at exactly 48 kHz. Recording at 48 kHz standardizes the **capture file** but not the period hardware's internal engine.
- Analogue DAC / cable / ADC frequency response, noise, channel balance, phase and latency are part of this measurement. Hardware reference audio is **not expected to be sample-identical** to the wrapper even if DSP logic were perfect.

Use the SAME `a3d5_2000.dm3` copied from the 2000 reference recording. If the demo doesn't play on the Win98 executable, document that and classify the test as an *approximate scene comparison*, not a deterministic same-demo test.

## 5 — Check that each demo copy is identical

On Windows 10 or Debian (including for the file copied back from Windows 98):

```text
python tools/demo_sha256.py path/to/a3d5_2000.dm3
python tools/demo_sha256.py path/to/a3d5_2011.dm3
```

Put the resulting 64-character hex string in `profiles/five_way.json` under `demo_sha256` for EVERY capture using that demo. All THREE 2000 rows should have the SAME hash, and the two 2011 rows should have the SAME hash. The two editions' hashes can differ.

Different demo hashes or an empty hash will be explicitly flagged in analysis. A matching hash proves the bytes match; it does **not** prove identical game simulation, sounds or A3D setup on all platforms.

## 6 — Analyze all five WAV files

Copy the five WAVs into `recordings/` using the EXACT names in the table above. On Windows 10 or Debian 13, from the extracted kit root:

```text
python -m pip install numpy scipy matplotlib
python tools/analyze_five_way.py profiles/five_way.json --out results --plots
```

On Debian 13, system Python may be externally managed; use a virtual environment instead:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install numpy scipy matplotlib
.venv/bin/python tools/analyze_five_way.py profiles/five_way.json --out results --plots
```

If Python reports venv unavailable: `sudo apt install python3-venv` (package management not performed by this kit).

Outputs:
- `results/report.txt` — readable overview of all FIVE captures, A/B differences, cautions
- `results/report.json` — complete machine-readable stats and alignment metadata
- `results/summary.csv` — one row per configuration, with three frequency-band stereo-width metrics
- `results/windows.csv` — time-varying side/mid width and channel correlation
- `results/side_mid_five_way.png`, `results/side_mid_timeline.png` — optional plots

If you only have 2-4 recordings so far, use `--allow-partial` to analyze what exists. If automatic alignment is weak, fill `start_seconds` in the profile for the affected recording(s), corresponding to the same audible event as the group's reference at its `start_seconds`. You can also try `--max-lag 25`, `--no-align`, or set `--duration 30`.

**All five WAVs must have the same 48000 Hz sample rate by default.** If an interface captured another rate, re-export at 48 kHz in Audacity, or explicitly use `--resample`. The tool does not silently resample or silently compare unmatched sample rates.

## 7 — Verify the analyzer without making recordings

```text
python tools/make_synthetic_fixture.py --out synthetic_five_way
python tools/analyze_five_way.py synthetic_five_way/profile.json --out synthetic_results --plots
python -m unittest discover -s tests -v
```

All `synthetic_*` files are **artificial test signals** only; they DO NOT simulate real A3D geometry/HRTF/hardware or prove game compatibility.

## Demo limitations and study design

- The historical `record`, `stoprecord`, `demo`, and `map` console commands exist in original Alice/Quake III-family engines, but **we have NOT executed these `.cfg` files inside Alice 2000, Alice 2011 or Win98**. Check console output and demo playback before spending time capturing.
- The 2011 rerelease carries **higher-quality audio assets**, so unlike-for-like 2000-v-2011 sound clips cannot isolate the HRTF. Compare within the 2000 group and within the 2011 group first.
- A `.dm3` often recreates the player's simulation/events but may not control audio scheduling, voice randomization, Miles buffer behavior, or drivers. It is a **repeatable game-demonstration test**, not necessarily bit-perfect input playback.
- Waveform alignment based on audio energy is approximate and may fail for different effects, reverb, or long recordings with playback-speed drift. Use identical events or manually selected event boundaries.
- The real card should only be evaluated as a meaningful A3D2 reference if native A3D2 was actually selected. Check driver, provider, sample rate, channel configuration, and physical cabling.
- A more negative Side/Mid ratio means less difference-channel energy in that recording, NOT automatically worse 3D audio. Strong hardware HRTF cues can exist with lower overall side energy; reflections and spatial impression are more complicated.
- Cross-edition (2000 versus 2011) five-way summaries are descriptive until the content and events are demonstrably controlled. Primary pairwise comparisons only occur **within an edition**.
- For the most accurate future test: record A3D API calls including source assets, positions, timestamps, geometry, and render direct pre-WaveOut PCM, then compare against the Vortex 2 physical reference. This kit does not perform API trace replay.

No GitHub access, source modifications, build or game executable changes are involved in this kit.
