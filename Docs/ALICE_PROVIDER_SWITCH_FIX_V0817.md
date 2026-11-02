# Alice 2000 / 2011: bidirectional A3D2 and Miles 2D switching (candidate)

## Observed failure

With the old `RUN_AUFAKE3D_WINDOWS.cmd` launcher, a forced `+set s_milesdriver a3d2` overrides Alice's saved audio choice on launch. Removing this override without updating the Alice 2011 Miles proxy configuration causes `Could not find 3D provider a3d2`: the proxy has a strict `A3D_MILES_REQUIRE_CLI_A3D2=1` gate that checks only the process's startup command line, not subsequent menu selections.

## Candidate correction

- Neither Alice launcher injects `+set s_milesdriver a3d2` anymore. The game receives the real user configuration, and callers can still provide explicit command-line arguments with `%*` or `"$@"`.
- The Alice 2011 launcher retains `A3D_MILES_ALIAS_UNKNOWN=1` while setting `A3D_MILES_REQUIRE_CLI_A3D2=0`. Its real A3D2 provider can then be enumerated using the established `unknown` compatibility alias even without a startup `+set`. Provider handles are not substituted; Miles/Dolby still open their genuine drivers.
- Alice 2000 continues to use its RAM-only selector bridge; the bridge already checks the selected `a3d2` token dynamically.
- No DSP/COM/WaveOut source is modified. No game executable is modified on disk.

## Limitations and acceptance

The original proxy's `unknown` alias is necessarily less narrowly scoped when strict command-line gating is disabled. An unrelated unrecognised `s_milesdriver` value could select the real A3D2 provider. Test the game default (`auto`) and the supported selections before shipping a release.

Run `BUILD_WINDOWS.cmd`, deploy the updated Alice game kit, then try `Miles -> A3D2 -> Dolby -> Miles -> A3D2` in-game. Account for Alice's restart-required/latching message. Confirm the *Sound Initialization* console message and a fresh Miles trace for every transition. As of preparing this patch, the corrected Windows launcher has not been exercised in the retail games; native mock and source tests are not gameplay validation.
