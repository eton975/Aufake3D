# v0.4.6 build verification
- PE32 i386 DLL cross-built with clang/lld-link on Linux.
- 45 Python contract tests passing.
- Native master-gain test passing: 1.0x, 1.5x, 2.5x values produce ordered gain for unclipped source.
- Limiter stress test passing; limiter may cancel requested gain when saturated.
- No in-game Wine runtime test performed; gather real game logs and compare 0.2 vs 3.0 settings.
