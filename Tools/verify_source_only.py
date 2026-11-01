#!/usr/bin/env python3
"""Fail if prebuilt PE/ELF payloads or compiled tools are tracked in source tree."""
from pathlib import Path
import json,subprocess,sys
root=Path(__file__).resolve().parents[1]
try:
    files=subprocess.check_output(['git','ls-files','-z'],cwd=root,stderr=subprocess.DEVNULL).split(b'\0')
    rels=[p.decode() for p in files if p]
except (OSError,subprocess.CalledProcessError):
    # A source ZIP isn't a Git checkout. Use its frozen source inventory,
    # not a recursive directory walk that mistakes newly compiled .exe/.lib
    # development outputs for prebuilt *distributed* source files.
    inventory=root/'SOURCE_MANIFEST_SHA256.json'
    if not inventory.is_file():
        sys.exit('Source-only check requires Git or SOURCE_MANIFEST_SHA256.json')
    rels=list(json.loads(inventory.read_text())['files'])
bad=[]
for rel in rels:
    p=root/rel
    if not p.is_file():continue
    b=p.read_bytes()[:4]
    if p.suffix.lower() in ('.exe','.dll','.lib','.obj','.pdb','.exp','.pyc','.so') or b[:2]==b'MZ' or b==b'\x7fELF':bad.append(rel)
if bad:sys.exit('Unexpected compiled files in source: '+repr(bad))
print('PASS: no compiled PE/ELF/helper payloads among',len(rels),'tracked/source files')
