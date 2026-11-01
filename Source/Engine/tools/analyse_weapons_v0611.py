#!/usr/bin/env python3
"""A3D v0.6.11 offline weapon-identification and mixer-context report.

No matching in the game/audio thread: ALL 100 private reference WAVs are read
only at offline analysis.  Uncertain matches remain unknown, not invented.
Requires Python >=3.9, NumPy and SciPy.  No game audio/assets distributed.
"""
from __future__ import annotations
import argparse, csv, io, json, re, struct, wave, zipfile
from pathlib import Path
from collections import Counter
from functools import lru_cache

MAGIC=b'A3DWPC11'
WORDS=10
RECORD_META=struct.Struct('<10I')
HEADER=struct.Struct('<8sII')
BLOCK=1024
HOP=512
TARGET_RATE=11025


def read_capture(filename):
    import numpy as np
    file=Path(filename)
    with file.open('rb') as f:
        blob=f.read(HEADER.size)
        if len(blob)!=HEADER.size:raise ValueError('Truncated weapon-capture header')
        magic,count,stride=HEADER.unpack(blob)
        if magic!=MAGIC:raise ValueError('Not an A3D v0.6.11 capture')
        if count>256 or stride!=16384:raise ValueError('Unsupported capture header or count')
        for _ in range(count):
            meta=f.read(RECORD_META.size)
            if len(meta)!=RECORD_META.size:raise ValueError('Truncated metadata')
            ms,sid,rate,channels,bits,nbytes,gain,priority,sig,original_bytes=RECORD_META.unpack(meta)
            blob=f.read(stride)
            if len(blob)!=stride or nbytes>stride:raise ValueError('Truncated PCM')
            if bits!=16 or channels!=1 or nbytes%2:continue
            pcm=np.frombuffer(blob[:nbytes],dtype='<i2').astype(np.float32)/32768.0
            yield {'ms':ms,'id':sid,'rate':rate,'channels':channels,'bits':bits,
                   'gain':gain/1000.,'priority':priority/1000.,'hash':sig,
                   'original_bytes':original_bytes,'pcm':pcm}
        if f.read(1):raise ValueError('Unexpected extra data: incompatible format')


def read_references(archive):
    import numpy as np
    entries=[]
    with zipfile.ZipFile(archive) as z:
        bad=z.testzip()
        if bad:raise ValueError('Corrupt weapon WAV: '+bad)
        for filename in sorted(x for x in z.namelist() if x.lower().endswith('.wav')):
            with wave.open(io.BytesIO(z.read(filename))) as w:
                n=w.getnframes();rate=w.getframerate()
                if w.getsampwidth()!=2 or w.getnchannels()!=1:
                    continue
                data=np.frombuffer(w.readframes(n),dtype='<i2').astype(np.float32)/32768.
            entries.append({'name':Path(filename).name,'rate':rate,'pcm':data})
    if not entries:raise ValueError('No mono 16-bit WAV references in '+str(archive))
    return entries


