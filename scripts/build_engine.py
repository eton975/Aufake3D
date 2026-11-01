#!/usr/bin/env python3
"""Build public source Win32 x86 components with the pinned Clang/LLD recipe.
No proprietary SDK, vendor DLL, Wine or game needed. Does not install software.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import shutil

REPO = Path(__file__).resolve().parents[1]
ENGINE = REPO / 'Source' / 'Engine'

def pe32(data):
    if len(data)<64 or data[:2]!=b'MZ': return False
    off=int.from_bytes(data[0x3c:0x40],'little')
    return off+6<len(data) and data[off:off+4]==b'PE\0\0' and int.from_bytes(data[off+4:off+6],'little')==0x14c

def main():
    pa=argparse.ArgumentParser(description=__doc__)
    pa.add_argument('--clang',default='clang')
    pa.add_argument('--linker',default='lld-link')
    a=pa.parse_args()
    cmd=[sys.executable,str(ENGINE/'build_from_recipe.py'),'--clang',a.clang,'--linker',a.linker]
    subprocess.run(cmd,check=True)
    dist=REPO/'dist'/'core'; dist.mkdir(parents=True,exist_ok=True)
    result={}
    for filename in ('a3d.dll','a3dapi.dll'):
        src=ENGINE/'win32'/'build'/filename
        b=src.read_bytes()
        if not pe32(b): raise RuntimeError(f'Invalid PE32/x86: {src}')
        dest=dist/filename;shutil.copyfile(src,dest)
        result[filename]={'sha256':hashlib.sha256(b).hexdigest(),'size':len(b),'machine':'PE32 x86'}
    (dist/'local-build-manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Generated:',dist)
    print('These are UNVERIFIED LOCAL BUILDS, not verified by running on your Windows or Wine system. See Docs/REPRODUCIBILITY.md.')
if __name__=='__main__':main()
