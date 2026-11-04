#!/usr/bin/env python3
"""Read-only PE import/marker inspection for an owner-provided Descent 3 EXE.

This is evidence collection, not proof of executed A3D calls, compatibility,
malware safety, or an instruction to patch the retail executable.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'Source/Engine/tools'))
from security_audit_v072 import PEError,import_table  # noqa: E402

TOKENS=("a3d.dll","a3dapi.dll","a3d2","aureal","sound_mixer_aureal",
        "mssa3d2.m3d","directsound","dsound.dll","a3d_init", "co_createinstance")
LIMIT=128*1024*1024

def inspect(path:Path)->dict:
    if not path.is_file():raise ValueError('expected an existing EXE file')
    size=path.stat().st_size
    if size>LIMIT:raise ValueError('input exceeds 128 MiB inspection limit')
    data=path.read_bytes()
    arch,imports=import_table(data)
    # Preserve name matching in single-byte and UTF-16LE; these are only clues.
    lo=data.lower()
    markers=[t for t in TOKENS if t.encode() in lo or t.encode('utf-16le') in lo]
    a3d_imports=[s for s in imports if s.partition('!')[0].lower() in ('a3d.dll','a3dapi.dll')]
    relevant=[s for s in imports if s.partition('!')[2].lower() in
              ('cocreateinstance','cogetclassobject','loadlibrarya','loadlibraryw',
               'getprocaddress','directsoundcreate','directsoundcreate8')]
    return {
        'filename':path.name,'sha256':hashlib.sha256(data).hexdigest(),
        'size':size,'architecture':arch,'aureal_static_imports':a3d_imports,
        'possible_activation_imports':relevant,'static_text_markers':markers,
        'a3d_path_confirmed':False,'gameplay_verified':False,
        'interpretation':('Imports and strings are leads only. A game may resolve A3D '
          'dynamically, use a utility wrapper, or never execute a referenced branch. '
          'Only a runtime trace of original-game A3D calls confirms activation.'),
    }

def main()->int:
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('exe',type=Path)
    a.add_argument('--output',type=Path,help='write JSON locally (does not modify EXE)')
    ns=a.parse_args()
    try:result=inspect(ns.exe)
    except (OSError,ValueError,PEError) as e:
        a.exit(2,f'ERROR: {e}\n')
    out=json.dumps(result,indent=2,sort_keys=True)+'\n'
    if ns.output:ns.output.write_text(out,encoding='utf-8')
    else:print(out,end='')
    return 0
if __name__=='__main__':raise SystemExit(main())
