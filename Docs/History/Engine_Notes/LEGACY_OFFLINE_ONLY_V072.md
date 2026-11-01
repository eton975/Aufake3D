# Separately distributed optional legacy activation bridge

`a3d-launch.exe` is deliberately **excluded from the v0.7.2 Standard Runtime**.
It creates a suspended x86 child and uses remote memory writes and thread-context
modification to activate A3D COM when normal registration-free loading fails.
This technique is not malware by definition, but it has a credible basis for
triggering antivirus heuristics and anti-cheat violations.

Use only for your own offline/local retro-game compatibility testing, or in an
environment with explicit prior permission. Never attempt to evade antivirus or
anti-cheat monitoring; there is **no claim that this executable will be accepted**.
The bridge does not patch the game EXE on disk. It can nonetheless change what
runs in its memory, so it is a materially different trust category from the
Standard Runtime.

This optional archive carries only the legacy launcher, its SHA-256 manifest,
and these instructions; the audio DLLs remain in the Standard Runtime package.
No game executable, WAV, Miles library or other proprietary asset is included.
