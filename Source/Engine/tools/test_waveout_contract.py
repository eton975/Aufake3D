# v0.5.0 SOURCE COMMENTARY — Regression test / harness
# Exercises the release implementation or checks its ABI/packaging contract. Do not
# treat fixture success as proof of native Wine or retail-game compatibility.
from pathlib import Path
r=Path(__file__).resolve().parents[1]
s=(r/'win32/source_probe.inc').read_text()
a=(r/'win32/waveout_renderer.inc').read_text()
m=(r/'win32/playback_demo.c').read_text()
assert 'static HRESULT WINAPI sr_setevent' in s
assert 'event_codes[s->event_count]=event' in s
assert 'return S_OK;' in s.split('static HRESULT WINAPI sr_setevent',1)[1].split('static HRESULT WINAPI sr_clearevents',1)[0]
assert 'E_NOTIMPL' not in s.split('static HRESULT WINAPI sr_setevent',1)[1].split('static HRESULT WINAPI sr_clearevents',1)[0]
assert 'WaveHeader header;' in s
assert 'sr_audio_stop(s)' in s
assert 'waveOutPrepareHeader' in a and 'waveOutWrite' in a and 'waveOutReset' in a
assert '#include "stream_winmm.inc"' in a
stream=(r/'win32/stream_winmm.inc').read_text()
assert 'sr_audio_play' in stream and 'IA3dSource.Play queued on shared realtime mixer' in stream
assert 'mixer_thread_run' in stream and 'a3dmix_render(&mixer' in stream
assert 'NewSource' in m and 'SetWaveFormat' in m and 'LEFT_POSITION' in m and 'RIGHT_POSITION' in m
b=(r/'win32/build/a3dapi.dll').read_bytes()
c=(r/'win32/build/a3d-playback-demo.exe').read_bytes()
assert b[:2]==b'MZ' and c[:2]==b'MZ'
print('PASS: SetWaveEvent ABI + experimental WaveOut playback structure')
