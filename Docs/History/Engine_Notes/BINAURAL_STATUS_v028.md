# v0.2.8: first analytical binaural cue prototype

This **experimental** renderer is not a reconstruction of original Aureal HRTF coefficients.
It produces different per-ear PCM signals using actual interaural time differences
(up to ~650 microseconds), distance/azimuth-dependent interaural level differences,
far-ear lowpass filtering, and modest rear/elevation coloration.

Key limitations (remaining): No measured SOFA/MHR or original Aureal HRTF filters;
rear and elevation cues are crude; no head-size calibration; no true 3D source
streaming or continuous movement; no resampling, robust looping or callback/event
delivery; no geometry-aware Wavetracing; each Play uses its own one-shot waveOut
buffer and handle, not a production shared mixer. Not yet playable in Alice.

Miles-driven left/centre/right playback through Wine was independently verified by
user listening in v0.2.7. The new v0.2.8 audio renderer has only compiled/native
test coverage until tested on Wine/Windows.

To compare recorded PCM with known expected behaviour without a listening test:
`tools/test_binaural_native.c` asserts ITD sample peak ordering, left/right gains,
rear high-frequency damping, elevation spectral changes and right/left-handed coordinates.
