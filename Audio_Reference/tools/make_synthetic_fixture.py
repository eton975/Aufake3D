#!/usr/bin/env python3
"""Generate FAKE stereo WAV inputs for validating the five-way analysis tool.

The generated sounds are mathematical test signals, NOT recorded Alice or Vortex 2.
"""
import argparse
import json
from pathlib import Path


def main():
    import numpy as np
    from scipy.io import wavfile
    from scipy.signal import lfilter

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', default='synthetic_five_way', type=Path)
    parser.add_argument('--seconds', default=20, type=float)
    args = parser.parse_args()
    if args.seconds < 10:
        parser.error('--seconds must be at least 10')
    args.out.mkdir(parents=True, exist_ok=True)
    fs = 48000
    n = int(fs * args.seconds)
    rng = np.random.default_rng(20261103)

    def source(seed):
        t = np.arange(n, dtype=np.float64) / fs
        # Slow directional motion, repeated onsets, and short silences.
        env = np.zeros(n, dtype=np.float64)
        for i, onset in enumerate(np.arange(0.7, args.seconds-1, 2.4)):
            start = int(onset * fs)
            duration = min(int((.75 + .15*(i%3))*fs), n-start)
            q = np.linspace(0, 1, duration, endpoint=False)
            env[start:start+duration] += (np.sin(np.pi*q)**2)
        noise = rng.standard_normal(n)
        audio = env * (.16*np.sin(2*np.pi*(330+seed*77)*t)
                      + .08*np.sin(2*np.pi*(880+seed*110)*t)
                      + .055*noise)
        pan = .3*np.sin(2*np.pi*.13*t)
        l = audio*(1-pan)
        r = audio*(1+pan)
        # Use a small nonidentical interchannel delay to provide side energy.
        delay = 14
        return np.column_stack((l, np.roll(r,delay))).astype(np.float32)

    def transform(x, side_scale=1, quiet=1, analog=False):
        mid = .5*(x[:,0]+x[:,1]); side = .5*(x[:,0]-x[:,1]) * side_scale
        y = np.column_stack(((mid+side)*quiet, (mid-side)*quiet)).astype(np.float32)
        if analog:
            y = lfilter([.78], [1,-.22], y, axis=0).astype(np.float32)
            y += rng.standard_normal(y.shape).astype(np.float32)*.00008
        return np.clip(y, -.98, .98)

    def prefix(x, start):
        pad = np.zeros((int(fs*start),2), dtype=np.float32)
        return np.concatenate((pad,x))

    src2000 = source(0)
    src2011 = source(1)
    signals = {
        'alice2000_windows': prefix(transform(src2000,1.00),1.8),
        'alice2000_wine': prefix(transform(src2000,.73),3.15),
        'alice2000_vortex2_win98': prefix(transform(src2000,1.15,.85,True),.8),
        'alice2011_windows': prefix(transform(src2011,1.0),2.1),
        'alice2011_wine': prefix(transform(src2011,.82),3.4),
    }
    names = [
        ('alice2000_windows','Synthetic 2000 / Windows','alice2000','a'*64),
        ('alice2000_wine','Synthetic 2000 / Wine','alice2000','a'*64),
        ('alice2011_windows','Synthetic 2011 / Windows','alice2011','b'*64),
        ('alice2011_wine','Synthetic 2011 / Wine','alice2011','b'*64),
        ('alice2000_vortex2_win98','Synthetic hardware-like / Win98','alice2000','a'*64),
    ]
    captures = []
    for cid, label, _group, sha in names:
        wavfile.write(str(args.out/f'{cid}.wav'), fs, (signals[cid]*32767).astype(np.int16))
        captures.append({'id':cid,'label':label,'file':f'{cid}.wav',
                         'demo_sha256':sha,'start_seconds':None,
                         'notes':'Synthetic test only, NOT real game audio'})
    profile = {'schema_version':1,'analysis':{'max_lag_seconds':6,
                'duration_seconds':min(10, args.seconds-4),'window_seconds':2},
                'captures':captures}
    (args.out/'profile.json').write_text(json.dumps(profile,indent=2)+'\n',encoding='utf-8')
    (args.out/'SYNTHETIC_ONLY.txt').write_text(
        'These are artificial numerical test signals. They are NOT Alice recordings, '
        'NOT authentic A3D 2.0, and NOT genuine Vortex 2 output.\n', encoding='utf-8')
    print(f'Generated FIVE synthetic WAVs and profile.json at {args.out}')

if __name__ == '__main__':
    main()
