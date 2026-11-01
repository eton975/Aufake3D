# Half-Life progress snapshot verification

Version 0.7.0-alpha. Windows x86-64 host, llvm-mingw 20261020 Clang/LLD, rebuilt freestanding PE32 x86 components.

* Combined regression suite: 171 tests; 170 passed, one explicitly skipped because SciPy is unavailable (synthetic weapon-forensics resampling).
* 18 native Windows API smoke executions passed across five title profiles and Generic-A3D2. Shared DLL identity, all deployed PE32 files and Bash syntax passed.
* New checks cover capability sizes 0–80, unaligned records, guard bytes, NULL/short/oversized records, configured 24-voice limits through actual COM, optional/no launcher logs, preflight failures, recursive generic targets and unknown-layout rejection.
* An independently assembled synthetic x86 child with the recognizer's matching landmarks passed the actual Windows memory read/protect/write/restore/flush compatibility path, child manifest activation and exit forwarding. The synthetic executable stayed unchanged on disk. This is not Half-Life game code or gameplay.
* Existing synthetic clients passed the Half-Life Init 0x7f/PCM and Galaxy IA3d4 startup subsets, shared IUnknown/control prefixes, bounded capabilities and deliberate IA3d5 refusal. Native fixed/generic launcher tests cover quoted arguments, inheritance, child status, invalid/missing manifests, architecture and argument length.
* The recognizer compiled from this release matched the supplied hl.exe read-only. All four original supplied file hashes match the earlier inventory. HALFLIFE_BINARY_REPORT.json records evidence; no originals were edited.
* User confirms direct original Half-Life startup works normally. The isolated trace found error 5 on the obsolete Aureal HKLM splash setting. A private debugger skip reached successful launcher/window setup and stayed alive through the observation interval, but desktop capture/control failed. No usable menu, game audio, map gameplay or listening pass is claimed. The final production workaround was not successfully exercised in the real game.
* DSP sources and HRTF data remain identical to the preceding alpha (DSP_SOURCE_IDENTITY.json). The previous alpha's 18 native DSP programs passed; the historical DSP log is included and clearly labelled. These unchanged checks were not repeated.
* Shell syntax and fake-Wine argument/environment checks passed. No actual Wine runtime smoke or Linux gameplay was verified.

The core build retains five existing unused-helper warnings. No sanitizer or warning-free build is claimed. validation contains the current build/regression/runtime/input reports; unchanged-dsp-previous-alpha.log is historical evidence only.

Packaging verifies CRC, exact ZIP member sets, file sizes and embedded SHA-256 manifests. Separate ZIP checksums and an archive verification JSON accompany the downloads. Game binaries/assets, vendor runtime DLLs, private debugger helpers and disassembly are excluded. Historical documentation/results elsewhere in the source are not current game validation.
