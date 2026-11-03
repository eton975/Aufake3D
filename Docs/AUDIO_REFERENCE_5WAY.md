# Aufake3D v0.9.2: independent Alice five-way audio reference target

This is a **parallel, source-only toolchain**, not part of the runtime DLL
build. It packages console `.cfg` files, a configurable Python WAV analyzer,
regression tests, and instructions for recording the original Vortex 2.

## Targets: choose one; the main audio runtime build is untouched

| Windows 10/11 | Debian 13 / Linux | Result |
|---|---|---|
| Double-click `BUILD_AUDIO_REFERENCE_WINDOWS.cmd` | `./BUILD_AUDIO_REFERENCE_LINUX.sh` | Deterministic audio-reference kit ZIP only |
| `BUILD_AUDIO_REFERENCE_WINDOWS.cmd --doctor` | `./BUILD_AUDIO_REFERENCE_LINUX.sh --doctor` | Inspect sources, Python and optional analysis dependencies |
| `BUILD_AUDIO_REFERENCE_WINDOWS.cmd --test` | `./BUILD_AUDIO_REFERENCE_LINUX.sh --test` | Run analyzer's independent regression suite |
| `BUILD_AUDIO_REFERENCE_WINDOWS.cmd --verify` | `./BUILD_AUDIO_REFERENCE_LINUX.sh --verify` | Validate package bytes and its SHA-256 manifest |

Run these from the repository root. The underlying target is:

```text
python scripts/build_audio_reference.py
```

Output is `dist/audio-reference/Aufake3D_Alice_Five_Way_Audio_Reference_Kit_v0.9.2.zip`.
A fixed ZIP entry order, stored (not DEFLATE-compressed) contents, fixed
1980 timestamps and permissions, and an internal `SHA256SUMS.txt` allow
reproducible packaging without compiler or zlib dependencies. Three separate
Python build processes must agree byte-for-byte before the ZIP is accepted.
Both the main build and its existing `dist/` outputs remain unaffected.

A **separate GitHub Actions job** is defined in
`.github/workflows/audio-reference-ci.yml`. It does not run the full Win32
build, and it uploads its own package artifact. Installing the Python analysis
libraries is a CI-only step; the plain packaging target needs only Python 3.10+.

## Analyze captures

Install analysis dependencies once:

```text
python -m pip install -r Audio_Reference/requirements.txt
```

Extract the standalone ZIP, put the following files into its `recordings/`
folder, and capture all five as stereo 48 kHz lossless WAV:

| Capture file | Environment / A3D path |
|---|---|
| `alice2000_windows.wav` | Original Alice, Windows 10, Aufake3D |
| `alice2000_wine.wav` | Original Alice, Debian Wine, Aufake3D |
| `alice2011_windows.wav` | Alice remaster / VorpalFix, Windows 10, Aufake3D |
| `alice2011_wine.wav` | Alice remaster / VorpalFix, Debian Wine, Aufake3D |
| `alice2000_vortex2_win98.wav` | Original Alice, Pentium III / Win98SE / actual AU8830 |

Then, **inside the extracted kit**, run:

```text
python tools/analyze_five_way.py profiles/five_way.json --out results --plots
```

For incomplete sets, append `--allow-partial`. The analyzer's comparisons
and alignment are statistical, not proof of sample-equivalent game execution.
The original 2000 and the 2011 rerelease may differ in their audio assets.
The physical AU8830 recording includes analogue conversion, line-input noise,
and recorder clock differences; no unsupported sixth Alice 2011/Win98
configuration is implied.

The `.cfg` demo commands are historically documented for original Alice;
**their functionality on Alice 2011 remains unverified**. See the packaged
`README_FIRST.md` and `CAPTURE_WORKSHEET.md` for detailed capture, installation
and hardware line-in guidance. This distribution contains no `.dm3`, WAV,
commercial game data, original Aureal drivers or Windows 98 executables.

The source is in `Audio_Reference/`; only explicitly enumerated source files
are shipped. Local recordings, `.dm3` demos, hidden git metadata, build outputs,
`__pycache__` and captured reports are excluded. Do not distribute copyrighted
recordings or game data without permission.

## Scope and source control

- Main build entry points (`BUILD_WINDOWS.cmd`, `BUILD_LINUX.sh`) are unchanged.
- New audio-reference entry points do not invoke `scripts/build.py`.
- The main v0.9.2 DLL and reproducibility implementation is unchanged.
- To update a source-release manifest after committing these additional files,
  run `python scripts/update_source_manifest.py` and review the differences.
- CI proves the standalone artifact's same-environment reproducibility; it
  does **not** establish equal PCM under Windows/Wine/real AU8830, or test
  original game behavior.
