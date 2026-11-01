# Contributing to Aufake3D v0.8.16

Start with [Docs/DEVELOPER_INDEX.md](Docs/DEVELOPER_INDEX.md). Before changing
any COM method, PCM ownership or WaveOut worker logic, read the corresponding
contract guide and add a regression test. Preserve 32-bit vtable layout,
DLL exports and thread/lifetime invariants. The v0.8.12 polling behavior is
empirical, not proof of the underlying WinMM cause.

For every PR, include the intended game/API scope, tests, build hashes for
modified core binaries, and clear observations versus hypotheses. Do not
include retail game data, original Miles/Aureal SDK implementation, VorpalFix
binaries, personal debug logs or copyrighted game audio. Mark process-memory
helpers experimental and maintain separate security review.

Before publishing contributions under MIT, verify the ownership and
licensing of the actual code being contributed; preserve independent KEMAR
attribution. See `LICENSE_SCOPE.md` and `THIRD_PARTY_NOTICES.md`.

## Building before opening a pull request

Use `BUILD_WINDOWS.cmd` or `./BUILD_LINUX.sh` and read
[Docs/ONE_CLICK_BUILD.md](Docs/ONE_CLICK_BUILD.md). These are the same
cross-platform build/test/package steps used by CI. New builds are unverified
until tested with games. Do not commit generated `.exe`, `.dll`, `dist/` or
`build/` artifacts. When changing an interface or its implementation, add
an explanatory comment about the invariant *and* a corresponding regression
check; don't pad obvious statements with decorative comments.
