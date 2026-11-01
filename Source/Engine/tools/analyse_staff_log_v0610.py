#!/usr/bin/env python3
"""Offline interpretation of v0.6.10 capped diagnostic log; no identical combat reproduction needed."""
from pathlib import Path
from collections import Counter,defaultdict
import argparse,re
p=argparse.ArgumentParser(description='Aureal A3D v0.6.10 staff/source diagnostic report')
p.add_argument('log',type=Path)
a=p.parse_args()
if not a.log.exists():p.error('Log does not exist: '+str(a.log))
txt=a.log.read_text(errors='replace')
pattern=re.compile(r'^A3D\.Staff\.E ((?:[a-fA-F0-9]{8} ?){9})$',re.M)
records=[]
for m in pattern.finditer(txt):
    vals=m.group(1).split()
    if len(vals)==9:
        ms,kind,sid,sig,gain,prio,active,lim,extra=map(lambda v:int(v,16),vals)
        records.append(dict(ms=ms,kind=kind,id=sid,sig=sig,gain=gain,prio=prio,active=active,lim=lim,extra=extra))
names={1:'play',2:'play-preserved',3:'stop',4:'gain-change',5:'priority-change',6:'rejected',7:'meter',8:'GOOD-mark',9:'BAD-mark',10:'active-at-mark',11:'restart',12:'new',13:'release',14:'unlock',15:'idle-stop',16:'failed-play'}
print('A3D v0.6.10 Staff Sound Diagnostic Analysis')
print('File:',a.log,'size:',a.log.stat().st_size,'bytes')
if not records:
    print('No staff events; run RUN_A3D_STAFF_DIAGNOSTIC_... and exit the game normally.')
    raise SystemExit(1)
print('Retained events:',len(records),'(rolling maximum 4096)')
count=Counter(q['kind'] for q in records)
print('Events: '+', '.join(f'{names.get(k,k)}={v}' for k,v in sorted(count.items())))
played=Counter(q['sig'] for q in records if q['kind']==1 and q['sig'])
print('Most frequently started PCM fingerprints (heuristic, may change with streaming):')
for sig,num in played.most_common(12):print(f'  {sig:08x}: {num} plays')
meters=[x for x in records if x['kind']==7]
if meters:
    lo=min(x['lim'] for x in meters)
    hi=max(x['active'] for x in meters)
    print('Minimum sampled limiter gain:',round(lo/1000,3))
    print('Maximum sampled simultaneous active voices:',hi)
    print('Sampled windows with limiter gain < 0.75:',sum(x['lim']<750 for x in meters),'of',len(meters))
    print('Sampled windows with 6+ voices:',sum(x['active']>=6 for x in meters),'of',len(meters))
marks=[(n,x) for n,x in enumerate(records) if x['kind'] in (8,9)]
if marks:
    print('GOOD/BAD marks (events within +/- 5 seconds):')
    for idx,m in marks:
        nearby=[x for x in records if abs(((x['ms']-m['ms']+2**31)%2**32)-2**31)<=5000]
        kinds=Counter(x['kind'] for x in nearby)
        localmeters=[x for x in nearby if x['kind']==7]
        print(' ',names[m['kind']],f'tick={m["ms"]}ms',
              'plays=',kinds[1], 'stops=',kinds[3], 'rejected=',kinds[6],
              'min-limiter=',str(round(min((x['lim'] for x in localmeters),default=1000)/1000,3)),
              'max-voices=',max((x['active'] for x in localmeters),default=0))
        active=[x for x in nearby if x['kind']==10]
        if active:print('   Active sources at mark:',', '.join(f'ID={x["id"]}, PCM={x["sig"]:08x}, gain={x["gain"]/1000:.2f}, priority={x["prio"]/1000:.2f}' for x in active[:24]))
else:
    print('No GOOD/BAD marks, which is fine; basic event/limiter statistics are still useful.')
alerts=[]
if count[6]:alerts.append('Voice allocation rejections occurred; inspect the requested voice limit.')
if any(x['lim']<750 for x in meters):alerts.append('The global limiter reduced mix gain significantly in at least one sampled window; masking/limiting is plausible, not proven.')
if count[11]:alerts.append('Active-source restarts occurred; check whether the quiet sound was cut short.')
if not alerts:alerts.append('No clear smoking gun in retained events; game-side priority, masking or source PCM activity remains possible.')
print('Interpretation:')
for x in alerts:print(' -',x)
print('Limits: fingerprints identify buffer prefixes, not game sound assets; this is diagnostic telemetry, not a causal proof.')
