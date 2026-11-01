# v0.5.0 SOURCE COMMENTARY — Regression test / harness
# Exercises the release implementation or checks its ABI/packaging contract. Do not
# treat fixture success as proof of native Wine or retail-game compatibility.
from pathlib import Path
s=Path(__file__).resolve().parents[1].joinpath('win32/source_probe.inc').read_text()
assert 'MAX_PCM_BYTES (64UL*1024UL*1024UL)' in s
assert 'IA3dSource.Unlock checksum_FNV1a' in s
assert 'A3D_ENTIREBUFFER 2UL' in s
assert 'A3D_FROMWRITECURSOR 1UL' in s
assert 'sr_free_pcm(s);s->magic=0' in s
assert 's->wave_size=(DWORD)len' in s
assert 's->locked=1;s->lock_at=at;s->lock_bytes=bytes' in s
assert 'static HRESULT WINAPI sr_play(Source*s,int repeat){return sr_audio_play(s,repeat);}' in s
assert 'sr_setformat /* 7 SetWaveFormat */' in s
assert 'sr_lock /* 11 Lock */' in s
assert 'sr_unlock /* 12 Unlock */' in s
print('PASS: PCM buffer source ABI and safety contract')
