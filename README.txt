Aufake3D v0.9.2a-HRTF-hotfix - Source hotfix kit

BASE Git tag: v0.9.2, commit 4eeb00fc5443e2e8d0f2664df08d6f36a01f3b28.
Ten active game launchers change FAST defaults to REFERENCE (Windows and Wine).
Other six were already REFERENCE. Explicit overrides remain supported.
DLLs and audio engine are unchanged; this does not prove better 3D perception.

Dry-run:
  python3 APPLY_HRTF_HOTFIX.py --root "$HOME/Downloads/Aufake3D_master"
Apply:
  python3 APPLY_HRTF_HOTFIX.py --root "$HOME/Downloads/Aufake3D_master" --apply
Or from checkout root: git apply /path/to/Aufake3D_v0.9.2a-HRTF-hotfix_Source.patch
Then run tests, full pinned build, and package hotfix runtime:
  python3 scripts/package_hrtf_hotfix.py --input dist/Aufake3D_v0.9.2_Local_Runtime.zip --from-built

See Docs/HRTF_REFERENCE_DEFAULT_HOTFIX.md for details.

Known v0.9.2 baseline issue: two old pinned-reference regression tests may fail.
If so, apply the INCLUDED separate test-only fix:
  python3 SUPPORT_ONLY_Pinned_Test_Compatibility_Fix.py --root "$HOME/Downloads/Aufake3D_master" --apply
This support utility only updates tests/test_pinned_local_build.py and is not
a prerequisite for testing the HRTF launcher defaults.
