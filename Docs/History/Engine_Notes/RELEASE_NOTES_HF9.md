# Hotfix 9 - Acoustic geometry retrace pacing

- Based on Hotfix 7 (not Hotfix 8), no experimental tail voices.
- Quake III acoustic geometry may have ~2048 triangles; each Flush used to
  force a new trace for all active voices on the next block.
- Added configurable geometry cache age / complete geometry bypass,
  without affecting measured HRTF convolution.
- Added shutdown counters for trace calls, cache hits, deferred revisions,
  and bypassed geometry work.
- Native geometry cache regression and full offline build/test.
- This is an experimental performance fix; Wine gameplay not yet validated.
