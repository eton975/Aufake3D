# Change summary — v0.7.1-dev

- Added 32-bit, read-only native ABI-survey executable for A3D1 export presence,
  A3D2 COM QI and A3D3 extension query results.
- Added a new PE32 generic direct-launch executable and made it the default
  candidate test path; the memory-activating bridge remains explicitly opt-in.
  Also added raw-EXE direct-start experiment for controlled comparisons. It does not bypass anti-cheat or AV.
- Improved static candidate scan classification and Miles .m3d module evidence.
- Stager now includes the ABI survey and scoped report, leaving the game untouched.
- Existing DSP DLLs, HRTF algorithms, gains, low-latency queues and Alice clarity
  unchanged; the generic executable launcher is rebuilt, title profiles untouched.
- Compilation and Python regression tests pass; **real new-game playback unverified**.
