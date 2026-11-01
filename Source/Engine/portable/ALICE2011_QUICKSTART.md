# Alice 2011 remaster / VorpalFix 4.2.1 — v0.6.0 FINAL (experimental)

Use an unmodified `alice.exe` with SHA-256 `08bcbe4b549633b24c90a1ab36bf516bd8873432c68b37248c98ee4225506e50`. The target directory must already contain VorpalFix `winmm.dll`, `VorpalFix.ini`, `SndDrivers/mss32.dll`, and `SndDrivers/mssa3d2.m3d`; they are not redistributed or modified.

After registering `alice2011` using `--profile alice2011` and installing from the final portable ZIP:

```bash
bash ./run_alice2011_wine.sh "/path/to/Alice2011/bin/alice.exe" +set s_milesdriver a3d2
```

The checked bridge makes a RAM-only provider-selector change. The launcher retains Wine's existing prefix and adds a native-first `winmm=n,b` override so the game's own VorpalFix `winmm.dll` can load. **Offline builds and selector checks are not evidence of working remaster gameplay**; real Wine test still required. Do not replace VorpalFix's winmm.dll with another copy.
