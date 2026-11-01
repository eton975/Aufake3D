# Quake III 1.17: bounded WaveOut queue (experimental Hotfix 3)

Hotfix 2's 12 prepared headers were all eagerly rendered and submitted, so its 512-frame setting allowed **128ms** of queued PCM. Quake III periodically overwrites its circular DMA ring and may not have filled that far ahead. A long output queue can then contain previously silent or stale audio; simply increasing the buffers can make it worse.

Hotfix 3 keeps 12 *prepared* headers but limits those simultaneously submitted to the device. Default settings are 512 frames/header, 3 headers queued, about **32ms** nominal maximum ahead audio. This is a bound on *submitted* audio, not a guarantee of actual Wine/PipeWire latency. The ring may still underrun if DSP/host scheduling falls behind.

Set `A3D_WAVEOUT_QUEUE_HEADERS` to 2..12 to A/B test. The default depends on `A3D_WAVEOUT_SUBBLOCKS`: 1 -> 6 headers; 2 -> 3; 4 -> 2, targeting approximately 32-43ms. `A3D_WAVEOUT_PLAY_CURSOR` remains optional and **disabled by default**; begin with 0, then try 1. Disable `A3D_TRACE_DETAIL` during gameplay.

After the game exits normally, `A3D_PROBE_LOG` logs `A3D.Mixer.waveOut.queue_limit_frames`, `headers_submitted`, `max_queued_headers`, `queue_empty_events`. The last counter counts transitions from non-empty to empty observed by the worker; it isn't a definitive measurement of PipeWire underruns. An increasing value suggests WaveOut needs more scheduling slack; try 4-6 queued headers, but avoid 12 when possible.

Example:

```bash
cd "$HOME/Games/QuakeIII-117-A3D2"
env -u A3D_TRACE_DETAIL A3D_PROBE_LOG="$PWD/a3d-hf3.log" \
  A3D_MASTER_GAIN=0.5 A3D_WAVEOUT_SUBBLOCKS=2 \
  A3D_WAVEOUT_QUEUE_HEADERS=3 A3D_WAVEOUT_PLAY_CURSOR=0 \
  wine ./quake3.exe
```

If still choppy, repeat with `A3D_WAVEOUT_QUEUE_HEADERS=6`, then compare the audio and `queue_empty_events` values. If the two settings are similarly bad, don't keep guessing buffer sizes; we need a real Wine trace and/or a direct capture of Quake III's DMA write/cursor progression.

**Limits:** this is an engineering hypothesis derived from the source, not yet verified by actual Quake III playback. Tests compile DLL and validate queue-capacity logic, but this environment has no Wine runtime. Keep original Hotfix 2 as a rollback option. No source-game EXE is modified; both Alice launchers are retained.
