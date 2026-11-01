# Historical integration & release automation source

This directory preserves the original v0.8.13 installation utilities, game-kit launch scripts, manifest definitions and regression test **source code** for review. No compiled game helpers, Miles proxies or proprietary game files are present.

**Do not run the historical installers from this source-only distribution.** Their original game kits depended on compiled DLLs, standalone executables and the pinned Miles proxy, all deliberately withheld from the public source ZIP for the security investigation. The historical installer/rollback tests require the complete old distribution and are not part of the default GitHub source CI. The source repository's supported instructions are in the root `README.md` and `BUILDING.md`; build only the independent A3D core in the default workflow.

These files allow contributors to review and revise the installation system once individual executable provenance and redistribution issues are resolved.
