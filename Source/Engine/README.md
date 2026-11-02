# Engine source — current guide for v0.9.2

The authoritative source map is [Docs/SOURCE_ARCHITECTURE.md](../../Docs/SOURCE_ARCHITECTURE.md).
Build from the repository root with `python3 scripts/build_engine.py`; do not
compile individual `.inc` units as separate translation units. The current core
is Windows x86 PE32 (also usable under Wine), not a native Linux `.so`.

The previous README and version-specific hotfix notes were moved without
changing their content to `Docs/History/Engine_Notes/`. They describe prior
experiments, **not** current runtime requirements. The `Source/Engine/win32/`
units, `Source/Engine/acoustics/` library, test fixtures and pinned recipe remain
in place. See `Docs/HISTORY_INDEX.md` before following historical instructions.
