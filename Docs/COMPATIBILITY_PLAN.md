# Game support and planned coverage — v0.8.16

| Game | Platform | Confidence | Notes |
|---|---|---|---|
| American McGee's Alice (2011 bundle) + VorpalFix 4.2.1 | Windows | **User gameplay-tested** | Clean Cheshire Cat and good overall audio with v0.8.12 RC1 core (same engine source in v0.8.16; new binaries untested); adapter version pinned |
| American McGee's Alice (2000) | Windows/Wine | Experimental | Verify real A3D2 provider/console naming, dialogue, and spatial sound separately |
| Quake III Arena 1.17 | Windows/Wine | Historically tested on earlier builds | Needs v0.8.16 gameplay retest, matching version 1.17 PK3 data |
| Half-Life 1.0.1.1 | Windows/Wine | Experimental | Needs real end-to-end A3D activation / gameplay verification |
| Alice 2011 + VorpalFix 4.2.1 | Wine/Linux | Untested with this release | Win32 x86 DLL override and game-local original vendor files required |
| Unreal (1998), Unreal Tournament (1999) | Windows/Wine | Research targets | Identify actual retail A3D generation and entry points before adding kits |
| Unreal II, Halo: Combat Evolved PC | Windows/Wine | Research targets | Don't assume A3D 3.0 retail support; inspect actual game imports/calls |

**A3D 1.x/2.0 support is incomplete outside the tested paths. A3D 3.0 API conformance is not implemented.** No Linux-native shared object is shipped; Wine runs 32-bit PE DLLs. Quadraphonic support remains a future goal.
