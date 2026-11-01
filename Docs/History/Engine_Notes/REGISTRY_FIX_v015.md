# v0.1.5 Wine COM registration diagnostic

The uploaded v0.1.4 results show **REGDB_E_CLASSNOTREG (0x80040154)**. The 32-bit HKCU\Software\Classes key was present, but the 32-bit merged HKCR lookup did not find it. No evidence of a DLL ABI or hardware failure yet.

The new `a3d-register32.exe` is a 32-bit native Windows program to ensure we register in the same bitness/view as the 32-bit COM test. It attempts per-machine HKLM\Software\Classes registration in this **isolated Wine prefix only**; if HKCR is still missing, it tries a direct HKCR registration. It prints readback results before and after.

## Run

Extract the v0.1.5 archive, `cd` into its root, then run:

```bash
bash tools/wine_com_probe.sh
```

The earlier `tools/wine_probe.sh` is only necessary when the isolated prefix does not exist. Upload `~/alice-a3d2-com-results-v015.tar.gz` whether the test passes or fails.

No physical AU8830 card, PCI access, Windows 9x drivers, or Linux driver reload is involved.

## Status

Build verified locally with Clang/LLD and PE32 checks; Wine execution awaits user-run. COM success alone is *not* A3D 2.0 rendering or a working Alice game.
