# Aufake3D v0.9.2a-HRTF-hotfix — reference-default launchers

**Status:** configuration-only source hotfix candidate; not yet released/cross-platform certified.
**Base:** public [v0.9.2](https://github.com/eton975/Aufake3D/releases/tag/v0.9.2),
Git commit `4eeb00fc5443e2e8d0f2664df08d6f36a01f3b28`.

## Changes

- Ten active launchers change `A3D_HRTF_MODE=fast` to `A3D_HRTF_MODE=reference`.
- Six active launchers already defaulted to `reference` and are unchanged.
- All 16 launchers preserve explicit user HRTF overrides.
- HRTF mode documentation is corrected to reflect the new default.
- No changes to DLLs, audio DSP, Vortex2 coefficients, geometry, COM interfaces, WaveOut, game executables, or gameplay assets.
- Descent 3 retail's separate ZIP has no game launcher and therefore is unaffected.

**Important:** In public v0.9.2 `fast` and `reference` follow the same corrected 56-tap HRTF/ITD DSP processing and are designed to produce identical PCM. Switching the launch default is a valid consistency change, **not** an independently demonstrated fix for subjective 3D quality. Test against `legacy` if the issue persists.

## Apply to source checkout

Run `python3 APPLY_HRTF_HOTFIX.py --root /path/to/Aufake3D_master --apply` from the unpacked source-changes archive; the tool verifies the original scripts against the published v0.9.2 Git blob hashes before changing them. Dry-run is the default. It also installs `scripts/package_hrtf_hotfix.py`, a test, and this document; no engines are altered. Use a clean copy based on the tag for reproducible results.

For direct Git application, `git apply Aufake3D_v0.9.2a-HRTF-hotfix_Source.patch` performs the corresponding changes.

## Package a runtime from official v0.9.2 release ZIP (no recompilation)

Download the actual v0.9.2 published **runtime ZIP**, whose SHA-256 is
`6952672bfbd60130bf2d8bb16a445f35707458bd817d0907e0853e033c8d28ad`. Then run:

```bash
python3 scripts/package_hrtf_hotfix.py --input /path/to/Aufake3D_v0.9.2_Local_Runtime.zip
```

This creates `Aufake3D_v0.9.2a-HRTF-hotfix_Local_Runtime.zip` with updated SHA-256 manifest, uniform ZIP metadata and **unchanged DLL bytes**. The script refuses an unexpected input checksum.

## Build from patched source

Run `./BUILD_LINUX.sh` on Debian or `BUILD_WINDOWS.cmd` on Windows, then:

```bash
python3 scripts/package_hrtf_hotfix.py --input dist/Aufake3D_v0.9.2_Local_Runtime.zip --from-built
```

This source rebuild requires pinned toolchain inputs, passing tests and local reproducibility. The unchanged `scripts/build.py` retains its base v0.9.2 runtime filename; the separate hotfix repacker issues the distinctly versioned ZIP. The new test verifies every Windows/Wine launcher defaults to reference.

## Release verification

Check the original base ZIP SHA; verify all 16 launcher defaults, manifest entries, and that all non-launcher binaries match the official base. Run the existing local tests, repeat on Windows and Debian, and run the five-platform reproducibility CI matrix before claiming release certification. The `v0.9.2a-HRTF-hotfix` GitHub tag/release should be created against the exact hotfix source commit, **not** a mutable `main` branch.

No separate Descent 3 retail patch is necessary for this change because it has no launcher.
