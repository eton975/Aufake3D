# Wine 11.19: next step

The first real COM test failed with HRESULT `0x80040154` (class not registered); the COM factory was never reached. The previous 32-bit HKCU entry was not visible through Wine's 32-bit HKCR view.

Run from the **v0.1.5** extracted directory:

```bash
bash tools/wine_com_probe.sh
```

The script copies the updated test binaries, invokes the 32-bit registry helper inside the same isolated prefix, runs `CoCreateInstance`, and packages diagnostics to `~/alice-a3d2-com-results-v015.tar.gz`. It never accesses PCI or ALSA. Do **not** run Alice until this COM test succeeds.

A success here demonstrates only COM activation, not A3D 2.0 rendering. When COM activation works, the next step is tracing the Miles `mssa3d2.m3d` provider with `Alice.exe`.
