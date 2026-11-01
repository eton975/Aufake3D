# GitHub source integration audit — Aufake3D v0.8.15

**Authoritative uploaded GitHub snapshot:** `0d74797` (full archive filename
`Aufake3D-0d747972f9ffddab9d0be624059ecbf1d7ec05d0.zip`).
**Additional source snapshot:** `Aufake3D_v0.8.14-RC1_OneClick_Windows_Linux_Source.zip`.

The uploaded GitHub ZIP contained **449 files**. Every one of those relative
source paths is present in the new v0.8.15 source tree. The older one-click
snapshot added 29 paths, including `BUILD_WINDOWS.cmd`, `BUILD_LINUX.sh`,
`scripts/build.py`, `scripts/host_toolchain.py`, `tests/test_one_click_build.py`,
and source-owned templates for all four game kits. The two input trees had
11 overlapping paths with different contents; those differences were reviewed
before merging, including `.github/workflows/source-ci.yml` and the Miles
export-map build script.

The GitHub script's **opt-in frozen hash check** and mandatory Miles export
verification are retained. The build-system version adds safe repeat-build
handling and stronger reporting for a proxy built with a different toolchain.
The build toolchain also auto-discovers Microsoft CRT headers (`stdio.h`)
and import libraries (`msvcrt.lib`, `oldnames.lib`) on Windows.
The new CI builds on Windows and Linux; unlike the earlier CI, it runs the
single local-equivalent build driver and uploads the generated runtime ZIP.

The active release version is v0.8.15, including game installer receipts,
build filenames and source metadata. Earlier v0.8.14-RC1 security reports,
old engine history and frozen binary hash references remain historical facts
and are not relabelled as new v0.8.15 evidence.

## What this comparison cannot prove

A GitHub auto-generated archive includes only the **committed tree**. Files
edited locally on Windows but never committed or pushed cannot be recovered
from this archive. Similarly, an additional GitHub commit after `0d74797`
needs explicit reconciliation before applying the supplied patch. Please
check `git log -1 --oneline` in the destination checkout before application.

**There are no changes to the C audio mixing, WaveOut, geometry or HRTF
implementation in this merge.** The Windows one-click script still needs
native Windows acceptance testing; the available Linux cross-build confirms
the PE32 build and package contents, not end-to-end Windows gameplay.

For an exact source snapshot check, run:

```text
python Tools/audit_source_checkout.py
python Tools/verify_source_manifest.py
python -m unittest discover -s tests -v
```

After source files are intentionally edited for development, the historical
snapshot verifier may fail until a future release snapshot is explicitly
updated. This is expected and distinct from the everyday build pipeline.
