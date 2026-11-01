# v0.4.2 -- Alice/Wine audio-continuity experiment

Designed in response to first real Alice A3D2 provider activation, which reported
choppy/stuttering 3D audio and a nonstandard startup/menu sequence. Audio behaviour
has NOT been retested in-game: the changes below are hypotheses, not confirmed fixes.

- Increased shared waveOut playback queue from 4 x 256 to 16 x 256 frames at
  48 kHz (about 85 ms queued maximum rather than about 21 ms), trading some
  latency for tolerance of Wine scheduling jitter.
- Default HRTF processing shortened to 48 measured HRIR taps; optional
  A3D_HRTF_TAPS=24 for a diagnostic low-cost mode or =96 for original fidelity.
  Measured KEMAR HRIR sample data and directional spatialization are retained.
- Added a per-voice mirrored playback buffer. Game writes stay in the original
  sample buffer; IA3dSource.Unlock publishes the updated range under the
  mixer mutex. IA3dSource.Lock no longer forcibly sets mix.active=0 and thus
  no longer unconditionally inserts audio gaps on streaming updates.
- Position and Lock/Unlock detail tracing is now opt-in via A3D_TRACE_DETAIL=1.
  Provider startup, errors, source creation and Play markers still go to the
  log by default. Detailed tracing increases I/O and may reintroduce stutter.
- Updated the streaming race-protection offline test to expect the mirrored
  playback design rather than the old forced pause approach.
- Included the corrected Wine prefix-initializing run_wine.sh (v0.4.1 hotfix).

Please compare with v0.4.1 using the same in-game audio situation and the base
`Alice-A3D2.exe`, not the experimental `Alice-A3D2-Miles2.exe` gate/selector patch.
Do not assume this DLL fixes missing intros/menus. That may be an independent
configuration, executable, or game/media issue.
