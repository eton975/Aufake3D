# v0.6.0 release notes — consolidated

Build lineage: Hotfix 10 (based on Hotfix 9 / Hotfix 7, **not** experimental Hotfix 8). Consolidation changes scripts/docs and delivery only. Audio DLL byte-for-byte unchanged from Hotfix 10.

**Retained fixes:** valid Quake III null secondary PCM Lock pointers; WaveOut bounded queue and event scheduling; measured MIT KEMAR HRTF / Fast24 onset window; 128 voices and low-overhead diagnostics; idle Stop fast path; active Play continuity; geometry-cache retrace interval; documented Aureal IA3dList::Call / End polygon-count API semantics (Quake III 0xABABABAB crash prevention).

**User-confirmed Quake III 1.17:** Demo 1 completes; geometry retrace every four DSP blocks and 0.14 late reverb yield strong subjective spatial audio. Quake III preset applies these when launched with `run_quake3_117_wine.sh`.

**Alice 2000:** proven classic bridge included and tested offline, but latest DLL not revalidated end-to-end. **Alice 2011 + VorpalFix 4.2.1:** exact-hash bridge included and offline tested; gameplay unverified. No retroactive claims of full runtime testing. Experimental A3D 1.x and A3D 3.0 remain outside full parity.
