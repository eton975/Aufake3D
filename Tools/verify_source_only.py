#!/usr/bin/env python3
"""Fail if prebuilt PE/ELF payloads or compiled tools are tracked in source tree."""
from pathlib import Path
import subprocess,sys
root=Path(__file__).resolve().parents[1]
try:
    files=subprocess.check_output(['git','ls-files','-z'],cwd=root,stderr=subprocess.DEVNULL).split(b'\0')
    rels=[p.decode() for p in files if p]
except (OSError,subprocess.CalledProcessError):
    rels=[str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and not any(q in ('build','dist','__pycache__','.git') for q in p.relative_to(root).parts)]
bad=[]
for rel in rels:
    p=root/rel
    if not p.is_file():continue
    b=p.read_bytes()[:4]
    if p.suffix.lower() in ('.exe','.dll','.lib','.obj','.pdb','.exp','.pyc','.so') or b[:2]==b'MZ' or b==b'\x7fELF':bad.append(rel)
if bad:sys.exit('Unexpected compiled files in source: '+repr(bad))
print('PASS: no compiled PE/ELF/helper payloads among',len(rels),'tracked/source files')