def resample(data,source_rate):
    import numpy as np
    from scipy.signal import resample_poly
    from math import gcd
    if source_rate==TARGET_RATE:return data
    if source_rate<6000 or source_rate>192000:raise ValueError('Invalid PCM source rate')
    d=gcd(source_rate,TARGET_RATE)
    return resample_poly(data,TARGET_RATE//d,source_rate//d).astype(np.float32)


def feature_blocks(data):
    import numpy as np
    if len(data)<BLOCK:return np.zeros((0,24),dtype=np.float32)
    idx=np.arange(0,len(data)-BLOCK+1,HOP,dtype=int)
    if len(idx)>50000:idx=idx[:50000]
    window=np.hanning(BLOCK).astype(np.float32)
    blocks=np.stack([data[i:i+BLOCK] for i in idx],axis=0)*window
    mag=np.abs(np.fft.rfft(blocks,axis=1)).astype(np.float32)
    freqs=np.fft.rfftfreq(BLOCK,1/TARGET_RATE)
    bands=np.geomspace(60,5000,25)
    out=np.stack([mag[:,(freqs>=a)&(freqs<b)].mean(axis=1) for a,b in zip(bands[:-1],bands[1:])],axis=1)
    # Log-spectral shape: robust to source gains. Silence excluded.
    out=np.log1p(out)
    norm=np.linalg.norm(out,axis=1)
    ok=norm>0.15
    out[ok]/=norm[ok,None]
    out[~ok]=0
    return out


def prepare_index(refs):
    import numpy as np
    vectors=[];labels=[]
    for j,ref in enumerate(refs):
        ref['resampled']=resample(ref['pcm'],ref['rate'])
        feats=feature_blocks(ref['resampled'])
        if len(feats):vectors.append(feats);labels.extend([j]*len(feats))
    return np.concatenate(vectors,axis=0),np.asarray(labels,dtype=int)


def normalized_correlation(query,reference):
    import numpy as np
    from scipy.signal import fftconvolve
    n=len(query)
    if n>len(reference) or n<256:return 0.0
    x=query.astype(np.float64);x-=x.mean()
    en=np.dot(x,x)
    if en<1e-8:return 0.
    ref=reference.astype(np.float64)
    c=fftconvolve(ref,x[::-1],mode='valid')
    sums=np.r_[0.0,np.cumsum(ref)]
    sq=np.r_[0.0,np.cumsum(ref*ref)]
    v=np.maximum((sq[n:]-sq[:-n])-(sums[n:]-sums[:-n])**2/n,1e-9)
    scores=np.abs(c)/np.sqrt(en*v)
    return float(min(1.,np.max(scores)))


def rank_sound(record,refs,index,labels,max_candidates=5):
    import numpy as np
    if record['rate']<6000 or record['rate']>192000:return ('unknown',0.,0.)
    data=resample(record['pcm'],record['rate'])
    if len(data)<1024 or float(np.std(data))<0.0002:return ('unknown',0.,0.)
    features=feature_blocks(data)
    if len(features)==0:return ('unknown',0.,0.)
    # Library-scale coarse search, ALL 100 references; no in-game DSP work.
    cosines=features@index.T
    # Sort max similarity for each reference, NOT an ungrounded ID guess.
    coarse=np.zeros(len(refs),dtype=np.float32)
    for j in range(len(refs)):
        mask=labels==j
        if np.any(mask):coarse[j]=float(np.max(cosines[:,mask]))
    shortlist=np.argsort(coarse)[-max_candidates:][::-1]
    # Validate by time-domain normalized matched-filter correlation.
    # Volume changes, sign inversion, and buffer offset do not prevent matching.
    score=0.;best=None
    segment=2048 if len(data)>=2048 else len(data)
    positions=list(dict.fromkeys([0,max(0,(len(data)-segment)//2),max(0,len(data)-segment)]))
    for j in shortlist:
        ref=refs[int(j)]['resampled']
        for k in positions:
            part=data[k:k+segment]
            corr=normalized_correlation(part,ref)
            if corr>score:score=corr;best=int(j)
    if best is None or score<0.65:return ('unknown',score,float(np.max(coarse)))
    # Medium-confidence matches must be reviewed, not treated as proof.
    return (refs[best]['name'],score,float(coarse[best]))


def read_meters(logfile):
    if not logfile:return []
    events=[]
    # Same hex event format as v0.6.10, one observation every ~500ms.
    pattern=re.compile(r'^A3D\.Staff\.E ((?:[0-9a-fA-F]{8} ?){9})$',re.M)
    for m in pattern.finditer(Path(logfile).read_text(errors='replace')):
        values=[int(x,16) for x in m.group(1).split()]
        if len(values)==9 and values[1]==7:
            events.append({'ms':values[0],'voices':values[6],'limiter':values[7]/1000.})
    return events


def nearest_meter(t,meters):
    if not meters:return (None,None)
    delta=lambda x:abs(((x['ms']-t+2**31)%(2**32))-2**31)
    nearest=min(meters,key=delta)
    return (nearest['voices'],nearest['limiter']) if delta(nearest)<=1000 else (None,None)


def analyse(capture,archive,log=None,out=None,quiet=False):
    import numpy as np
    refs=read_references(archive)
    index,labels=prepare_index(refs)
    records=list(read_capture(capture))
    meters=read_meters(log)
    results=[]
    for i,x in enumerate(records):
        name,score,coarse=rank_sound(x,refs,index,labels)
        voices,lim=nearest_meter(x['ms'],meters)
        rms=20*np.log10(max(1e-10,float(np.sqrt(np.mean(x['pcm']*x['pcm']))))) if len(x['pcm']) else -200
        results.append({'record':i,'tick_ms':x['ms'],'source_id':x['id'],
         'sound':name,'match_score':round(score,4),
         'confidence':('high' if score>=0.85 else 'medium' if score>=0.65 else 'unknown'),
         'source_rms_dbfs':round(float(rms),2),'source_gain':x['gain'],
         'priority':x['priority'],'voices_nearby':voices,'limiter_nearby':lim,
         'source_pcm_bytes':x['original_bytes'],'source_rate':x['rate'],
         'hash':f"{x['hash']:08x}"})
        if not quiet and (name!='unknown' or i%32==0):
            print(f"{i+1:3}/{len(records)} source={x['id']} {name:26} "+
                  f"similarity={score:.3f} voices={voices} limiter={lim}")
    if out:
        with open(out,'w',newline='',encoding='utf8') as f:
            w=csv.DictWriter(f,fieldnames=results[0].keys() if results else [
               'record','tick_ms','source_id','sound','match_score','confidence'])
            w.writeheader();w.writerows(results)
    known=[r for r in results if r['sound']!='unknown']
    print(f'Automatic weapon recognition: {len(known)}/{len(results)} sound-start captures matched at >=0.65')
    print('Confirmed/high confidence:',sum(r['confidence']=='high' for r in known))
    print('Names:',', '.join(f'{name}={n}' for name,n in Counter(x['sound'] for x in known).most_common(12)) or 'none')
    print('Unknown entries are not proof that a weapon failed to play.')
    print('Limiter context is for the entire mix, not a per-weapon post-limiter volume reading.')
    if out:print('CSV:',out)
    return results


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('capture',type=Path,help='A3D v0.6.11 a3d-v0611-weapon-*.bin sidecar')
    ap.add_argument('--archive',type=Path,required=True,help='Your private 100-WAV weapons ZIP')
    ap.add_argument('--log',type=Path,help='Matching A3D diagnostic text log')
    ap.add_argument('--out',type=Path,help='CSV destination (default: next to capture)')
    a=ap.parse_args()
    try:
        analyse(a.capture,a.archive,a.log,a.out or a.capture.with_suffix('.csv'))
    except (ValueError,OSError,zipfile.BadZipFile,ImportError) as e:
        ap.exit(2,'ERROR: '+str(e)+'\n')

if __name__=='__main__':main()
