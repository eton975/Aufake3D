#!/usr/bin/env python3
"""Verify tracked, source-only v0.8.16 package bytes before building."""
import hashlib,json,sys
from pathlib import Path
r=Path(__file__).resolve().parents[1]
m=json.loads((r/'SOURCE_MANIFEST_SHA256.json').read_text())['files']
ignored={'build','dist','__pycache__','.git'}
# The historical manifest freezes reviewed *source*, not build artifacts.
# Compilation creates .obj/.lib/.exe files directly inside legacy folders;
# do not report those as unexpected edits to the original source tree.
generated={'.exe','.dll','.lib','.obj','.o','.exp','.pdb','.bsp','.pyc','.zip'}
bad=[]
for rel,digest in m.items():
 p=r/rel
 if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=digest:
  bad.append('missing/changed '+rel)
actual={p.relative_to(r).as_posix() for p in r.rglob('*') if p.is_file()
        and not ignored.intersection(p.relative_to(r).parts)
        and p.suffix.lower() not in generated
        and p.name not in ('SOURCE_MANIFEST_SHA256.json','SHA256SUMS.txt')}
for rel in sorted(actual-set(m)):bad.append('unexpected '+rel)
if bad:sys.exit('\n'.join(bad))
print('PASS:',len(m),'source manifest hashes verified')
