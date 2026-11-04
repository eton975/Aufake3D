# Aufake3D v0.8.15 — One-click build and contributor workflow

**Release type:** source and build-infrastructure update of the v0.8.14-RC1
one-click snapshot. **Not** a new gameplay-validated or malware-cleared binary
release. Windows 10/11 native builds remain to be accepted independently.

## Changes

- Stable `BUILD_WINDOWS.cmd` / `BUILD_LINUX.sh` entry points and common
  `scripts/build.py` pipeline, inherited from the previous one-click snapshot.
- Local packaging for four existing game kits from source-owned templates,
  without acquiring a historical binary release.
- Native Windows CRT/Miles mock compiler discovery for **both headers and
  libraries**, with explicit diagnostics in ordinary PowerShell sessions.
- Strict frozen binary reproducibility is opt-in; COM export/ABI validation
  remains mandatory for the locally rebuilt Miles proxy.
- Active version identifiers, build ZIP filenames, installer receipts and CI
  artifact paths updated coherently to **v0.8.15**.
- New `Tools/audit_source_checkout.py` to detect missing, unexpected and
  locally modified source files before they are committed.

## Source provenance and limitations

The v0.8.15 source archive merges the uploaded GitHub source ZIP
`Aufake3D-0d747972f9ffddab9d0be624059ecbf1d7ec05d0.zip` (commit `0d74797`)
with the v0.8.14-RC1 one-click build source. The uploaded commit includes the
Miles proxy development hash-warning fix and the previously edited GitHub
Actions workflow. No source path from that uploaded GitHub snapshot was
dropped in the merge. **Uncommitted Windows changes and GitHub commits newer
than `0d74797` are not available in that ZIP and are not claimed included.** This is a source-only archive; no compiled PE files,
original Miles vendor DLLs or proprietary game data are included.

No changes were made to the A3D C audio-processing engine, COM implementation,
HRTF/geometry algorithms or the 331-export Miles proxy C implementation in
this version-only bump. Byte-for-byte binary identity depends on the toolchain;
no new Windows gameplay regression testing has been performed.

Previous notes: [v0.8.14-RC1](RELEASE_NOTES_V0814_RC1.md). Historical
VirusTotal and licensing findings are in `Docs/` and should not be silently
reinterpreted as clearances for locally rebuilt binaries.

## Verification for prospective commit

```
python scripts/build.py --doctor
python Tools/audit_source_checkout.py
python -m unittest discover -s tests -v
```

Then run `BUILD_WINDOWS.cmd` on Windows or `./BUILD_LINUX.sh` on Linux.
Review `git diff --stat` and `git diff --cached --check` before committing.
