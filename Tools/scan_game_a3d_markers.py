#!/usr/bin/env python3
"""Read-only static game binary inventory: names/strings do not prove A3D calls."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

EXTENSIONS={'.exe','.dll','.m3d','.asi'}
MARKERS=(b'A3DAPI.DLL',b'A3D.DLL',b'MSSA3D2.M3D',b'MSSA3D.M3D',
         b'A3D',b'DSOUND.DLL',b'EAX',b'OPENAL32.DLL')
MAX_BYTES=128*1024*1024

def inventory(path:Path)->dict:
    if not path.exists(): raise FileNotFoundError(path)
    paths=[path] if path.is_file() else sorted(
        (f for f in path.rglob('*') if f.is_file() and f.suffix.lower() in EXTENSIONS),
        key=lambda f:str(f).lower())
    scanned=[]
    for p in paths:
        info={'path':str(p),'size':p.stat().st_size,'sha256':None,'markers':[]}
        if info['size']>MAX_BYTES:
            info['skipped']='exceeds 128MiB limit'
        else:
            data=p.read_bytes(); info['sha256']=hashlib.sha256(data).hexdigest()
            upper=data.upper()
            info['markers']=[s.decode('ascii') for s in MARKERS
                if s in upper or b''.join(bytes((c,0)) for c in s) in upper]
        scanned.append(info)
    return {'path':str(path),'count':len(scanned),
            'interpretation':'Static markers only. This does NOT establish an invoked A3D API, spatial audio, or compatibility.',
            'files':scanned}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('path',type=Path,help='Game file or folder (never modified)')
    ap.add_argument('--out',type=Path,help='Optional destination for JSON report')
    args=ap.parse_args(); report=json.dumps(inventory(args.path),indent=2)+'\n'
    if args.out: args.out.write_text(report,encoding='utf-8')
    else: print(report,end='')

if __name__=='__main__':main()
