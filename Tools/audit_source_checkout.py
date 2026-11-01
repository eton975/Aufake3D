#!/usr/bin/env python3
"""Check a v0.8.16 source checkout before committing or publishing.

Source-only integrity compares tracked-code files against the snapshot; an
uncommitted developer edit is expected to change hashes, so the tool reports
but does not silently rewrite the frozen manifest. It never pushes to GitHub.
"""
from __future__ import annotations
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
EXCLUDE={'.git','build','dist','__pycache__'}
GENERATED={'.exe','.dll','.lib','.obj','.o','.exp','.pdb','.bsp','.pyc','.zip'}

def main()->int:
    manifest=json.loads((ROOT/'SOURCE_MANIFEST_SHA256.json').read_text(encoding='utf-8'))
    release=manifest['release']
    errors=[]
    if release!='0.8.16':errors.append('Manifest release is not v0.8.16')
    if not (ROOT/'BUILD_WINDOWS.cmd').is_file() or not (ROOT/'BUILD_LINUX.sh').is_file():
        errors.append('One-click build launchers missing')
    actual={}
    paths={}
    for file in ROOT.rglob('*'):
        if not file.is_file():continue
        rel=file.relative_to(ROOT)
        if EXCLUDE.intersection(rel.parts) or rel.suffix.lower() in GENERATED or rel.name in ('SOURCE_MANIFEST_SHA256.json','SHA256SUMS.txt'):
            continue
        name=rel.as_posix()
        if name.casefold() in paths:errors.append('Windows filename collision: '+paths[name.casefold()]+' / '+name)
        paths[name.casefold()]=name
        actual[name]=hashlib.sha256(file.read_bytes()).hexdigest()
    known=manifest['files']
    missing=sorted(set(known)-set(actual))
    extra=sorted(set(actual)-set(known))
    changed=sorted(p for p in set(actual)&set(known) if actual[p]!=known[p])
    print('Snapshot:',release,'| hashed source files:',len(actual))
    print('Missing from checkout:',len(missing),'| Extra source files:',len(extra),'| Modified since snapshot:',len(changed))
    for heading,seq in [('MISSING',missing),('EXTRA',extra),('MODIFIED',changed)]:
        for entry in seq[:30]:print(' ',heading,entry)
        if len(seq)>30:print(' ',heading,'... and',len(seq)-30,'more')
    if missing or extra or changed:errors.append('Checkout does not match this supplied v0.8.16 source snapshot')
    cp=subprocess.run(['git','status','--short'],cwd=ROOT,capture_output=True,text=True)
    if cp.returncode==0:
        print('Git status:')
        print(cp.stdout.strip() or '  clean')
        if cp.stdout.strip():print('Review all Git changes and stage deliberately before commit.')
    else:
        print('No usable Git checkout detected: audit is still valid for the extracted source ZIP.')
    if errors:
        for e in errors:print('ERROR:',e,file=sys.stderr)
        return 1
    print('PASS: source checkout matches this published v0.8.16 snapshot.')
    return 0
if __name__=='__main__':raise SystemExit(main())
